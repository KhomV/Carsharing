"""Preserve existing crontab and add a single updater entry. Run after publication."""
from pathlib import Path
import subprocess

result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
if result.returncode and "no crontab" not in result.stderr.lower():
    raise RuntimeError(result.stderr)
lines = [line for line in result.stdout.splitlines() if "# carsharing-updater" not in line]
lines.append(
    "*/2 * * * * /bin/sh /home/khomch/carsharing/deploy/update.sh "
    "> /home/khomch/carsharing/deploy/update.log 2>&1 # carsharing-updater"
)
subprocess.run(["crontab", "-"], input="\n".join(lines) + "\n", text=True, check=True)
print("Installed updater (every 2 minutes), existing cron entries preserved")
