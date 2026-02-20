import pytest
import pytest_asyncio
from app.models.project.model import Project, ProjectStatus, ProjectVisibility, Board, BoardColumn
from app.models.task.model import Task, TaskStatus, TaskPriority
from faker import Faker
import random

fake = Faker()

@pytest_asyncio.fixture
async def project_factory(db_session):
    async def create_project(owner, **kwargs):
        project = Project(
            name=kwargs.get("name", fake.company()),
            description=kwargs.get("description", fake.text()),
            key=kwargs.get("key", fake.lexify(text="????").upper()),
            owner_id=owner.id,
            status=kwargs.get("status", ProjectStatus.ACTIVE),
            visibility=kwargs.get("visibility", ProjectVisibility.PRIVATE),
            task_counter=kwargs.get("task_counter", 0),
            **kwargs
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)
        return project
    return create_project

@pytest_asyncio.fixture
async def board_factory(db_session):
    async def create_board(project, **kwargs):
        board = Board(
            name=kwargs.get("name", "Default Board"),
            project_id=project.id,
            **kwargs
        )
        db_session.add(board)
        await db_session.commit()
        await db_session.refresh(board)

        # Add default columns
        columns = ["To Do", "In Progress", "Done"]
        for i, col_name in enumerate(columns):
            col = BoardColumn(
                name=col_name,
                board_id=board.id,
                position=i
            )
            db_session.add(col)

        await db_session.commit()
        return board
    return create_board

@pytest_asyncio.fixture
async def task_factory(db_session):
    async def create_task(project, author, **kwargs):
        # Determine status and priority
        status = kwargs.pop("status", TaskStatus.TODO)
        priority = kwargs.pop("priority", TaskPriority.MEDIUM)

        # Generate task number
        task_number = kwargs.pop("task_number", f"{project.key}-{random.randint(1, 1000)}")

        task = Task(
            title=kwargs.get("title", fake.sentence()),
            description=kwargs.get("description", fake.text()),
            project_id=project.id,
            reporter_id=author.id,
            task_number=task_number,
            status=status,
            priority=priority,
            assignee_id=kwargs.get("assignee_id"),
            **kwargs
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)
        return task
    return create_task
