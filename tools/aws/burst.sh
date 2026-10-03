#!/usr/bin/env bash
# tools/aws/burst.sh — a reusable burst of compute for a survey run (M12.3).
#
# Resume, never restart: every finished cell is an atomic file; the box mirrors its
# survey directory to S3 every five minutes; an auto scaling group of size one
# replaces an interrupted or failed instance, and the replacement resumes from the
# checkpoint. Nothing here needs SSH: the box reports progress and logs through S3.
# What reaches the box: a git bundle of committed HEAD, the archive's manifest and
# the bars the grid's universes need (M14.7), and the programme's config from SSM
# Parameter Store (SecureString).
# What never leaves this machine: the Tiingo key, AWS access keys, any GitHub
# credential. The box runs with --no-record; `survey record` runs here.
#
#   tools/aws/burst.sh setup                      # bucket, config parameter, instance role, launch template, group (idempotent)
#   tools/aws/burst.sh start GRID SEED            # bundle + upload the input, declare the job, scale the group to one
#   tools/aws/burst.sh status GRID SEED           # the progress record from S3 and the group's instances
#   tools/aws/burst.sh console                    # the group's instance console log, filtered (a boot that never reported)
#   tools/aws/burst.sh watch GRID SEED            # a loop for a monitor: one line per change, exits on done
#   tools/aws/burst.sh pull GRID SEED             # sync the checkpoint here, into archive/surveys/<job>-<type>/
#   tools/aws/burst.sh compare DIR_A DIR_B        # cells in both directories, byte for byte
#   tools/aws/burst.sh record GRID SEED DIR       # verify and append SurveyRecorded here
#   tools/aws/burst.sh stop                       # scale the group to zero (the checkpoint stays)
#   tools/aws/burst.sh teardown [--all]           # group and launch template; --all also the bucket, parameter and role
#
# Environment: REGION (default: the CLI's), INSTANCE_TYPES (default "c7a.32xlarge c6i.32xlarge", 128 vCPUs each),
# CONFIG (default configs/programme-2.toml), REGISTER (default register/programme-2.jsonl), NAME (default occams-burst).
# Programme 3: CONFIG=configs/programme-3.toml REGISTER=register/programme-3.jsonl tools/aws/burst.sh …
set -euo pipefail
cd "$(dirname "$0")/../.."
REGION="${REGION:-$(aws configure get region)}"
INSTANCE_TYPES="${INSTANCE_TYPES:-c7a.32xlarge c6i.32xlarge}"
CONFIG="${CONFIG:-configs/programme-2.toml}"
REGISTER="${REGISTER:-register/programme-2.jsonl}"   # the programme's Register the box reads (committed: the bundle carries it)
NAME="${NAME:-occams-burst}"
export AWS_DEFAULT_REGION="$REGION"
SUFFIX=$(aws sts get-caller-identity --query Account --output text | shasum -a 256 | cut -c1-10)
BUCKET="$NAME-$SUFFIX"
PARAM="/$NAME/$(basename "${CONFIG%.toml}")"
ROLE="$NAME-instance"
B=build/burst; mkdir -p "$B"
PY=.venv/bin/python

job_name() { echo "$($PY -c "import tomllib;print(tomllib.load(open('$1','rb'))['grid']['name'])")-seed$2"; }

case "${1:-}" in
setup)
  if ! aws s3api head-bucket --bucket "$BUCKET" 2>/dev/null; then
    aws s3api create-bucket --bucket "$BUCKET" --create-bucket-configuration "LocationConstraint=$REGION" >/dev/null
    echo "bucket $BUCKET created"
  fi
  aws s3api put-public-access-block --bucket "$BUCKET" --public-access-block-configuration \
    BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true >/dev/null
  aws s3api put-bucket-encryption --bucket "$BUCKET" --server-side-encryption-configuration \
    '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}' >/dev/null
  aws ssm put-parameter --name "$PARAM" --type SecureString --value "file://$CONFIG" --overwrite >/dev/null
  echo "config parameter $PARAM written (SecureString)"
  ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
  KMS=$(aws kms describe-key --key-id alias/aws/ssm --query KeyMetadata.Arn --output text)
  if ! aws iam get-role --role-name "$ROLE" >/dev/null 2>&1; then
    aws iam create-role --role-name "$ROLE" --assume-role-policy-document \
      '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"ec2.amazonaws.com"},"Action":"sts:AssumeRole"}]}' >/dev/null
    aws iam create-instance-profile --instance-profile-name "$ROLE" >/dev/null
    aws iam add-role-to-instance-profile --instance-profile-name "$ROLE" --role-name "$ROLE"
    echo "role and instance profile $ROLE created"
  fi
  aws iam put-role-policy --role-name "$ROLE" --policy-name "$NAME" --policy-document "$(cat <<JSON
{"Version":"2012-10-17","Statement":[
 {"Effect":"Allow","Action":["s3:ListBucket"],"Resource":"arn:aws:s3:::$BUCKET"},
 {"Effect":"Allow","Action":["s3:GetObject","s3:PutObject","s3:DeleteObject"],"Resource":"arn:aws:s3:::$BUCKET/*"},
 {"Effect":"Allow","Action":["ssm:GetParameter"],"Resource":"arn:aws:ssm:$REGION:$ACCOUNT:parameter$PARAM"},
 {"Effect":"Allow","Action":["kms:Decrypt"],"Resource":"$KMS"},
 {"Effect":"Allow","Action":["autoscaling:SetDesiredCapacity"],"Resource":"arn:aws:autoscaling:$REGION:$ACCOUNT:autoScalingGroup:*:autoScalingGroupName/$NAME"},
 {"Effect":"Allow","Action":["autoscaling:DescribeAutoScalingGroups"],"Resource":"*"}
]}
JSON
)"
  sed -e "s|__BUCKET__|$BUCKET|; s|__PARAM__|$PARAM|; s|__ASG__|$NAME|; s|__REGION__|$REGION|" tools/aws/user-data.sh > "$B/user-data.sh"
  UD=$(base64 < "$B/user-data.sh" | tr -d '\n')
  FIRST=$(echo $INSTANCE_TYPES | awk '{print $1}')
  LT_DATA=$(cat <<JSON
{"ImageId":"resolve:ssm:/aws/service/canonical/ubuntu/server/24.04/stable/current/amd64/hvm/ebs-gp3/ami-id",
 "InstanceType":"$FIRST","IamInstanceProfile":{"Name":"$ROLE"},"UserData":"$UD",
 "BlockDeviceMappings":[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":40,"VolumeType":"gp3","Encrypted":true,"DeleteOnTermination":true}}],
 "MetadataOptions":{"HttpTokens":"required","HttpPutResponseHopLimit":1},
 "TagSpecifications":[{"ResourceType":"instance","Tags":[{"Key":"Name","Value":"$NAME"}]}]}
JSON
)
  if aws ec2 describe-launch-templates --launch-template-names "$NAME" >/dev/null 2>&1; then
    V=$(aws ec2 create-launch-template-version --launch-template-name "$NAME" --launch-template-data "$LT_DATA" --query 'LaunchTemplateVersion.VersionNumber' --output text)
    aws ec2 modify-launch-template --launch-template-name "$NAME" --default-version "$V" >/dev/null
    echo "launch template $NAME version $V"
  else
    aws ec2 create-launch-template --launch-template-name "$NAME" --launch-template-data "$LT_DATA" >/dev/null
    echo "launch template $NAME created"
  fi
  SUBNETS=$(aws ec2 describe-subnets --filters Name=default-for-az,Values=true --query 'Subnets[].SubnetId' --output text | tr '\t' ',')
  if [ -z "$SUBNETS" ]; then   # a region with no default VPC: create the standard one (free) — public subnets in every zone
    aws ec2 create-default-vpc >/dev/null && echo "default VPC created in $REGION"
    SUBNETS=$(aws ec2 describe-subnets --filters Name=default-for-az,Values=true --query 'Subnets[].SubnetId' --output text | tr '\t' ',')
  fi
  OVERRIDES=$(for t in $INSTANCE_TYPES; do printf '{"InstanceType":"%s"},' "$t"; done | sed 's/,$//')
  MIP="{\"LaunchTemplate\":{\"LaunchTemplateSpecification\":{\"LaunchTemplateName\":\"$NAME\",\"Version\":\"\$Default\"},\"Overrides\":[$OVERRIDES]},\"InstancesDistribution\":{\"OnDemandPercentageAboveBaseCapacity\":0,\"SpotAllocationStrategy\":\"price-capacity-optimized\"}}"
  if aws autoscaling describe-auto-scaling-groups --auto-scaling-group-names "$NAME" --query 'AutoScalingGroups[0].AutoScalingGroupName' --output text 2>/dev/null | grep -q "$NAME"; then
    aws autoscaling update-auto-scaling-group --auto-scaling-group-name "$NAME" --mixed-instances-policy "$MIP" --capacity-rebalance
    echo "group $NAME updated"
  else
    sleep 10   # the instance profile propagates
    aws autoscaling create-auto-scaling-group --auto-scaling-group-name "$NAME" --mixed-instances-policy "$MIP" \
      --min-size 0 --max-size 1 --desired-capacity 0 --vpc-zone-identifier "$SUBNETS" --capacity-rebalance \
      --tags "Key=Name,Value=$NAME,PropagateAtLaunch=true"
    echo "group $NAME created (min 0, max 1, desired 0, spot, capacity rebalance)"
  fi
  echo "setup complete: bucket $BUCKET · parameter $PARAM · role $ROLE · template and group $NAME · types: $INSTANCE_TYPES"
  ;;
start)
  GRID="$2"; SEED="$3"; JOB=$(job_name "$GRID" "$SEED")
  if aws s3api head-object --bucket "$BUCKET" --key "checkpoint/$JOB/done.json" >/dev/null 2>&1; then
    echo "REFUSED: $JOB is already complete in S3 (checkpoint/$JOB/done.json); pull it, or remove the marker to run again"; exit 1; fi
  D=$(aws autoscaling describe-auto-scaling-groups --auto-scaling-group-names "$NAME" --query 'AutoScalingGroups[0].DesiredCapacity' --output text)
  [ "$D" = "0" ] || { echo "REFUSED: the group is already at desired $D; stop it first"; exit 1; }
  git bundle create "$B/repo.bundle" HEAD 2>/dev/null
  # M14.7: the manifest whole (it is a chain) and only the bars the grid's universes and the classifier's index need
  INPUTS=$($PY -m occams survey inputs "$GRID" --register "$REGISTER" --archive archive)
  tar czf "$B/archive.tgz" $INPUTS
  echo "archive input: $(echo "$INPUTS" | wc -l | tr -d ' ') files (the manifest and the grid's bars), of $(ls archive/bars | wc -l | tr -d ' ') series archived"
  COUNT=$($PY -c "from occams.survey.grid import load; from occams.register import Register; print(load('$GRID', register=Register('$REGISTER')).count)")
  aws s3 cp "$B/repo.bundle" "s3://$BUCKET/input/repo.bundle" --quiet
  aws s3 cp "$B/archive.tgz" "s3://$BUCKET/input/archive.tgz" --quiet
  printf '{"grid":"%s","grid_name":"%s","seed":%s,"cell_count":%s,"config_name":"%s","register":"%s","started":"%s","commit":"%s"}\n' \
    "$GRID" "${JOB%-seed*}" "$SEED" "$COUNT" "$(basename "$CONFIG")" "$REGISTER" "$(date -u +%FT%TZ)" "$(git rev-parse --short HEAD)" > "$B/job.json"
  aws s3 cp "$B/job.json" "s3://$BUCKET/jobs/current.json" --quiet
  aws autoscaling set-desired-capacity --auto-scaling-group-name "$NAME" --desired-capacity 1
  echo "job $JOB: $COUNT cells, commit $(git rev-parse --short HEAD); group scaled to one at $(date -u +%FT%TZ); checkpoint s3://$BUCKET/checkpoint/$JOB/"
  ;;
status)
  JOB=$(job_name "$2" "$3")
  aws autoscaling describe-auto-scaling-groups --auto-scaling-group-names "$NAME" \
    --query 'AutoScalingGroups[0].{desired:DesiredCapacity,instances:Instances[].[InstanceId,InstanceType,LifecycleState,HealthStatus]}' --output text | sed 's/^/group: /'
  aws s3 cp "s3://$BUCKET/checkpoint/$JOB/progress.json" - 2>/dev/null | $PY -c "import json,sys; d=json.load(sys.stdin); print(f\"{d['state']} · {d['cells_done']:,}/{d['cells_total']:,} cells · {d['type']} {d['instance']} · heartbeat {d['heartbeat']} · {d['last_line']}\")" 2>/dev/null || echo "no progress record yet"
  aws s3 cp "s3://$BUCKET/checkpoint/$JOB/done.json" - 2>/dev/null | sed 's/^/done: /' || true
  ;;
watch)
  JOB=$(job_name "$2" "$3"); last=""
  while true; do
    line=$(aws s3 cp "s3://$BUCKET/checkpoint/$JOB/progress.json" - 2>/dev/null | $PY -c "import json,sys; d=json.load(sys.stdin); print(f\"{d['state']} · {d['cells_done']:,}/{d['cells_total']:,} cells · {d['type']} {d['instance']} · {d['heartbeat']}\")" 2>/dev/null || echo "waiting for the box's first progress record")
    [ "$line" != "$last" ] && echo "$line" && last="$line"
    if aws s3api head-object --bucket "$BUCKET" --key "checkpoint/$JOB/done.json" >/dev/null 2>&1; then echo "DONE $JOB $(aws s3 cp "s3://$BUCKET/checkpoint/$JOB/done.json" - 2>/dev/null)"; exit 0; fi
    D=$(aws autoscaling describe-auto-scaling-groups --auto-scaling-group-names "$NAME" --query 'AutoScalingGroups[0].DesiredCapacity' --output text 2>/dev/null || echo "?")
    if [ "$D" = "0" ] && [ "$last" != "waiting for the box's first progress record" ]; then
      echo "STOPPED: the group is at zero without a done marker — the box failed or was stopped; see status and console"; exit 1; fi
    if [ "$last" = "waiting for the box's first progress record" ]; then
      started=$(aws s3 cp "s3://$BUCKET/jobs/current.json" - 2>/dev/null | $PY -c "import json,sys,datetime as d; s=json.load(sys.stdin)['started']; print(int((d.datetime.now(d.timezone.utc)-d.datetime.fromisoformat(s.replace('Z','+00:00'))).total_seconds()))" 2>/dev/null || echo 0)
      [ "$started" -gt 1200 ] && echo "NO REPORT: $((started / 60)) minutes since start and no progress record — run \`burst.sh console\`; the box scales itself to zero on a failed boot" && last="no report"
    fi
    sleep 300
  done
  ;;
console)
  IID=$(aws autoscaling describe-auto-scaling-groups --auto-scaling-group-names "$NAME" --query 'AutoScalingGroups[0].Instances[0].InstanceId' --output text)
  [ -n "$IID" ] && [ "$IID" != "None" ] || { echo "no instance in the group"; exit 1; }
  aws ec2 get-console-output --instance-id "$IID" --latest --output text 2>/dev/null | grep -aE "cloud-init\[" | grep -avE "^\s*$" | sed -E 's/^.*cloud-init\[[0-9]+\]: //' | tail -40 | cut -c1-200
  ;;
pull)
  JOB=$(job_name "$2" "$3")
  T=$(aws s3 cp "s3://$BUCKET/checkpoint/$JOB/progress.json" - 2>/dev/null | $PY -c "import json,sys; print(json.load(sys.stdin)['type'])" 2>/dev/null || echo aws)
  DEST="archive/surveys/$JOB-$T"; mkdir -p "$DEST"
  aws s3 sync "s3://$BUCKET/checkpoint/$JOB/" "$DEST/" --quiet --exclude "progress.json" --exclude "done.json" --exclude "logs/*"
  aws s3 sync "s3://$BUCKET/checkpoint/$JOB/logs/" "$B/logs-$JOB/" --quiet
  echo "pulled into $DEST: $(ls "$DEST/cells" | wc -l | tr -d ' ') cells$( [ -f "$DEST/survey.json" ] && echo ', index present' ); logs in $B/logs-$JOB/"
  ;;
compare)
  $PY - "$2" "$3" <<'PY'
import hashlib, sys
from pathlib import Path
a, b = Path(sys.argv[1]) / "cells", Path(sys.argv[2]) / "cells"
ha = {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in a.glob("*.json")}
hb = {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in b.glob("*.json")}
common = [k for k in ha if k in hb]
same = sum(1 for k in common if ha[k] == hb[k])
print(f"{len(ha):,} cells in {a.parent.name}, {len(hb):,} in {b.parent.name}, {len(common):,} in both, {same:,} byte-identical, {len(common) - same:,} differ")
sys.exit(0 if common and same == len(common) else 1)
PY
  ;;
record)
  $PY -m occams survey record "$2" --out "$4" --register "$REGISTER" --seed "$3"
  ;;
stop)
  aws autoscaling set-desired-capacity --auto-scaling-group-name "$NAME" --desired-capacity 0 && echo "group scaled to zero; the checkpoint stays in S3"
  ;;
teardown)
  aws autoscaling delete-auto-scaling-group --auto-scaling-group-name "$NAME" --force-delete 2>/dev/null && echo "group deleted" || true
  aws ec2 delete-launch-template --launch-template-name "$NAME" >/dev/null 2>&1 && echo "launch template deleted" || true
  if [ "${2:-}" = "--all" ]; then
    aws s3 rm "s3://$BUCKET" --recursive --quiet && aws s3api delete-bucket --bucket "$BUCKET" && echo "bucket deleted"
    aws ssm delete-parameter --name "$PARAM" && echo "parameter deleted"
    aws iam remove-role-from-instance-profile --instance-profile-name "$ROLE" --role-name "$ROLE"
    aws iam delete-instance-profile --instance-profile-name "$ROLE"; aws iam delete-role-policy --role-name "$ROLE" --policy-name "$NAME"
    aws iam delete-role --role-name "$ROLE" && echo "role deleted"
  else
    echo "kept for reuse: bucket $BUCKET, parameter $PARAM, role $ROLE (teardown --all removes them)"
  fi
  ;;
*)
  sed -n 2,26p "$0"; exit 2 ;;
esac
