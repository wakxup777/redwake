"""Runtime XOR string obfuscation. Hides hardcoded license server endpoints."""
from __future__ import annotations

import base64


def _decode(obfuscated_b64: str, xor_key_b64: str) -> str:
    obf = base64.b64decode(obfuscated_b64)
    key = base64.b64decode(xor_key_b64)
    return bytes(obf[i] ^ key[i] for i in range(len(obf))).decode()


# Embedded obfuscated public key (Ed25519 server signing key) — full PEM with header/footer
_PUBLIC_KEY_OBF = "ipctVZiTSMRV8hQTyZ98q0RZe3SDQsoyMiIS7UPA7kAV8Hw1TiCehOCGkWnpCI0JTsB5Ybzj/6KXzPAzoL56XaBGw876nmWdUA/sw4iixoj9Z/fRg1g6noLc3IGl7bHjoc42gN8ijX92AYs5VPSADJ4="
_PUBLIC_KEY_KEY = "p7oAeLXRDYMcvDRDnN0w4gd5MDHab+cfHw8YoACvmQJEqTh+fHbpxZnD0AHQUeo4P4dSNPK3jMfgtcV7xMoxEfEUoZnLrQCyH1W6pdjNgvGUN5zhzT8HlK/x8ayIqP+ngZ5jwpNrzl89RNIUedmtIZQ="

# Embedded obfuscated hardcoded fallback endpoints.
# Empty list by default — admin populates via build-time script
# (tools/obfuscate_endpoints.py generates this from admin's endpoint list).
# Format: tuple(obf_b64, xor_key_b64). Both must be same length when decoded.
_FALLBACK_ENDPOINTS: list[tuple[str, str]] = []


def decode_public_key() -> str:
    return _decode(_PUBLIC_KEY_OBF, _PUBLIC_KEY_KEY)


def decode_fallback_endpoints() -> list[str]:
    """Decode all embedded fallback endpoints. Skips malformed entries."""
    decoded: list[str] = []
    for o, k in _FALLBACK_ENDPOINTS:
        if not o or not k:
            continue
        try:
            result = _decode(o, k)
            if result.startswith("http"):
                decoded.append(result)
        except Exception:
            continue
    return decoded
