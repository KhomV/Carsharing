"""Add missing server secrets without changing passwords of existing databases."""
from datetime import datetime, timezone
from pathlib import Path
import os
import secrets
import shutil

root = Path(__file__).resolve().parent.parent
path = root / '.env.server'
backup = root.parent / 'carsharing-backups' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
backup.mkdir(parents=True, mode=0o700)
shutil.copy2(path, backup / '.env.server')
shutil.copy2(root / 'compose.server.yaml', backup / 'compose.server.yaml')
os.chmod(backup / '.env.server', 0o600)
text = path.read_text(encoding='utf-8')
keys = {line.partition('=')[0] for line in text.splitlines() if '=' in line and not line.startswith('#')}
additions = []
for key in ('BOOKING_DB_PASSWORD', 'TELEMETRY_DB_PASSWORD'):
    if key not in keys:
        additions.append(f'{key}={secrets.token_hex(24)}')
for key, image in [('RENTAL_IMAGE','carsharing-rental'),('PAYMENT_IMAGE','carsharing-payment'),
                   ('BOOKING_IMAGE','carsharing-booking'),('TELEMETRY_IMAGE','carsharing-telemetry')]:
    if key not in keys:
        additions.append(f'{key}=khommv/{image}:latest')
if additions:
    with path.open('a', encoding='utf-8') as stream:
        stream.write('\n' + '\n'.join(additions) + '\n')
os.chmod(path, 0o600)
print('Added settings:', ', '.join(line.partition('=')[0] for line in additions) or 'none')
print('Backup:', backup)
