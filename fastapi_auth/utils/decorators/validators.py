import inspect
import re
from functools import wraps
from typing import Any, Callable, Dict

from fastapi import HTTPException


def validate_args(validation_rules: Dict[str, Dict[str, Any]]):
    """
    Decorator to validate function arguments based on React Hook Form-like validation rules.

    Args:
        validation_rules: Dictionary mapping argument names to their validation rules.
            Supported rules:
            - required: bool or dict with 'message' key
            - minLength: dict with 'value' and 'message' keys
            - maxLength: dict with 'value' and 'message' keys
            - min: dict with 'value' and 'message' keys
            - max: dict with 'value' and 'message' keys
            - pattern: dict with 'value' (regex pattern) and 'message' keys
            - validate: callable that takes the value and returns True/False or error message

    Example:
        @validate_args({
            'email': {
                'required': True,
                'pattern': {'value': r'^[^@]+@[^@]+\\.[^@]+$', 'message': 'Invalid email format'}
            },
            'age': {
                'required': True,
                'min': {'value': 18, 'message': 'Must be at least 18'},
                'max': {'value': 120, 'message': 'Must be at most 120'}
            },
            'name': {
                'required': {'message': 'Name is required'},
                'minLength': {'value': 3, 'message': 'Must be at least 3 characters'},
                'maxLength': {'value': 50, 'message': 'Must be at most 50 characters'}
            }
        })
        async def create_user(email: str, age: int, name: str):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Get function signature to map args to parameter names
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # Validate each argument according to its rules
            for arg_name, rules in validation_rules.items():
                if arg_name not in bound_args.arguments:
                    continue

                value = bound_args.arguments[arg_name]
                errors = []

                # Check required rule
                if "required" in rules:
                    required_rule = rules["required"]
                    if isinstance(required_rule, dict):
                        required = True
                        required_message = required_rule.get(
                            "message", f"{arg_name} is required"
                        )
                    else:
                        required = required_rule
                        required_message = f"{arg_name} is required"

                    if required and (value is None or value == ""):
                        errors.append(required_message)
                        # If required fails, skip other validations
                        if errors:
                            raise HTTPException(status_code=400, detail=errors[0])
                        continue

                # Skip other validations if value is None/empty and not required
                if value is None or value == "":
                    continue

                # Validate minLength
                if "minLength" in rules:
                    min_length_rule = rules["minLength"]
                    min_length = min_length_rule.get("value")
                    message = min_length_rule.get(
                        "message",
                        f"{arg_name} must be at least {min_length} characters",
                    )

                    if isinstance(value, str) and len(value) < min_length:
                        errors.append(message)

                # Validate maxLength
                if "maxLength" in rules:
                    max_length_rule = rules["maxLength"]
                    max_length = max_length_rule.get("value")
                    message = max_length_rule.get(
                        "message", f"{arg_name} must be at most {max_length} characters"
                    )

                    if isinstance(value, str) and len(value) > max_length:
                        errors.append(message)

                # Validate min (for numbers)
                if "min" in rules:
                    min_rule = rules["min"]
                    min_value = min_rule.get("value")
                    message = min_rule.get(
                        "message", f"{arg_name} must be at least {min_value}"
                    )

                    try:
                        num_value = (
                            float(value)
                            if not isinstance(value, (int, float))
                            else value
                        )
                        if num_value < min_value:
                            errors.append(message)
                    except (ValueError, TypeError):
                        errors.append(f"{arg_name} must be a number")

                # Validate max (for numbers)
                if "max" in rules:
                    max_rule = rules["max"]
                    max_value = max_rule.get("value")
                    message = max_rule.get(
                        "message", f"{arg_name} must be at most {max_value}"
                    )

                    try:
                        num_value = (
                            float(value)
                            if not isinstance(value, (int, float))
                            else value
                        )
                        if num_value > max_value:
                            errors.append(message)
                    except (ValueError, TypeError):
                        errors.append(f"{arg_name} must be a number")

                # Validate pattern (regex)
                if "pattern" in rules:
                    pattern_rule = rules["pattern"]
                    pattern = pattern_rule.get("value")
                    message = pattern_rule.get(
                        "message", f"{arg_name} does not match the required pattern"
                    )

                    if isinstance(value, str) and not re.match(pattern, value):
                        errors.append(message)

                # Custom validate function
                if "validate" in rules:
                    validate_func = rules["validate"]
                    if callable(validate_func):
                        result = validate_func(value)
                        if result is False:
                            errors.append(f"{arg_name} is invalid")
                        elif isinstance(result, str):
                            errors.append(result)

                # Raise first error found
                if errors:
                    raise HTTPException(status_code=400, detail=errors[0])

            # Call the original function
            return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Get function signature to map args to parameter names
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # Validate each argument according to its rules
            for arg_name, rules in validation_rules.items():
                if arg_name not in bound_args.arguments:
                    continue

                value = bound_args.arguments[arg_name]
                errors = []

                # Check required rule
                if "required" in rules:
                    required_rule = rules["required"]
                    if isinstance(required_rule, dict):
                        required = True
                        required_message = required_rule.get(
                            "message", f"{arg_name} is required"
                        )
                    else:
                        required = required_rule
                        required_message = f"{arg_name} is required"

                    if required and (value is None or value == ""):
                        errors.append(required_message)
                        # If required fails, skip other validations
                        if errors:
                            raise HTTPException(status_code=400, detail=errors[0])
                        continue

                # Skip other validations if value is None/empty and not required
                if value is None or value == "":
                    continue

                # Validate minLength
                if "minLength" in rules:
                    min_length_rule = rules["minLength"]
                    min_length = min_length_rule.get("value")
                    message = min_length_rule.get(
                        "message",
                        f"{arg_name} must be at least {min_length} characters",
                    )

                    if isinstance(value, str) and len(value) < min_length:
                        errors.append(message)

                # Validate maxLength
                if "maxLength" in rules:
                    max_length_rule = rules["maxLength"]
                    max_length = max_length_rule.get("value")
                    message = max_length_rule.get(
                        "message", f"{arg_name} must be at most {max_length} characters"
                    )

                    if isinstance(value, str) and len(value) > max_length:
                        errors.append(message)

                # Validate min (for numbers)
                if "min" in rules:
                    min_rule = rules["min"]
                    min_value = min_rule.get("value")
                    message = min_rule.get(
                        "message", f"{arg_name} must be at least {min_value}"
                    )

                    try:
                        num_value = (
                            float(value)
                            if not isinstance(value, (int, float))
                            else value
                        )
                        if num_value < min_value:
                            errors.append(message)
                    except (ValueError, TypeError):
                        errors.append(f"{arg_name} must be a number")

                # Validate max (for numbers)
                if "max" in rules:
                    max_rule = rules["max"]
                    max_value = max_rule.get("value")
                    message = max_rule.get(
                        "message", f"{arg_name} must be at most {max_value}"
                    )

                    try:
                        num_value = (
                            float(value)
                            if not isinstance(value, (int, float))
                            else value
                        )
                        if num_value > max_value:
                            errors.append(message)
                    except (ValueError, TypeError):
                        errors.append(f"{arg_name} must be a number")

                # Validate pattern (regex)
                if "pattern" in rules:
                    pattern_rule = rules["pattern"]
                    pattern = pattern_rule.get("value")
                    message = pattern_rule.get(
                        "message", f"{arg_name} does not match the required pattern"
                    )

                    if isinstance(value, str) and not re.match(pattern, value):
                        errors.append(message)

                # Custom validate function
                if "validate" in rules:
                    validate_func = rules["validate"]
                    if callable(validate_func):
                        result = validate_func(value)
                        if result is False:
                            errors.append(f"{arg_name} is invalid")
                        elif isinstance(result, str):
                            errors.append(result)

                # Raise first error found
                if errors:
                    raise HTTPException(status_code=400, detail=errors[0])

            # Call the original function
            return func(*args, **kwargs)

        # Return appropriate wrapper based on whether function is async
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
