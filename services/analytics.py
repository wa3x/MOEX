from __future__ import annotations

from data.models import CandlePoint


def calc_change(points: list[CandlePoint]) -> tuple[float, float]:
    """
    Посчитать абсолютное и процентное изменение цены на диапазоне.

    Логика:
    - берётся close первой точки;
    - берётся close последней точки;
    - считается абсолютная разница и разница в процентах.

    Args:
        points:
            Список точек графика.

    Returns:
        Кортеж:
            (
                абсолютное изменение,
                изменение в процентах
            )
    """
    if len(points) < 2:
        return 0.0, 0.0

    first_price = points[0].close_price
    last_price = points[-1].close_price

    diff = last_price - first_price
    diff_pct = (diff / first_price * 100.0) if first_price else 0.0

    return diff, diff_pct


def get_last_price(points: list[CandlePoint]) -> float:
    """
    Вернуть последнюю цену в выборке.

    Args:
        points:
            Список точек графика.

    Returns:
        Последняя цена close.
        Если точек нет, возвращается 0.0.
    """
    if not points:
        return 0.0

    return points[-1].close_price