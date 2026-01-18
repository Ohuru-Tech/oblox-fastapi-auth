"""Extended tests for validator decorator covering sync functions and edge cases."""

import pytest
from fastapi import HTTPException

from fastapi_auth.utils.decorators.validators import validate_args


class TestValidateArgsSync:
    """Test validate_args decorator with sync functions."""

    def test_sync_required_validation(self):
        """Test required validation with sync function."""

        @validate_args({"email": {"required": True}})
        def test_func(email: str):
            return email

        with pytest.raises(HTTPException) as exc_info:
            test_func(None)
        assert exc_info.value.status_code == 400

    def test_sync_min_length_validation(self):
        """Test minLength validation with sync function."""

        @validate_args({"name": {"minLength": {"value": 3, "message": "Too short"}}})
        def test_func(name: str):
            return name

        with pytest.raises(HTTPException) as exc_info:
            test_func("ab")
        assert exc_info.value.status_code == 400
        assert "Too short" in exc_info.value.detail

    def test_sync_max_length_validation(self):
        """Test maxLength validation with sync function."""

        @validate_args({"name": {"maxLength": {"value": 5, "message": "Too long"}}})
        def test_func(name: str):
            return name

        with pytest.raises(HTTPException) as exc_info:
            test_func("toolongname")
        assert exc_info.value.status_code == 400

    def test_sync_min_validation(self):
        """Test min validation with sync function."""

        @validate_args({"age": {"min": {"value": 18, "message": "Too young"}}})
        def test_func(age: int):
            return age

        with pytest.raises(HTTPException) as exc_info:
            test_func(17)
        assert exc_info.value.status_code == 400

    def test_sync_max_validation(self):
        """Test max validation with sync function."""

        @validate_args({"age": {"max": {"value": 100, "message": "Too old"}}})
        def test_func(age: int):
            return age

        with pytest.raises(HTTPException) as exc_info:
            test_func(101)
        assert exc_info.value.status_code == 400

    def test_sync_pattern_validation(self):
        """Test pattern validation with sync function."""

        @validate_args(
            {
                "email": {
                    "pattern": {
                        "value": r"^[^@]+@[^@]+\.[^@]+$",
                        "message": "Invalid email",
                    }
                }
            }
        )
        def test_func(email: str):
            return email

        with pytest.raises(HTTPException) as exc_info:
            test_func("invalid-email")
        assert exc_info.value.status_code == 400

    def test_sync_validate_callable(self):
        """Test validate callable with sync function."""

        def custom_validator(value):
            return value.startswith("test")

        @validate_args({"value": {"validate": custom_validator}})
        def test_func(value: str):
            return value

        result = test_func("test_value")
        assert result == "test_value"

        with pytest.raises(HTTPException):
            test_func("invalid_value")


class TestValidateArgsNumberEdgeCases:
    """Test number validation edge cases."""

    @pytest.mark.asyncio
    async def test_min_validation_with_string_number(self):
        """Test min validation with string that can be converted to number."""

        @validate_args({"age": {"min": {"value": 18, "message": "Too young"}}})
        async def test_func(age):
            return age

        # String that can be converted to float
        with pytest.raises(HTTPException) as exc_info:
            await test_func("17")
        assert exc_info.value.status_code == 400

        # Valid number as string
        result = await test_func("25")
        assert result == "25"

    @pytest.mark.asyncio
    async def test_min_validation_with_invalid_string(self):
        """Test min validation with string that cannot be converted to number."""

        @validate_args({"age": {"min": {"value": 18, "message": "Too young"}}})
        async def test_func(age):
            return age

        with pytest.raises(HTTPException) as exc_info:
            await test_func("not_a_number")
        assert exc_info.value.status_code == 400
        assert "must be a number" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_max_validation_with_string_number(self):
        """Test max validation with string that can be converted to number."""

        @validate_args({"age": {"max": {"value": 100, "message": "Too old"}}})
        async def test_func(age):
            return age

        with pytest.raises(HTTPException) as exc_info:
            await test_func("101")
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_max_validation_with_invalid_string(self):
        """Test max validation with string that cannot be converted to number."""

        @validate_args({"age": {"max": {"value": 100, "message": "Too old"}}})
        async def test_func(age):
            return age

        with pytest.raises(HTTPException) as exc_info:
            await test_func("not_a_number")
        assert exc_info.value.status_code == 400
        assert "must be a number" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_min_validation_with_float(self):
        """Test min validation with float value."""

        @validate_args({"price": {"min": {"value": 10.0, "message": "Too low"}}})
        async def test_func(price):
            return price

        with pytest.raises(HTTPException) as exc_info:
            await test_func(9.5)
        assert exc_info.value.status_code == 400

        result = await test_func(10.5)
        assert result == 10.5

    @pytest.mark.asyncio
    async def test_max_validation_with_float(self):
        """Test max validation with float value."""

        @validate_args({"price": {"max": {"value": 100.0, "message": "Too high"}}})
        async def test_func(price):
            return price

        with pytest.raises(HTTPException) as exc_info:
            await test_func(100.5)
        assert exc_info.value.status_code == 400

    def test_sync_min_validation_with_string_number(self):
        """Test sync min validation with string number."""

        @validate_args({"age": {"min": {"value": 18, "message": "Too young"}}})
        def test_func(age):
            return age

        with pytest.raises(HTTPException):
            test_func("17")

    def test_sync_max_validation_with_string_number(self):
        """Test sync max validation with string number."""

        @validate_args({"age": {"max": {"value": 100, "message": "Too old"}}})
        def test_func(age):
            return age

        with pytest.raises(HTTPException):
            test_func("101")

    def test_sync_min_validation_with_invalid_string(self):
        """Test sync min validation with invalid string."""

        @validate_args({"age": {"min": {"value": 18, "message": "Too young"}}})
        def test_func(age):
            return age

        with pytest.raises(HTTPException) as exc_info:
            test_func("not_a_number")
        assert "must be a number" in exc_info.value.detail

    def test_sync_max_validation_with_invalid_string(self):
        """Test sync max validation with invalid string."""

        @validate_args({"age": {"max": {"value": 100, "message": "Too old"}}})
        def test_func(age):
            return age

        with pytest.raises(HTTPException) as exc_info:
            test_func("not_a_number")
        assert "must be a number" in exc_info.value.detail


class TestValidateArgsMultipleErrors:
    """Test multiple validation errors accumulation."""

    @pytest.mark.asyncio
    async def test_multiple_validations_accumulate_errors(self):
        """Test that multiple validation errors accumulate."""

        @validate_args(
            {
                "name": {
                    "minLength": {"value": 5, "message": "Name too short"},
                    "maxLength": {"value": 10, "message": "Name too long"},
                }
            }
        )
        async def test_func(name: str):
            return name

        # This should trigger minLength error first
        with pytest.raises(HTTPException) as exc_info:
            await test_func("ab")
        assert "Name too short" in exc_info.value.detail

        # This should trigger maxLength error
        with pytest.raises(HTTPException) as exc_info:
            await test_func("this_is_too_long")
        assert "Name too long" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_multiple_rules_single_field(self):
        """Test multiple rules on single field."""

        @validate_args(
            {
                "email": {
                    "required": True,
                    "pattern": {
                        "value": r"^[^@]+@[^@]+\.[^@]+$",
                        "message": "Invalid email",
                    },
                    "minLength": {"value": 5, "message": "Too short"},
                }
            }
        )
        async def test_func(email: str):
            return email

        # Missing email - should trigger required first
        with pytest.raises(HTTPException) as exc_info:
            await test_func(None)
        assert "required" in exc_info.value.detail.lower()

        # Invalid pattern
        with pytest.raises(HTTPException) as exc_info:
            await test_func("bad")
        assert (
            "Invalid email" in exc_info.value.detail
            or "Too short" in exc_info.value.detail
        )

    def test_sync_multiple_validations(self):
        """Test sync function with multiple validations."""

        @validate_args(
            {
                "age": {
                    "min": {"value": 18, "message": "Too young"},
                    "max": {"value": 100, "message": "Too old"},
                }
            }
        )
        def test_func(age: int):
            return age

        with pytest.raises(HTTPException):
            test_func(17)

        with pytest.raises(HTTPException):
            test_func(101)

        result = test_func(25)
        assert result == 25

    @pytest.mark.asyncio
    async def test_async_required_validation_continue_statement_line_78(self):
        """Test async required validation continue statement (line 78)."""

        @validate_args(
            {
                "email": {"required": True},
                "name": {"minLength": {"value": 3, "message": "Too short"}},
            }
        )
        async def test_func(email: str, name: str = None):
            return {"email": email, "name": name}

        # When email is required and None, should raise before checking name
        # This tests the continue statement on line 78
        with pytest.raises(HTTPException) as exc_info:
            await test_func(None, "ab")
        assert exc_info.value.status_code == 400
        # Should raise on required, not on name validation
        assert "required" in exc_info.value.detail.lower()

    def test_sync_required_validation_continue_statement_line_205(self):
        """Test sync required validation continue statement (line 205)."""

        @validate_args(
            {
                "email": {"required": True},
                "name": {"minLength": {"value": 3, "message": "Too short"}},
            }
        )
        def test_func(email: str, name: str = None):
            return {"email": email, "name": name}

        # This tests the continue statement on line 205
        with pytest.raises(HTTPException) as exc_info:
            test_func(None, "ab")
        assert exc_info.value.status_code == 400
        assert "required" in exc_info.value.detail.lower()


class TestValidateArgsEdgeCases:
    """Test edge cases for validator decorator."""

    @pytest.mark.asyncio
    async def test_arg_not_in_bound_args(self):
        """Test validation when arg_name is not in bound_args."""

        @validate_args({"nonexistent": {"required": True}})
        async def test_func(email: str):
            return email

        # Should not raise error since 'nonexistent' is not in function signature
        result = await test_func("test@example.com")
        assert result == "test@example.com"

    @pytest.mark.asyncio
    async def test_required_false_with_empty_string(self):
        """Test required=False with empty string."""

        @validate_args(
            {
                "email": {
                    "required": False,
                    "minLength": {"value": 5, "message": "Too short"},
                }
            }
        )
        async def test_func(email: str = ""):
            return email

        # Empty string should skip validation when not required
        result = await test_func("")
        assert result == ""

    @pytest.mark.asyncio
    async def test_required_dict_with_default_message(self):
        """Test required dict without custom message."""

        @validate_args({"email": {"required": {"message": "Custom required message"}}})
        async def test_func(email: str = None):
            return email

        with pytest.raises(HTTPException) as exc_info:
            await test_func(None)
        assert "Custom required message" in exc_info.value.detail

    def test_sync_arg_not_in_bound_args(self):
        """Test sync validation when arg_name is not in bound_args."""

        @validate_args({"nonexistent": {"required": True}})
        def test_func(email: str):
            return email

        result = test_func("test@example.com")
        assert result == "test@example.com"

    def test_sync_required_false_with_empty_string(self):
        """Test sync required=False with empty string."""

        @validate_args(
            {
                "email": {
                    "required": False,
                    "minLength": {"value": 5, "message": "Too short"},
                }
            }
        )
        def test_func(email: str = ""):
            return email

        result = test_func("")
        assert result == ""

    def test_sync_required_dict_with_default_message(self):
        """Test sync required dict without custom message."""

        @validate_args({"email": {"required": {"message": "Custom required message"}}})
        def test_func(email: str = None):
            return email

        with pytest.raises(HTTPException) as exc_info:
            test_func(None)
        assert "Custom required message" in exc_info.value.detail

    def test_sync_validate_callable_returns_string(self):
        """Test sync validate callable that returns error string."""

        def custom_validator(value):
            if not value.startswith("test"):
                return "Must start with 'test'"
            return True

        @validate_args({"value": {"validate": custom_validator}})
        def test_func(value: str):
            return value

        with pytest.raises(HTTPException) as exc_info:
            test_func("invalid_value")
        assert "Must start with 'test'" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_required_validation_continue_after_error(self):
        """Test that validation continues after required error (line 78)."""

        @validate_args({"email": {"required": True}})
        async def test_func(email: str):
            return email

        # When required fails, it should raise immediately and continue is not reached
        # But we test the path where errors list has items
        with pytest.raises(HTTPException) as exc_info:
            await test_func(None)
        assert exc_info.value.status_code == 400

    def test_sync_required_validation_continue_after_error(self):
        """Test sync required validation continue path (line 205)."""

        @validate_args({"email": {"required": True}})
        def test_func(email: str):
            return email

        with pytest.raises(HTTPException) as exc_info:
            test_func(None)
        assert exc_info.value.status_code == 400
