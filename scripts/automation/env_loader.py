# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2024-2026 Alonso Alvarado Hernández <alonsoalvaradohr>
import os

def load_env(env_path=None):
    if not env_path:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        local_env = os.path.join(base_dir, ".env.local")
        default_env = os.path.join(base_dir, ".env")
        if os.path.exists(local_env):
            env_path = local_env
        elif os.path.exists(default_env):
            env_path = default_env

    if env_path and os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip().strip('"').strip("'")
    return os.environ

