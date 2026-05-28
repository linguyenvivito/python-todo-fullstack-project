from dataclasses import dataclass
from enum import Enum
from typing import Optional


class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    ARCHIVED = "archived"


@dataclass
class Task:
    id: int
    title: str
    description: Optional[str]
    status: TaskStatus
