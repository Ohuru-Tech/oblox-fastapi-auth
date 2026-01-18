"""Tests for validator decorator."""

import pytest
from fastapi import HTTPException

from fastapi_auth.utils.decorators.validators import validate_args


class TestValidateArgs:
    """Test validate_args decorator."""

    @pytest.mark.asyncio
    async def test_required_validation_bool_true(self):
        """Test required validation with bool True."""

        @validate_args({"email": {"required": True}})
        async def test_func(email: str):
            return email

        with pytest.raises(HTTPException) as exc_info:
            await test_func(None)
        assert exc_info.value.status_code == 400
        assert "email is required" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_required_validation_dict(self):
        """Test required validation with dict message."""

        @validate_args({"email": {"required": {"message": "Email is mandatory"}}})
        async def test_func(email: str):
            return email

        with pytest.raises(HTTPException) as exc_info:
            await test_func(None)
        assert exc_info.value.status_code == 400
        assert "Email is mandatory" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_required_validation_empty_string(self):
        """Test required validation with empty string."""

        @validate_args({"email": {"required": True}})
        async def test_func(email: str):
            return email

        with pytest.raises(HTTPException) as exc_info:
            await test_func("")
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_min_length_validation(self):
        """Test minLength validation."""

        @validate_args({"name": {"minLength": {"value": 3, "message": "Too short"}}})
        async def test_func(name: str):
            return name

        with pytest.raises(HTTPException) as exc_info:
            await test_func("ab")
        assert exc_info.value.status_code == 400
        assert "Too short" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_max_length_validation(self):
        """Test maxLength validation."""

        @validate_args({"name": {"maxLength": {"value": 5, "message": "Too long"}}})
        async def test_func(name: str):
            return name

        with pytest.raises(HTTPException) as exc_info:
            await test_func("toolongname")
        assert exc_info.value.status_code == 400
        assert "Too long" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_min_validation(self):
        """Test min validation for numbers."""

        @validate_args({"age": {"min": {"value": 18, "message": "Too young"}}})
        async def test_func(age: int):
            return age

        with pytest.raises(HTTPException) as exc_info:
            await test_func(17)
        assert exc_info.value.status_code == 400
        assert "Too young" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_max_validation(self):
        """Test max validation for numbers."""

        @validate_args({"age": {"max": {"value": 100, "message": "Too old"}}})
        async def test_func(age: int):
            return age

        with pytest.raises(HTTPException) as exc_info:
            await test_func(101)
        assert exc_info.value.status_code == 400
        assert "Too old" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_pattern_validation(self):
        """Test pattern validation."""

        @validate_args(
            {
                "email": {
                    "pattern": {
                        "value": r"^[^@]+@[^@]+\.[^@]+$",
                        "message": "Invalid email format",
                    }
                }
            }
        )
        async def test_func(email: str):
            return email

        with pytest.raises(HTTPException) as exc_info:
            await test_func("invalid-email")
        assert exc_info.value.status_code == 400
        assert "Invalid email format" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_pattern_validation_success(self):
        """Test pattern validation with valid value."""

        @validate_args(
            {
                "email": {
                    "pattern": {
                        "value": r"^[^@]+@[^@]+\.[^@]+$",
                        "message": "Invalid email format",
                    }
                }
            }
        )
        async def test_func(email: str):
            return email

        result = await test_func("test@example.com")
        assert result == "test@example.com"

    @pytest.mark.asyncio
    async def test_validate_callable_true(self):
        """Test validate callable that returns True."""

        def custom_validator(value):
            return value.startswith("test")

        @validate_args({"value": {"validate": custom_validator}})
        async def test_func(value: str):
            return value

        result = await test_func("test_value")
        assert result == "test_value"

    @pytest.mark.asyncio
    async def test_validate_callable_false(self):
        """Test validate callable that returns False."""

        def custom_validator(value):
            return value.startswith("test")

        @validate_args({"value": {"validate": custom_validator}})
        async def test_func(value: str):
            return value

        with pytest.raises(HTTPException) as exc_info:
            await test_func("invalid_value")
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_validate_callable_error_message(self):
        """Test validate callable that returns error message."""

        def custom_validator(value):
            if not value.startswith("test"):
                return "Must start with 'test'"
            return True

        @validate_args({"value": {"validate": custom_validator}})
        async def test_func(value: str):
            return value

        with pytest.raises(HTTPException) as exc_info:
            await test_func("invalid_value")
        assert exc_info.value.status_code == 400
        assert "Must start with 'test'" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_multiple_validations(self):
        """Test multiple validation rules."""

        @validate_args(
            {
                "email": {
                    "required": True,
                    "pattern": {
                        "value": r"^[^@]+@[^@]+\.[^@]+$",
                        "message": "Invalid email",
                    },
                },
                "age": {
                    "required": True,
                    "min": {"value": 18, "message": "Too young"},
                    "max": {"value": 100, "message": "Too old"},
                },
            }
        )
        async def test_func(email: str, age: int):
            return {"email": email, "age": age}

        # Test valid input
        result = await test_func("test@example.com", 25)
        assert result["email"] == "test@example.com"
        assert result["age"] == 25

        # Test invalid email
        with pytest.raises(HTTPException):
            await test_func("invalid-email", 25)

        # Test invalid age
        with pytest.raises(HTTPException):
            await test_func("test@example.com", 15)

    @pytest.mark.asyncio
    async def test_optional_field_not_required(self):
        """Test that optional fields pass validation when None."""

        @validate_args({"name": {"minLength": {"value": 3, "message": "Too short"}}})
        async def test_func(name: str | None = None):
            return name

        result = await test_func(None)
        assert result is None

    @pytest.mark.asyncio
    async def test_skip_validation_when_none_and_not_required(self):
        """Test that validation is skipped for None values when not required."""

        @validate_args({"name": {"minLength": {"value": 3, "message": "Too short"}}})
        async def test_func(name: str | None = None):
            return name

        result = await test_func(None)
        assert result is None

    @pytest.mark.asyncio
    async def test_kwargs_validation(self):
        """Test validation works with kwargs."""

        @validate_args({"email": {"required": True}})
        async def test_func(email: str):
            return email

        result = await test_func(email="test@example.com")
        assert result == "test@example.com"

    @pytest.mark.asyncio
    async def test_args_and_kwargs_validation(self):
        """Test validation works with both args and kwargs."""

        @validate_args(
            {
                "email": {"required": True},
                "age": {"min": {"value": 18, "message": "Too young"}},
            }
        )
        async def test_func(email: str, age: int):
            return {"email": email, "age": age}

        result = await test_func("test@example.com", age=25)
        assert result["email"] == "test@example.com"
        assert result["age"] == 25
