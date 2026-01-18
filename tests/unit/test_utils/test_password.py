import bcrypt

from fastapi_auth.utils.password import hash_password, verify_password


class TestHashPassword:
    """Test password hashing functionality."""

    def test_hash_password_generates_valid_bcrypt_hash(self):
        """Test that hash_password generates a valid bcrypt hash."""
        password = "test_password_123"
        hashed = hash_password(password)

        # Check that it's a string (decoded from bytes)
        assert isinstance(hashed, str)

        # Verify it's a valid bcrypt hash by checking it starts with $2b$
        assert hashed.startswith("$2b$") or hashed.startswith("$2a$")

        # Verify the hash can be checked against the original password
        assert bcrypt.checkpw(password.encode(), hashed.encode())

    def test_hash_password_different_hashes_for_same_password(self):
        """Test that hashing the same password multiple times produces different hashes."""
        password = "test_password_123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        # Hashes should be different due to salt
        assert hash1 != hash2

        # But both should verify against the same password
        assert bcrypt.checkpw(password.encode(), hash1.encode())
        assert bcrypt.checkpw(password.encode(), hash2.encode())


class TestVerifyPassword:
    """Test password verification functionality."""

    def test_verify_password_with_correct_password(self):
        """Test verify_password with correct password."""
        password = "test_password_123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_with_incorrect_password(self):
        """Test verify_password with incorrect password."""
        password = "test_password_123"
        wrong_password = "wrong_password"
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_with_different_hash(self):
        """Test verify_password with hash from different password."""
        password1 = "test_password_123"
        password2 = "different_password"
        hashed1 = hash_password(password1)

        assert verify_password(password2, hashed1) is False
