#!/usr/bin/env python3
"""
Seal Alertmanager Email config with kubeseal.

Usage:
  python scripts/seal_alertmanager_email.py --smtp-user <EMAIL> --smtp-password <APP_PASSWORD> --from <EMAIL> --to <EMAIL>
  python scripts/seal_alertmanager_email.py --smtp-user <EMAIL> --smtp-password <APP_PASSWORD> --from <EMAIL> --to <EMAIL> --output <PATH>

Reads master cert from k3s/sealed-secrets/master-key.yaml
Outputs sealed secret to k3s/sealed-secrets/alertmanager-email-sealed-secret.yaml (default)
"""

import argparse
import base64
import subprocess
import sys
import yaml
from pathlib import Path


REPO_ROOT = Path(__file__).parent.parent
MASTER_KEY_PATH = REPO_ROOT / "k3s" / "sealed-secrets" / "master-key.yaml"
DEFAULT_OUTPUT = REPO_ROOT / "k3s" / "sealed-secrets" / "alertmanager-email-sealed-secret.yaml"

ALERTMANAGER_CONFIG_TEMPLATE = """apiVersion: v1
kind: Secret
metadata:
  name: alertmanager-email-secret
  namespace: monitoring
type: Opaque
stringData:
  alertmanager.yaml: |
    global:
      resolve_timeout: 5m
      smtp_smarthost: 'smtp.gmail.com:587'
      smtp_from: '{smtp_from}'
      smtp_auth_username: '{smtp_user}'
      smtp_auth_password: '{smtp_password}'
      smtp_require_tls: true
    route:
      receiver: email
      group_by: [alertname]
      group_wait: 30s
      group_interval: 5m
      repeat_interval: 4h
    receivers:
      - name: email
        email_configs:
          - to: '{email_to}'
            send_resolved: true
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
    parser = argparse.ArgumentParser(description="Generate/Seal Alertmanager Email config")
    parser.add_argument("--smtp-user", required=True, help="Gmail address (SMTP username)")
    parser.add_argument("--smtp-password", required=True, help="Gmail App Password (16 chars)")
    parser.add_argument("--from", dest="smtp_from", required=True, help="From email address")
    parser.add_argument("--to", dest="email_to", required=True, help="To email address (recipient)")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output sealed secret path")
    parser.add_argument("--plaintext-only", action="store_true", help="Only generate plaintext YAML (skip sealing)")
    args = parser.parse_args()

    plaintext = ALERTMANAGER_CONFIG_TEMPLATE.format(
        smtp_user=args.smtp_user,
        smtp_password=args.smtp_password,
        smtp_from=args.smtp_from,
        email_to=args.email_to,
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

    print("Sealing Alertmanager Email config...")
    sealed = seal_secret(cert_pem, plaintext)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(sealed)
    print(f"Sealed secret written to {args.output}")
    print("Commit this file to git. Do NOT commit the plaintext config.")


if __name__ == "__main__":
    main()