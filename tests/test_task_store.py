"""Tests for task store."""

import pytest

from src.models import AgentRole, CrewMode, TaskRequest, TaskStatus
from src.tasks.store import InMemoryTaskStore


@pytest.fixture
def store():
    return InMemoryTaskStore()


@pytest.fixture
def sample_request():
    return TaskRequest(
        topic="AI trends in 2026",
        crew_mode=CrewMode.SEQUENTIAL,
        agents=[AgentRole.RESEARCHER, AgentRole.ANALYST, AgentRole.WRITER, AgentRole.CRITIC],
    )


async def test_create_task(store, sample_request):
    response = await store.create_task(sample_request)
    assert response.task_id
    assert response.status == TaskStatus.PENDING
    assert response.topic == "AI trends in 2026"


async def test_get_task(store, sample_request):
    response = await store.create_task(sample_request)
    task = await store.get_task(response.task_id)
    assert task is not None
    assert task.task_id == response.task_id
    assert task.topic == "AI trends in 2026"


async def test_get_nonexistent_task(store):
    task = await store.get_task("nonexistent")
    assert task is None


async def test_list_tasks(store, sample_request):
    await store.create_task(sample_request)
    await store.create_task(sample_request)
    tasks = await store.list_tasks()
    assert len(tasks) == 2


async def test_update_task(store, sample_request):
    response = await store.create_task(sample_request)
    await store.update_task(
        response.task_id,
        TaskStatus.COMPLETED,
        result="Done",
        agent_outputs={"researcher": "Research findings"},
        iterations=4,
        latency_ms=1500.0,
    )
    task = await store.get_task(response.task_id)
    assert task is not None
    assert task.status == TaskStatus.COMPLETED
    assert task.result == "Done"
    assert task.agent_outputs == {"researcher": "Research findings"}
    assert task.completed_at is not None


async def test_delete_task(store, sample_request):
    response = await store.create_task(sample_request)
    deleted = await store.delete_task(response.task_id)
    assert deleted is True
    task = await store.get_task(response.task_id)
    assert task is None


async def test_delete_nonexistent(store):
    deleted = await store.delete_task("nonexistent")
    assert deleted is False


async def test_task_with_context(store):
    request = TaskRequest(
        topic="Cloud migration",
        context="Focus on AWS to Azure migration strategies",
    )
    response = await store.create_task(request)
    assert response.task_id
