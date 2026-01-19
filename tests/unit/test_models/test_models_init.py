"""Tests for models package __init__.py."""

from sqlalchemy import Column, Integer, MetaData, String
from sqlalchemy.orm import DeclarativeBase

from fastapi_auth.models import get_metadata
from fastapi_auth.models.base import Base


class TestGetMetadata:
    """Test get_metadata function."""

    def test_get_metadata_returns_metadata(self):
        """Test get_metadata returns a MetaData instance."""
        metadata = get_metadata()
        assert isinstance(metadata, MetaData)

    def test_get_metadata_returns_base_metadata(self):
        """Test get_metadata returns Base.metadata."""
        metadata = get_metadata()
        assert metadata is Base.metadata

    def test_get_metadata_contains_tables(self):
        """Test get_metadata contains expected tables."""
        metadata = get_metadata()
        assert len(metadata.tables) > 0
        # Verify some expected tables exist
        expected_tables = [
            "auth_users",
            "auth_roles",
            "auth_permissions",
            "social_providers",
        ]
        for table_name in expected_tables:
            assert table_name in metadata.tables

    def test_get_metadata_can_be_merged(self):
        """Test get_metadata can be merged with other metadata for Alembic."""

        # Create a test Base for another application
        class MyAppBase(DeclarativeBase):
            pass

        class MyModel(MyAppBase):
            __tablename__ = "my_table"
            id = Column(Integer, primary_key=True)
            name = Column(String)

        # Get metadata from fastapi_auth
        auth_metadata = get_metadata()

        # Merge metadata as shown in docstring example
        target_metadata = [MyAppBase.metadata, auth_metadata]

        # Verify both metadata objects are in the list
        assert len(target_metadata) == 2
        assert MyAppBase.metadata in target_metadata
        assert auth_metadata in target_metadata

        # Verify tables from both sources are accessible
        assert "my_table" in MyAppBase.metadata.tables
        assert "auth_users" in auth_metadata.tables
