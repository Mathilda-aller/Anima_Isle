from app.utils.security import validate_password_strength


def test_validate_password_strength():
    assert validate_password_strength("abc12345") is True
    assert validate_password_strength("12345678") is False
    assert validate_password_strength("abcdefgh") is False
    assert validate_password_strength("abc123") is False
    assert validate_password_strength("a" * 65 + "1") is False
