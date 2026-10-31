from app.core.security import generate_token, hash_password, hash_token, verify_password


def test_password_hash_is_not_plaintext() -> None:
    password = "a-correct-horse-battery-staple"
    password_hash = hash_password(password)
    assert password_hash != password
    assert verify_password(password_hash, password)
    assert not verify_password(password_hash, "wrong-password")


def test_tokens_are_random_and_stored_as_hashes() -> None:
    first = generate_token()
    second = generate_token()
    assert first != second
    assert hash_token(first) != first
    assert len(hash_token(first)) == 64
