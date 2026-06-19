#!/usr/bin/env bash
# Daily cron wrapper. Add to crontab, e.g. run 07:00 every day:
#   0 7 * * *  /home/azureuser/ai-research-kb/scripts/run_daily.sh >> /home/azureuser/ai-research-kb/cron.log 2>&1
set -euo pipefail
cd "$(dirname "$0")/.."

# load .env if present
if [ -f .env ]; then
  set -a; . ./.env; set +a
fi

# activate venv if present
[ -d .venv ] && . .venv/bin/activate

python src/main.py
