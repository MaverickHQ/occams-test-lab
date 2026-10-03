#!/bin/bash
# tools/aws/user-data.sh — what a burst instance does at boot (M12.3). Templated by
# tools/aws/burst.sh setup: the __PLACEHOLDERS__ are the bucket, the config parameter,
# the auto scaling group and the region. The job (grid, seed, workers) is read from
# S3, so one launch template serves every survey. Resume: the checkpoint prefix is
# synced down before the run, so finished cells are skipped; every five minutes the
# survey directory is synced up with a progress record; on completion the box writes
# the done marker and scales its own group to zero, which terminates it.
set -Eeuo pipefail   # -E: the ERR trap fires inside functions too
BUCKET="__BUCKET__"; PARAM="__PARAM__"; ASG="__ASG__"; REGION="__REGION__"
export AWS_DEFAULT_REGION="$REGION" DEBIAN_FRONTEND=noninteractive
exec > >(tee -a /var/log/occams-burst.log) 2>&1
echo "boot $(date -u +%FT%TZ)"
scale_to_zero() { aws autoscaling set-desired-capacity --auto-scaling-group-name "$ASG" --desired-capacity 0 --region "$REGION" 2>/dev/null || shutdown -h +1; }
on_error() {   # fail fast and stop the spend: a broken boot never idles; a deterministic failure never loops
  [ "${BASH_SUBSHELL:-0}" -eq 0 ] || return 0   # only a top-level failure stops the box, never one inside a $(...)
  echo "FAILED at line $1 $(date -u +%FT%TZ)"
  if command -v aws >/dev/null && [ -n "${CK:-}" ]; then progress failed 2>/dev/null || true; fi
  scale_to_zero
}
trap 'on_error $LINENO' ERR
# Ubuntu 24.04 carries no awscli package: the official installer, and the rest from apt
apt-get -o DPkg::Lock::Timeout=300 update -qq && apt-get -o DPkg::Lock::Timeout=300 install -y -qq git make unzip jq python3.12-venv >/dev/null
curl -sS https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip -o /tmp/awscliv2.zip && unzip -q /tmp/awscliv2.zip -d /tmp && /tmp/aws/install >/dev/null
aws --version
TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 300")
IID=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/instance-id)
ITYPE=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/instance-type)
aws s3 cp "s3://$BUCKET/jobs/current.json" /home/ubuntu/job.json --quiet
GRID=$(jq -r .grid /home/ubuntu/job.json); GRID_NAME=$(jq -r .grid_name /home/ubuntu/job.json)
SEED=$(jq -r .seed /home/ubuntu/job.json); TOTAL=$(jq -r .cell_count /home/ubuntu/job.json)
CONFIG=$(jq -r .config_name /home/ubuntu/job.json)
REGISTER=$(jq -r '.register // "register/programme-2.jsonl"' /home/ubuntu/job.json)
JOB="$GRID_NAME-seed$SEED"; CK="s3://$BUCKET/checkpoint/$JOB"
progress() {  # $1 = state; every pipeline here may legitimately find nothing yet, so none of them may fail the script
  local n=0 last="" dir="/home/ubuntu/occams-test-lab/archive/surveys/$JOB/cells"
  [ -d "$dir" ] && n=$(find "$dir" -maxdepth 1 -name '*.json' | wc -l)
  [ -f /home/ubuntu/occams-test-lab/survey-run.log ] && last=$(tail -n 1 /home/ubuntu/occams-test-lab/survey-run.log | cut -c1-200 || true)
  jq -n --arg state "$1" --arg iid "$IID" --arg itype "$ITYPE" --argjson done "$n" --argjson total "$TOTAL" \
     --arg at "$(date -u +%FT%TZ)" --arg last "$last" \
     '{state:$state,instance:$iid,type:$itype,cells_done:$done,cells_total:$total,heartbeat:$at,last_line:$last}' > /tmp/progress.json
  aws s3 cp /tmp/progress.json "$CK/progress.json" --quiet
  aws s3 cp /var/log/occams-burst.log "$CK/logs/boot-$IID.log" --quiet
  if [ -f /home/ubuntu/occams-test-lab/survey-run.log ]; then aws s3 cp /home/ubuntu/occams-test-lab/survey-run.log "$CK/logs/survey-run-$IID.log" --quiet; fi
  return 0
}
cd /home/ubuntu
progress installing
aws s3 cp "s3://$BUCKET/input/repo.bundle" . --quiet && aws s3 cp "s3://$BUCKET/input/archive.tgz" . --quiet
rm -rf occams-test-lab && git clone -q repo.bundle occams-test-lab && cd occams-test-lab
tar xzf ../archive.tgz && mkdir -p configs
aws ssm get-parameter --name "$PARAM" --with-decryption --query Parameter.Value --output text > "configs/$CONFIG"
chmod 600 "configs/$CONFIG"
python3.12 -m venv .venv && .venv/bin/pip install -q -e ".[dev]"
progress checking
echo "platform $(.venv/bin/python -c 'import sys,platform,numpy;print(sys.version.split()[0],platform.machine(),"numpy",numpy.__version__)') · $(nproc) vcpus · $ITYPE"
set +e; PATH="$PWD/.venv/bin:$PATH" make check > ../checks.log 2>&1; RC=$?; set -e   # outside the tree: never dirty
grep -E "passed|failed|error|All checks|credscan:|provenance:" ../checks.log | head -6 || true; echo "make check exit $RC"
aws s3 cp ../checks.log "$CK/logs/checks-$IID.log" --quiet
[ "$RC" -eq 0 ] || { echo "the checks failed on the box: not running"; false; }
OUT="archive/surveys/$JOB"; mkdir -p "$OUT/cells" "$OUT/baselines"
aws s3 sync "$CK/" "$OUT/" --quiet --exclude "progress.json" --exclude "done.json" --exclude "logs/*"
N0=$(find "$OUT/cells" -maxdepth 1 -name '*.json' | wc -l); echo "resumed from checkpoint: $N0 cells already there"
chown -R ubuntu:ubuntu /home/ubuntu   # after the directories exist and the checkpoint is down: the survey runs as ubuntu
progress running
sudo -u ubuntu nohup .venv/bin/python -m occams survey run "$GRID" --archive archive --register "$REGISTER" \
  --config "configs/$CONFIG" --seed "$SEED" --workers "$(nproc)" --no-record --out "$OUT" > survey-run.log 2>&1 &
PID=$!
while kill -0 "$PID" 2>/dev/null; do
  sleep 300
  aws s3 sync "$OUT/" "$CK/" --quiet --exclude "*.tmp" || true
  progress running || true
done
set +e; wait "$PID"; RC=$?; set -e
aws s3 sync "$OUT/" "$CK/" --quiet --exclude "*.tmp"
if [ "$RC" -eq 0 ] && [ -f "$OUT/survey.json" ]; then
  progress done
  jq -n --arg at "$(date -u +%FT%TZ)" --arg iid "$IID" '{finished:$at,instance:$iid}' > /tmp/done.json
  aws s3 cp /tmp/done.json "$CK/done.json" --quiet
  echo "done $(date -u +%FT%TZ); scaling to zero"
else
  progress failed
  echo "survey exit $RC without an index: the checkpoint is in S3; scaling to zero — a resume is a new start, an interruption is replaced by the group"
fi
scale_to_zero
