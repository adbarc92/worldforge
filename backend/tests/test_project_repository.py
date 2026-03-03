"""Tests for ProjectRepository."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.database import Project
from app.models.project_repository import ProjectRepository


@pytest.fixture
def mock_session():
    return AsyncMock()


@pytest.fixture
def repo(mock_session):
    return ProjectRepository(mock_session)


@pytest.mark.asyncio
async def test_create_project(repo, mock_session):
    project = await repo.create(name="My World", description="A fantasy world")
    mock_session.add.assert_called_once()
    added = mock_session.add.call_args[0][0]
    assert isinstance(added, Project)
    assert added.name == "My World"
    assert added.description == "A fantasy world"
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_list_projects(repo, mock_session):
    p1 = Project(id="id-1", name="World A")
    p2 = Project(id="id-2", name="World B")
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [p1, p2]
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute.return_value = mock_result
    projects = await repo.list()
    assert len(projects) == 2
    assert projects[0].name == "World A"


@pytest.mark.asyncio
async def test_get_project(repo, mock_session):
    p = Project(id="id-1", name="World A")
    mock_scalars = MagicMock()
    mock_scalars.first.return_value = p
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute.return_value = mock_result
    result = await repo.get("id-1")
    assert result is not None
    assert result.name == "World A"


@pytest.mark.asyncio
async def test_update_project(repo, mock_session):
    p = Project(id="id-1", name="Old Name", description="Old desc")
    mock_scalars = MagicMock()
    mock_scalars.first.return_value = p
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute.return_value = mock_result
    updated = await repo.update("id-1", name="New Name")
    assert updated.name == "New Name"
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_project(repo, mock_session):
    p = Project(id="id-1", name="World A")
    mock_scalars = MagicMock()
    mock_scalars.first.return_value = p
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute.return_value = mock_result
    result = await repo.delete("id-1")
    assert result is True
    mock_session.delete.assert_awaited_once_with(p)
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_project_not_found(repo, mock_session):
    mock_scalars = MagicMock()
    mock_scalars.first.return_value = None
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute.return_value = mock_result
    result = await repo.delete("nonexistent")
    assert result is False


@pytest.mark.asyncio
async def test_get_document_count(repo, mock_session):
    mock_scalars = MagicMock()
    mock_scalars.one.return_value = 5
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute.return_value = mock_result
    count = await repo.get_document_count("id-1")
    assert count == 5
