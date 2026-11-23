"""Create server-only credentials without printing them. Run once on the server."""
import os
from pathlib import Path
import secrets

path = Path(__file__).resolve().parent.parent / ".env.server"
content = "\n".join([
    "APP_BIND_IP=192.168.0.36",
    f"RENTAL_DB_PASSWORD={secrets.token_hex(24)}",
    f"BOOKING_DB_PASSWORD={secrets.token_hex(24)}",
    f"PAYMENT_DB_PASSWORD={secrets.token_hex(24)}",
    f"TELEMETRY_DB_PASSWORD={secrets.token_hex(24)}",
    f"RABBITMQ_PASSWORD={secrets.token_hex(24)}",
    f"AUTH_DB_PASSWORD={secrets.token_hex(24)}",
    f"LICENSE_DB_PASSWORD={secrets.token_hex(24)}",
    f"CONDITION_DB_PASSWORD={secrets.token_hex(24)}",
    f"SUPPORT_DB_PASSWORD={secrets.token_hex(24)}",
    f"LICENSE_STATUS_KEY={secrets.token_hex(24)}",
    "CONDITION_S3_USER=carsharing-storage",
    f"CONDITION_S3_PASSWORD={secrets.token_hex(24)}",
    "",
])
fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(fd, "w", encoding="utf-8") as stream:
    stream.write(content)
print("Created .env.server (credentials are not displayed)")
