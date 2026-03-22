import pytest

from workers.retry_utils import exponential_backoff_seconds


@pytest.mark.parametrize(
    "base,index,expected",
    [
        (1.0, 0, 1.0),
        (1.0, 1, 2.0),
        (1.0, 2, 4.0),
        (1.0, 3, 8.0),
        (0.5, 0, 0.5),
        (0.5, 2, 2.0),
    ],
)
def test_exponential_backoff_seconds(base: float, index: int, expected: float):
    assert exponential_backoff_seconds(base, index) == expected
