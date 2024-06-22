import hashlib
import base64

CROCKFORD_ALPHABET = '0123456789ABCDEFGHJKMNPQRSTVWXYZ'


def encode_sha256_base32(s):
    hash_object = hashlib.sha256(s.encode())
    hash_bytes = hash_object.digest()
    encoded = base64.b32encode(hash_bytes)
    encoded = encoded.decode('utf-8').replace('=', '')
    return encoded[:8]