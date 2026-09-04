#!/usr/bin/env python3
"""Atomic MAGI deployer. Dry-run by default; never installs dependencies."""

import argparse
import hashlib
import os
from pathlib import Path, PurePosixPath
import shlex
import sys
import time

import paramiko


REPO_ROOT = Path(__file__).resolve().parents[2]
APP_SOURCE = REPO_ROOT / "src" / "hmi_ui"
COMPONENTS = {
    "autostart": [(REPO_ROOT / "config" / "labwc" / "autostart", PurePosixPath("autostart"))],
    "systemd": [(REPO_ROOT / "config" / "systemd" / "magi-kiosk.service", PurePosixPath("magi-kiosk.service"))],
    "verifier": [(REPO_ROOT / "scripts" / "verify-input-stack.sh", PurePosixPath("verify-input-stack.sh"))],
}


class DeployError(RuntimeError):
    pass


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def app_files():
    result = []
    for path in sorted(APP_SOURCE.rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
            result.append((path, PurePosixPath(path.relative_to(APP_SOURCE).as_posix())))
    return result


def component_files(component):
    return app_files() if component == "app" else COMPONENTS[component]


class Remote:
    def __init__(self, client, sudo_password=None):
        self.client = client
        self.sudo_password = sudo_password

    def run(self, command, *, sudo=False, timeout=90):
        if sudo:
            if self.sudo_password:
                remote_command = f"sudo -S -p '' -- sh -c {shlex.quote(command)}"
            else:
                remote_command = f"sudo -n -- sh -c {shlex.quote(command)}"
        else:
            remote_command = command
        print(f"REMOTE_COMMAND: {remote_command}")
        stdin, stdout, stderr = self.client.exec_command(remote_command, timeout=timeout)
        if sudo and self.sudo_password:
            stdin.write(self.sudo_password + "\n")
            stdin.flush()
        out = stdout.read().decode("utf-8", errors="replace")
        err = stderr.read().decode("utf-8", errors="replace")
        rc = stdout.channel.recv_exit_status()
        print("REMOTE_STDOUT_BEGIN")
        print(out, end="" if out.endswith("\n") or not out else "\n")
        print("REMOTE_STDOUT_END")
        print("REMOTE_STDERR_BEGIN")
        print(err, end="" if err.endswith("\n") or not err else "\n")
        print("REMOTE_STDERR_END")
        print(f"REMOTE_RC: {rc}")
        if rc != 0:
            raise DeployError(f"Remote command failed with rc={rc}: {remote_command}")
        return out


def connect(args):
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    if args.known_hosts:
        client.load_host_keys(str(args.known_hosts))
    client.set_missing_host_key_policy(paramiko.RejectPolicy())
    password = os.environ.get(args.password_env) if args.password_env else None
    kwargs = {
        "hostname": args.host,
        "port": args.port,
        "username": args.user,
        "timeout": args.connect_timeout,
        "allow_agent": args.key_file is None and password is None,
        "look_for_keys": args.key_file is None and password is None,
    }
    if args.key_file:
        kwargs["key_filename"] = str(args.key_file)
    if password:
        kwargs["password"] = password
    client.connect(**kwargs)
    return client, password


def remote_target(component, relative):
    if component == "app":
        return PurePosixPath("[HOME_REDACTED]") / relative
    if component == "autostart":
        return PurePosixPath("[HOME_REDACTED]")
    if component == "systemd":
        return PurePosixPath("/etc/systemd/system/magi-kiosk.service")
    return PurePosixPath("[HOME_REDACTED]")


def print_plan(args, files):
    print(f"MODE: {'APPLY' if args.apply else 'DRY-RUN'}")
    print(f"TARGET: {args.user}@{args.host}:{args.port}")
    print(f"COMPONENT: {args.component}")
    for local, relative in files:
        print(f"LOCAL_SHA256: {sha256_file(local)}  {local}")
        print(f"REMOTE_TARGET: {remote_target(args.component, relative)}")


def upload_and_verify(remote, client, stage_root, files):
    remote.run(f"mkdir -p {shlex.quote(str(stage_root))}")
    sftp = client.open_sftp()
    try:
        for local, relative in files:
            staged = stage_root / relative
            remote.run(f"mkdir -p {shlex.quote(str(staged.parent))}")
            sftp.put(str(local), str(staged))
            print(f"SFTP_UPLOAD: {local} -> {staged}")
            local_hash = sha256_file(local)
            remote_hash = remote.run(f"sha256sum {shlex.quote(str(staged))}").split()[0]
            print(f"HASH_COMPARE: local={local_hash} remote={remote_hash} path={staged}")
            if remote_hash != local_hash:
                raise DeployError(f"SHA256 mismatch for staged file {staged}")
    finally:
        sftp.close()


def backup_if_present(remote, target, backup, *, sudo=False):
    command = f"if [ -e {shlex.quote(str(target))} ]; then mkdir -p {shlex.quote(str(backup.parent))}; cp -a {shlex.quote(str(target))} {shlex.quote(str(backup))}; fi"
    remote.run(command, sudo=sudo)


def install_component(remote, component, stage_root, files, timestamp):
    if component == "app":
        app_target = PurePosixPath("[HOME_REDACTED]")
        backup = PurePosixPath("[HOME_REDACTED]") / timestamp / "05_hmi_display"
        backup_if_present(remote, app_target, backup)
        for _, relative in files:
            source, target = stage_root / relative, app_target / relative
            remote.run(f"install -D -m 0644 {shlex.quote(str(source))} {shlex.quote(str(target))}")
            remote.run(f"sha256sum {shlex.quote(str(target))}")
        remote.run("systemctl restart magi-ui.service", sudo=True)
        remote.run("systemctl status magi-ui.service --no-pager -l", sudo=True)
        remote.run("curl --fail --show-error --silent http://127.0.0.1:8080/api/status")
        return

    local, relative = files[0]
    source = stage_root / relative
    target = remote_target(component, relative)
    backup = PurePosixPath("[HOME_REDACTED]") / timestamp / component / target.name
    sudo = component == "systemd"
    backup_if_present(remote, target, backup, sudo=sudo)
    mode = "0755" if component in {"autostart", "verifier"} else "0644"
    remote.run(f"install -D -m {mode} {shlex.quote(str(source))} {shlex.quote(str(target))}", sudo=sudo)
    remote.run(f"sha256sum {shlex.quote(str(target))}", sudo=sudo)
    if component == "systemd":
        remote.run("systemctl daemon-reload", sudo=True)
        remote.run("systemctl restart magi-kiosk.service", sudo=True)
        remote.run("systemctl status magi-kiosk.service --no-pager -l", sudo=True)
        remote.run("[HOME_REDACTED] --preflight")
    elif component == "autostart":
        print("AUTOSTART_STAGED: no service restart performed; deploy component=systemd later")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Atomic MAGI deployer (dry-run unless --apply)")
    parser.add_argument("--component", required=True, choices=("app", "autostart", "systemd", "verifier"))
    parser.add_argument("--apply", action="store_true", help="Perform the remote mutation")
    parser.add_argument("--host", default="192.168.4.2")
    parser.add_argument("--port", default=22, type=int)
    parser.add_argument("--user", default="alonso")
    parser.add_argument("--key-file", type=Path)
    parser.add_argument("--password-env", default="HIL_SSH_PASSWORD", help="Environment variable containing SSH/sudo password")
    parser.add_argument("--known-hosts", type=Path)
    parser.add_argument("--connect-timeout", default=10.0, type=float)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    files = component_files(args.component)
    missing = [str(path) for path, _ in files if not path.is_file()]
    if missing:
        raise DeployError("Missing canonical sources: " + ", ".join(missing))
    print_plan(args, files)
    if not args.apply:
        print("DRY_RUN_COMPLETE: no SSH connection and no remote mutation")
        return 0

    timestamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    stage_root = PurePosixPath("[HOME_REDACTED]") / timestamp / args.component
    client, password = connect(args)
    try:
        remote = Remote(client, password)
        upload_and_verify(remote, client, stage_root, files)
        install_component(remote, args.component, stage_root, files, timestamp)
    finally:
        client.close()
    print(f"APPLY_COMPLETE: component={args.component}; review literal command evidence above")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (DeployError, OSError, paramiko.SSHException) as exc:
        print(f"DEPLOY_FAILED: {exc}", file=sys.stderr)
        sys.exit(1)
