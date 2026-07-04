"""Ed25519 wrapper for license JWT verification."""
from __future__ import annotations

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
import jwt

from ._obfuscate import decode_public_key


def _load_public_key() -> Ed25519PublicKey:
    pem = decode_public_key()
    return serialization.load_pem_public_key(pem.encode())


def verify_jwt(token: str) -> dict:
    """Verify Ed25519-signed JWT and return claims. Raises on failure."""
    pub = _load_public_key()
    # PyJWT requires cryptography key for EdDSA
    return jwt.decode(
        token,
        pub,
        algorithms=["EdDSA"],
        options={"require": ["exp", "sub", "uid"]},
    )


def sign_jwt(payload: dict, private_key) -> str:
    """Sign a JWT with an Ed25519 private key (server-side use)."""
    return jwt.encode(payload, private_key, algorithm="EdDSA")
