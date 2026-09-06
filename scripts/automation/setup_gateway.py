import paramiko
import os

def setup():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect('AlonsoRTOS', username='alonso', key_filename=os.path.expanduser('~/.ssh/id_ed25519_hil'))

    nginx_conf = """server {
    listen 8088 default_server;
    server_name _;

    client_max_body_size 50M;

    # noVNC Web Interface
    location /vnc/ {
        proxy_pass http://127.0.0.1:6080/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    # noVNC WebSocket traffic
    location /websockify {
        proxy_pass http://127.0.0.1:6080/websockify;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }

    # ttyd Web Terminal
    location /terminal/ {
        proxy_pass http://127.0.0.1:7681/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }

    # MAGI SYSTEM HMI and Sensorial Backend
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }
}
"""

    sftp = c.open_sftp()
    with sftp.open('/tmp/magi-gateway.conf', 'w') as f:
        f.write(nginx_conf)
    sftp.close()

    sudo_pwd = os.environ.get('HIL_SUDO_PASS', '')
    sudo_pfx = f"echo {sudo_pwd} | sudo -S " if sudo_pwd else "sudo "

    cmds = [
        f"{sudo_pfx}cp /tmp/magi-gateway.conf /etc/nginx/sites-available/magi-gateway",
        f"{sudo_pfx}ln -sf /etc/nginx/sites-available/magi-gateway /etc/nginx/sites-enabled/magi-gateway",
        f"{sudo_pfx}nginx -t",
        f"{sudo_pfx}systemctl reload nginx",
        "curl -s -I http://127.0.0.1:8088/",
        "curl -s -I http://127.0.0.1:8088/vnc/vnc.html",
        "curl -s -I http://127.0.0.1:8088/terminal/"
    ]
    for cmd in cmds:
        print(">>>", cmd)
        stdin, stdout, stderr = c.exec_command(cmd)
        out = stdout.read().decode().strip()
        err = stderr.read().decode().strip()
        if out:
            print("[STDOUT]:", out)
        if err:
            print("[STDERR]:", err)

    c.close()

if __name__ == '__main__':
    setup()
