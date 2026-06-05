class TaskNotFoundError(Exception):
    def __init__(self, task_id: int):
        super().__init__("Task with id {0} was not found".format(task_id))
        self.task_id = task_id


class TaskNotFoundByNameError(Exception):
    def __init__(self, task_name: str):
        super().__init__("Task with name '{0}' was not found".format(task_name))
        self.task_name = task_name


class InvalidTaskSearchError(Exception):
    def __init__(self):
        super().__init__("Task search term must not be empty")


class RoleNotFoundError(Exception):
    def __init__(self, role_id: int):
        super().__init__("Role with id {0} was not found".format(role_id))
        self.role_id = role_id
