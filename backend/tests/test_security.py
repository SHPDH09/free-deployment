from cryptography.fernet import Fernet

from app.core.security import encrypt_value, decrypt_value, create_access_token, decode_access_token


def test_encrypt_decrypt():
    key = Fernet.generate_key().decode()
    import app.config
    app.config.settings.ENCRYPTION_KEY = key

    encrypted = encrypt_value("secret-value")
    assert encrypted != "secret-value"
    assert decrypt_value(encrypted) == "secret-value"


def test_jwt_roundtrip():
    token = create_access_token({"sub": "test-user-id"})
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "test-user-id"
