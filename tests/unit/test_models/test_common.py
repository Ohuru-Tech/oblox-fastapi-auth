"""Tests for common models."""

from unittest.mock import Mock, patch

from fastapi_auth.models.common import EncryptedString, create_enum_column
from fastapi_auth.models.social_providers import SupportedProviders


class TestEncryptedString:
    """Test EncryptedString type decorator."""

    def test_process_bind_param_encrypts_value(self):
        """Test process_bind_param encrypts string value."""
        encrypted_string = EncryptedString()

        with patch("fastapi_auth.models.common.get_settings") as mock_get_settings:
            mock_settings = Mock()
            mock_settings.encryption_key = "test_key_32_bytes_long!!"
            mock_get_settings.return_value = mock_settings

            with patch("fastapi_auth.models.common.Fernet") as mock_fernet:
                mock_cipher = Mock()
                mock_cipher.encrypt.return_value = b"encrypted_value"
                mock_fernet.return_value = mock_cipher

                result = encrypted_string.process_bind_param("test_value", None)

                assert result == "encrypted_value"
                mock_cipher.encrypt.assert_called_once_with(b"test_value")

    def test_process_bind_param_none_value(self):
        """Test process_bind_param returns None for None value."""
        encrypted_string = EncryptedString()
        result = encrypted_string.process_bind_param(None, None)
        assert result is None

    def test_process_result_value_decrypts_value(self):
        """Test process_result_value decrypts string value."""
        encrypted_string = EncryptedString()

        with patch("fastapi_auth.models.common.get_settings") as mock_get_settings:
            mock_settings = Mock()
            mock_settings.encryption_key = "test_key_32_bytes_long!!"
            mock_get_settings.return_value = mock_settings

            with patch("fastapi_auth.models.common.Fernet") as mock_fernet:
                mock_cipher = Mock()
                mock_cipher.decrypt.return_value = b"decrypted_value"
                mock_fernet.return_value = mock_cipher

                result = encrypted_string.process_result_value("encrypted_value", None)

                assert result == "decrypted_value"
                mock_cipher.decrypt.assert_called_once_with(b"encrypted_value")

    def test_process_result_value_none_value(self):
        """Test process_result_value returns None for None value."""
        encrypted_string = EncryptedString()
        result = encrypted_string.process_result_value(None, None)
        assert result is None

    def test_get_cipher_lazy_initialization(self):
        """Test _get_cipher initializes cipher lazily."""
        encrypted_string = EncryptedString()
        assert encrypted_string._cipher is None

        with patch("fastapi_auth.models.common.get_settings") as mock_get_settings:
            mock_settings = Mock()
            mock_settings.encryption_key = "test_key_32_bytes_long!!"
            mock_get_settings.return_value = mock_settings

            with patch("fastapi_auth.models.common.Fernet") as mock_fernet:
                mock_cipher = Mock()
                mock_fernet.return_value = mock_cipher

                cipher1 = encrypted_string._get_cipher()
                cipher2 = encrypted_string._get_cipher()

                # Should only create cipher once
                assert mock_fernet.call_count == 1
                assert cipher1 is cipher2
                assert encrypted_string._cipher is not None


class TestCreateEnumColumn:
    """Test create_enum_column function."""

    def test_create_enum_column_default_name(self):
        """Test create_enum_column with default name."""
        enum_column = create_enum_column(SupportedProviders)

        assert enum_column is not None
        # Check that it's an Enum type
        from sqlalchemy import Enum

        assert isinstance(enum_column, Enum)

    def test_create_enum_column_custom_name(self):
        """Test create_enum_column with custom name."""
        enum_column = create_enum_column(
            SupportedProviders, name="custom_provider_type"
        )

        assert enum_column is not None
        from sqlalchemy import Enum

        assert isinstance(enum_column, Enum)
