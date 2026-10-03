"""tools/aws — the burst is credential-free, resumes from S3, and records nothing on the box (M12.3)."""

from __future__ import annotations

import subprocess
from pathlib import Path

AWS = Path(__file__).resolve().parent.parent / "tools" / "aws"


def test_the_runbook_and_the_boot_script_parse_carry_no_credential_and_resume_rather_than_restart():
    run, boot = (AWS / "burst.sh").read_text(), (AWS / "user-data.sh").read_text()
    for f in ("burst.sh", "user-data.sh"):
        assert subprocess.run(["bash", "-n", str(AWS / f)], capture_output=True).returncode == 0, f
    for forbidden in ("TIINGO", "AKIA", "aws_secret", "occams.toml", "ssh ", "scp ", "@"):
        assert forbidden not in run and forbidden not in boot, forbidden
    # the box: resume from the checkpoint before running, mirror every five minutes, never record, scale itself to zero
    assert 'aws s3 sync "$CK/" "$OUT/"' in boot and 'aws s3 sync "$OUT/" "$CK/"' in boot and "--no-record" in boot
    assert "sleep 300" in boot and "set-desired-capacity" in boot and "--desired-capacity 0" in boot
    assert "set -Eeuo pipefail" in boot and "trap 'on_error $LINENO' ERR" in boot and "awscli-exe-linux-x86_64.zip" in boot
    assert boot.index('mkdir -p "$OUT/cells"') < boot.index("chown -R ubuntu:ubuntu") < boot.index("sudo -u ubuntu nohup")
    assert "return 0\n}" in boot and 'ls "$OUT/cells"' not in boot and 'BASH_SUBSHELL' in boot and 'mkdir -p "$OUT/cells"' in boot
    assert "| wc -l)\n" not in boot.split("progress()")[1].split("}")[0].replace("| wc -l)\n  [", "")
    assert "install -y -qq git make unzip jq python3.12-venv" in boot and "apt-get install -y -qq git python3.12-venv awscli" not in boot
    assert "NO REPORT" in run and "console)" in run
    assert "X-aws-ec2-metadata-token" in boot and "--with-decryption" in boot and 'chmod 600 "configs/$CONFIG"' in boot
    # this machine: private encrypted bucket, a SecureString for the config, a scoped role, spot only, resume-on-failure
    assert "BlockPublicAcls=true" in run and '"SSEAlgorithm":"AES256"' in run and "--type SecureString" in run
    assert '"Encrypted":true' in run and '"HttpTokens":"required"' in run and 'OnDemandPercentageAboveBaseCapacity\\":0' in run
    assert "--capacity-rebalance" in run and "--min-size 0 --max-size 1" in run and "git bundle create" in run
    assert "survey record" in run and "Resource\":\"*\"" in run.split('"autoscaling:DescribeAutoScalingGroups"')[1][:40]
    assert run.count("Resource\":\"*\"") == 1     # the only unscoped permission is the read-only describe
