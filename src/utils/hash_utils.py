from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

ph = PasswordHasher()


def hash_password(password: str) -> str:
    """Hasher un mot de passe avec Argon2"""
    return ph.hash(password)


def verify_password(hashed_password: str, password: str) -> bool:
    """Verifier un mot de passe avec son hash"""
    try:
        ph.verify(hashed_password, password)
        return True
    except VerifyMismatchError:
        return False
