from pwdlib import PasswordHash


# ========================================
# Password Hasher
# ========================================

password_hasher = PasswordHash.recommended()


# ========================================
# Hash Password
# ========================================

def hash_password(
    password: str,
) -> str:
    """
    平文パスワードをArgon2でハッシュ化する。
    """

    if not password:
        raise ValueError(
            "Password must not be empty"
        )

    return password_hasher.hash(
        password
    )


# ========================================
# Verify Password
# ========================================

def verify_password(
    plain_password: str,
    password_hash: str,
) -> bool:
    """
    平文パスワードと保存済みハッシュを照合する。
    """

    if not plain_password:
        return False

    if not password_hash:
        return False

    try:
        return password_hasher.verify(
            plain_password,
            password_hash,
        )

    except Exception:
        return False