# pylint: disable=import-error, line-too-long

import os
import sys
import json
from pathlib import Path
import tkinter as tk
from tkinter import filedialog

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/gmail.modify",
]

REPO_ROOT = Path.cwd()
GITIGNORE_PATH = REPO_ROOT / ".gitignore"
ENV_PATH = REPO_ROOT / ".env"


def ensure_gitignore_contains_env():
    """Step 1: Verify .gitignore exists and contains .env"""
    if not GITIGNORE_PATH.exists():
        print("Error: .gitignore file does not exist in the current directory.")
        sys.exit(1)

    content = GITIGNORE_PATH.read_text().splitlines()

    if ".env" not in [line.strip() for line in content]:
        print("Error: .gitignore does not contain '.env'. Add it before running this script.")
        sys.exit(1)


def ensure_env_file():
    """Step 2: Create .env if it doesn't exist"""
    if not ENV_PATH.exists():
        ENV_PATH.touch()


def choose_secrets_file():
    """Open file chooser for secrets JSON"""
    root = tk.Tk()
    root.withdraw()

    file_path = filedialog.askopenfilename(
        title="Select Google OAuth Client Secrets JSON file",
        filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
    )

    if not file_path:
        print("No secrets file selected. Exiting.")
        sys.exit(1)

    return file_path


def parse_secrets(file_path):
    """Step 3: Extract client_id and client_secret"""
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "installed" in data:
        creds = data["installed"]
    elif "web" in data:
        creds = data["web"]
    else:
        raise RuntimeError("Invalid Google client secrets file format.")

    return creds["client_id"], creds["client_secret"]


def update_env(values):
    """Write or update variables in .env"""
    existing = {}

    if ENV_PATH.exists():
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    existing[k] = v

    existing.update(values)

    with open(ENV_PATH, "w", encoding="utf-8") as f:
        for k, v in existing.items():
            f.write(f"{k}={v}\n")


def main():
    ensure_gitignore_contains_env()
    ensure_env_file()

    secrets_file = choose_secrets_file()

    client_id, client_secret = parse_secrets(secrets_file)

    flow = InstalledAppFlow.from_client_secrets_file(
        secrets_file,
        SCOPES
    )

    creds = flow.run_local_server(
        port=0,
        access_type="offline",
        prompt="consent"
    )

    update_env({
        "GOOGLE_OAUTH_CLIENT_ID": client_id,
        "GOOGLE_OAUTH_CLIENT_SECRET": client_secret,
        "GOOGLE_OAUTH_REFRESH_TOKEN": creds.refresh_token
    })

    print(".env updated successfully.")


if __name__ == "__main__":
    main()