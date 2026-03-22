"""Экспоненциальная задержка между повторными попытками воркера."""


def exponential_backoff_seconds(base_seconds: float, failed_attempt_index: int) -> float:
    """
    failed_attempt_index: номер неудачной попытки с нуля (после 1-й ошибки = 0, после 2-й = 1, ...).
    Задержка перед следующей попыткой: base * 2^index.
    """
    return base_seconds * (2**failed_attempt_index)
