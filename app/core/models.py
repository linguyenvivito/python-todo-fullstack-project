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
    user_id: Optional[int] = None


@dataclass
class User:
    id: int
    username: str
    password_hash: str

@dataclass
class Role:
    id: int
    name: str

@dataclass
class AuditLog:
    id: int
    occurred_at: int
    actor_user_id: Optional[int]
    action: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    success: bool
    http_method: Optional[str]
    path: Optional[str]
    status_code: Optional[int]
    client_ip: Optional[str]
    user_agent: Optional[str]
    request_id: Optional[str]
    details_json: Optional[str]
