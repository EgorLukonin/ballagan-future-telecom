#!/usr/bin/env python3
"""
Seal Alertmanager Telegram config with kubeseal.

Usage:
  python scripts/seal_alertmanager.py --bot-token <TOKEN> --chat-id <CHAT_ID>
  python scripts/seal_alertmanager.py --bot-token <TOKEN> --chat-id <CHAT_ID> --output <PATH>

Reads master cert from k3s/sealed-secrets/master-key.yaml
Outputs sealed secret to k3s/sealed-secrets/alertmanager-telegram-sealed-secret.yaml (default)
"""

import argparse
import base64
import subprocess
import sys
import tempfile
import yaml
from pathlib import Path


REPO_ROOT = Path(__file__).parent.parent
MASTER_KEY_PATH = REPO_ROOT / "k3s" / "sealed-secrets" / "master-key.yaml"
DEFAULT_OUTPUT = REPO_ROOT / "k3s" / "sealed-secrets" / "alertmanager-telegram-sealed-secret.yaml"

ALERTMANAGER_CONFIG_TEMPLATE = """apiVersion: v1
kind: Secret
metadata:
  name: alertmanager-telegram-secret
  namespace: monitoring
type: Opaque
stringData:
  alertmanager.yaml: |
    global:
      resolve_timeout: 5m
    route:
      receiver: telegram
      group_by: [alertname]
      group_wait: 30s
      group_interval: 5m
      repeat_interval: 4h
    receivers:
      - name: telegram
        telegram_configs:
          - bot_token: "{bot_token}"
            chat_id: {chat_id}
            parse_mode: HTML
    inhibit_rules:
      - source_matchers:
          - alertname =~ "KubeNodeUnreachable|KubeNodeNotReady|KubeletDown"
        target_matchers:
          - alertname =~ "UniversityMaterialsAPI.*"
"""


def load_master_cert(master_key_path: Path) -> str:
    with open(master_key_path) as f:
        data = yaml.safe_load(f)
    cert_b64 = data["items"][0]["data"]["tls.crt"]
    return base64.b64decode(cert_b64).decode()


def seal_secret(cert_pem: str, plaintext_yaml: str) -> str:
    result = subprocess.run(
        ["kubeseal", "--cert", "/dev/stdin", "--format", "yaml"],
        input=cert_pem.encode(),
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"kubeseal failed: {result.stderr.decode()}")

    # kubeseal reads from stdin, so we need to pipe the plaintext
    result = subprocess.run(
        ["kubeseal", "--cert", "/dev/stdin", "--format", "yaml"],
        input=plaintext_yaml.encode(),
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"kubeseal failed: {result.stderr.decode()}")

    return result.stdout.decode()


def main():
    parser = argparse.ArgumentParser(description="Generate/Seal Alertmanager Telegram config")
    parser.add_argument("--bot-token", required=True, help="Telegram bot token")
    parser.add_argument("--chat-id", required=True, help="Telegram chat ID (numeric)")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output sealed secret path")
    parser.add_argument("--plaintext-only", action="store_true", help="Only generate plaintext YAML (skip sealing)")
    args = parser.parse_args()

    plaintext = ALERTMANAGER_CONFIG_TEMPLATE.format(
        bot_token=args.bot_token,
        chat_id=args.chat_id,
    )

    if args.plaintext_only:
        plaintext_path = args.output.with_suffix(".plaintext.yaml")
        plaintext_path.write_text(plaintext)
        print(f"Plaintext config written to {plaintext_path}")
        print("Run kubeseal on a machine with the tool installed:")
        print(f"  kubeseal --cert <cert.pem> --format yaml < {plaintext_path} > {args.output}")
        return

    if not MASTER_KEY_PATH.exists():
        print(f"Error: Master key not found at {MASTER_KEY_PATH}", file=sys.stderr)
        sys.exit(1)

    cert_pem = load_master_cert(MASTER_KEY_PATH)

    print("Sealing Alertmanager config...")
    sealed = seal_secret(cert_pem, plaintext)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(sealed)
    print(f"Sealed secret written to {args.output}")
    print("Commit this file to git. Do NOT commit the plaintext config.")


if __name__ == "__main__":
    main()