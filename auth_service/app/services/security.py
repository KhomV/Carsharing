from hashlib import sha256, scrypt
from hmac import compare_digest
from secrets import token_bytes


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt if salt is not None else token_bytes(16)
    digest = scrypt(
        password.encode(), salt=salt, n=2**15, r=8, p=3,
        maxmem=64 * 1024 * 1024, dklen=32,
    )
    return f"{salt.hex()}:{digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    salt, _ = stored_hash.split(":", 1)
    return compare_digest(hash_password(password, bytes.fromhex(salt)), stored_hash)


def token_digest(token: str) -> str:
    return sha256(token.encode()).hexdigest()
