from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class CandlePoint:
    """
    Одна точка графика, построенная на основе свечи MOEX.

    Attributes:
        dt:
            Дата и время начала свечи.
        label:
            Подпись для оси X, подготовленная под текущий таймфрейм.
        open_price:
            Цена открытия свечи.
        high_price:
            Максимальная цена свечи.
        low_price:
            Минимальная цена свечи.
        close_price:
            Цена закрытия свечи.
    """

    dt: datetime
    label: str
    open_price: float
    high_price: float
    low_price: float
    close_price: float


@dataclass(frozen=True)
class CandleInterval:
    """
    Настройка таймфрейма свечи.

    Attributes:
        code:
            Короткий код таймфрейма, например 10M, 1H, 1D.
        title:
            Человекочитаемое название таймфрейма.
        moex_interval:
            Значение interval для MOEX ISS API.
        label_format:
            Формат подписей по оси X для этого таймфрейма.
    """

    code: str
    title: str
    moex_interval: int
    label_format: str


@dataclass(frozen=True)
class LookbackPeriod:
    """
    Настройка глубины просмотра истории.

    Attributes:
        code:
            Короткий код периода, например 48H, 30D, 6M.
        title:
            Человекочитаемое название периода.
        delta:
            Интервал времени назад от текущего момента.
    """

    code: str
    title: str
    delta: timedelta