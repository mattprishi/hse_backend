class PredictionError(Exception):
    pass


class AdNotFoundError(Exception):
    pass


class ModerationTaskNotFoundError(Exception):
    def __init__(self, task_id: int):
        self.task_id = task_id


class ModerationEnqueueFailedError(Exception):
    """Не удалось отправить задачу в Kafka после создания записи в БД."""
    pass
