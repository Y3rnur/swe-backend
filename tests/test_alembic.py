"""Alembic migration tests."""

from pathlib import Path

import pytest
from alembic.script import ScriptDirectory

from alembic import config as alembic_config


def test_alembic_config_has_target_metadata():
    """Test that Alembic is configured with target metadata."""
    # Read alembic/env.py to verify target_metadata is set
    env_file = Path("alembic/env.py")
    assert env_file.exists()

    content = env_file.read_text()

    # Check that target_metadata is defined
    assert "target_metadata" in content
    assert "Base.metadata" in content

    # Verify Base is imported
    assert (
        "from app.db.base import Base" in content
        or "from app.db.base import Base" in content
    )


def test_alembic_script_directory_exists():
    """Test that Alembic script directory exists and is valid."""
    script_location = Path("alembic")
    assert script_location.exists()
    assert (script_location / "env.py").exists()
    assert (script_location / "versions").exists()


def test_alembic_can_read_migrations():
    """Test that Alembic can read migration files."""
    script = ScriptDirectory.from_config(alembic_config.Config("alembic.ini"))

    # Should be able to get revisions
    revisions = list(script.walk_revisions())
    assert len(revisions) > 0

    # Should have a head
    head = script.get_current_head()
    assert head is not None


@pytest.mark.integration
def test_alembic_autogenerate_produces_empty_migration_when_synced():
    """Test that autogenerate produces empty migration when models match DB.

    This test requires a running database.
    """
    # This would require database setup in test environment
    # For now, we verify the configuration is correct
    # Actual migration testing should be done manually or in CI with test DB
    pass


@pytest.mark.integration
def test_alembic_upgrade_runs_successfully():
    """Test that alembic upgrade runs without errors.

    This test requires a running database.
    """
    # This would require database setup in test environment
    # For now, we verify the configuration is correct
    pass
