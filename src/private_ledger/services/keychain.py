from __future__ import annotations

import subprocess


class KeychainStore:
    def __init__(self, service_name: str = "local.gd.private-ledger.minimax", account_name: str = "minimax") -> None:
        self.service_name = service_name
        self.account_name = account_name

    def save_secret(self, secret: str) -> None:
        if not secret:
            raise ValueError("Secret cannot be empty.")
        subprocess.run(
            [
                "security",
                "add-generic-password",
                "-a",
                self.account_name,
                "-s",
                self.service_name,
                "-w",
                secret,
                "-U",
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def load_secret(self) -> str:
        result = subprocess.run(
            [
                "security",
                "find-generic-password",
                "-a",
                self.account_name,
                "-s",
                self.service_name,
                "-w",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return ""
        return result.stdout.strip()

    def has_secret(self) -> bool:
        return bool(self.load_secret())
