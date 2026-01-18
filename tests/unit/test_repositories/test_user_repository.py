import pytest

from fastapi_auth.repositories.user_repository import UserRepository
from fastapi_auth.schemas.user import UserSignupSchema


class TestUserRepositoryCreateUser:
    """Test UserRepository create_user method."""

    @pytest.mark.asyncio
    async def test_create_user_creates_user_with_correct_fields(self, db_session):
        """Test that create_user creates a user with correct fields."""
        repository = UserRepository(db_session)

        user_signup = UserSignupSchema(
            email="test@example.com",
            name="Test User",
            password="test_password",
            profile_pic="https://example.com/pic.jpg",
        )

        created_user = await repository.create_user(user_signup)

        assert created_user is not None
        assert created_user.email == user_signup.email
        assert created_user.name == user_signup.name
        assert created_user.profile_pic == user_signup.profile_pic
        assert created_user.password is not None

    @pytest.mark.asyncio
    async def test_create_user_with_minimal_fields(self, db_session):
        """Test create_user with minimal required fields."""
        repository = UserRepository(db_session)

        user_signup = UserSignupSchema(
            email="minimal@example.com",
            password=None,
            name=None,
            profile_pic=None,
        )

        created_user = await repository.create_user(user_signup)

        assert created_user is not None
        assert created_user.email == user_signup.email
        assert created_user.name is None
        assert created_user.profile_pic is None


class TestUserRepositoryGetUserByEmail:
    """Test UserRepository get_user_by_email method."""

    @pytest.mark.asyncio
    async def test_get_user_by_email_finds_existing_user(self, db_session, test_user):
        """Test that get_user_by_email finds an existing user."""
        repository = UserRepository(db_session)

        found_user = await repository.get_user_by_email(email=test_user.email)

        assert found_user is not None
        assert found_user.email == test_user.email
        assert found_user.id == test_user.id

    @pytest.mark.asyncio
    async def test_get_user_by_email_returns_none_for_nonexistent_user(
        self, db_session
    ):
        """Test that get_user_by_email returns None for non-existent user."""
        repository = UserRepository(db_session)

        found_user = await repository.get_user_by_email(email="nonexistent@example.com")

        assert found_user is None


class TestUserRepositoryGetUserById:
    """Test UserRepository get_user_by_id method."""

    @pytest.mark.asyncio
    async def test_get_user_by_id_finds_existing_user(self, db_session, test_user):
        """Test that get_user_by_id finds an existing user."""
        repository = UserRepository(db_session)

        found_user = await repository.get_user_by_id(user_id=test_user.id)

        assert found_user is not None
        assert found_user.id == test_user.id
        assert found_user.email == test_user.email

    @pytest.mark.asyncio
    async def test_get_user_by_id_returns_none_for_nonexistent_user(self, db_session):
        """Test that get_user_by_id returns None for non-existent user."""
        repository = UserRepository(db_session)

        found_user = await repository.get_user_by_id(user_id=99999)

        assert found_user is None
