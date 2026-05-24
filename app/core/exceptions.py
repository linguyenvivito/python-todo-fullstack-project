class TaskNotFoundError(Exception):
    def __init__(self, task_id: int):
        super().__init__("Task with id {0} was not found".format(task_id))
        self.task_id = task_id
