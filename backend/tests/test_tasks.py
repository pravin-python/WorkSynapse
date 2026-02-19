import pytest
from app.models.task.model import Task, TaskStatus

@pytest.mark.asyncio
async def test_task_model_creation(db_session, project_factory, regular_user):
    """Test creating a task model directly (Service/API missing)."""
    project = await project_factory(regular_user)
    task = Task(
        title="My Task",
        project_id=project.id,
        task_number="TASK-1",
        status=TaskStatus.TODO
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    assert task.id is not None
    assert task.title == "My Task"
    assert task.status == TaskStatus.TODO
    assert task.project_id == project.id
