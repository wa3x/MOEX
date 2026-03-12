from __future__ import annotations

from datetime import timedelta

from data.models import CandleInterval, LookbackPeriod


INTERVALS: dict[str, CandleInterval] = {
    "10M": CandleInterval(
        code="10M",
        title="Свечи 10 минут",
        moex_interval=10,
        label_format="%d.%m %H:%M",
    ),
    "1H": CandleInterval(
        code="1H",
        title="Свечи 1 час",
        moex_interval=60,
        label_format="%d.%m %H:%M",
    ),
    "1D": CandleInterval(
        code="1D",
        title="Свечи 1 день",
        moex_interval=24,
        label_format="%d.%m.%y",
    ),
}


LOOKBACK_OPTIONS: dict[str, list[LookbackPeriod]] = {
    "10M": [
        LookbackPeriod(code="48H", title="Последние 48 часов", delta=timedelta(hours=48)),
        LookbackPeriod(code="24H", title="Последние 24 часа", delta=timedelta(hours=24)),
        LookbackPeriod(code="12H", title="Последние 12 часов", delta=timedelta(hours=12)),
        LookbackPeriod(code="6H", title="Последние 6 часов", delta=timedelta(hours=6)),
        LookbackPeriod(code="3H", title="Последние 3 часа", delta=timedelta(hours=3)),
    ],
    "1H": [
        LookbackPeriod(code="7D", title="Последние 7 дней", delta=timedelta(days=7)),
        LookbackPeriod(code="5D", title="Последние 5 дней", delta=timedelta(days=5)),
        LookbackPeriod(code="3D", title="Последние 3 дня", delta=timedelta(days=3)),
        LookbackPeriod(code="2D", title="Последние 2 дня", delta=timedelta(days=2)),
        LookbackPeriod(code="1D", title="Последние 1 сутки", delta=timedelta(days=1)),
    ],
    "1D": [
        LookbackPeriod(code="120D", title="Последние 120 дней", delta=timedelta(days=120)),
        LookbackPeriod(code="60D", title="Последние 60 дней", delta=timedelta(days=60)),
        LookbackPeriod(code="30D", title="Последние 30 дней", delta=timedelta(days=30)),
        LookbackPeriod(code="15D", title="Последние 15 дней", delta=timedelta(days=15)),
        LookbackPeriod(code="5D", title="Последние 5 дней", delta=timedelta(days=5)),
        LookbackPeriod(code="3D", title="Последние 3 дня", delta=timedelta(days=3)),
    ],
}


DEFAULT_LOOKBACK_BY_INTERVAL: dict[str, str] = {
    "10M": "24H",
    "1H": "3D",
    "1D": "30D",
}


def get_interval(interval_code: str) -> CandleInterval:
    """
    Вернуть конфигурацию таймфрейма по коду.

    Args:
        interval_code:
            Код таймфрейма, например 10M, 1H, 1D.

    Returns:
        CandleInterval.
        Если код неизвестен, возвращается 1H.
    """
    return INTERVALS.get(interval_code, INTERVALS["1H"])


def get_lookback_options(interval_code: str) -> list[LookbackPeriod]:
    """
    Вернуть список допустимых глубин просмотра для выбранного таймфрейма.

    Args:
        interval_code:
            Код таймфрейма.

    Returns:
        Список LookbackPeriod.
    """
    return LOOKBACK_OPTIONS.get(interval_code, LOOKBACK_OPTIONS["1H"])


def get_default_lookback(interval_code: str) -> LookbackPeriod:
    """
    Вернуть lookback по умолчанию для выбранного таймфрейма.

    Args:
        interval_code:
            Код таймфрейма.

    Returns:
        LookbackPeriod по умолчанию.
    """
    options = get_lookback_options(interval_code)
    default_code = DEFAULT_LOOKBACK_BY_INTERVAL.get(interval_code)

    for option in options:
        if option.code == default_code:
            return option

    return options[0]


def get_lookback(interval_code: str, lookback_code: str) -> LookbackPeriod:
    """
    Вернуть lookback по коду в рамках выбранного таймфрейма.

    Args:
        interval_code:
            Код таймфрейма.
        lookback_code:
            Код lookback-периода.

    Returns:
        LookbackPeriod.
        Если код не найден, возвращается default для текущего таймфрейма.
    """
    options = get_lookback_options(interval_code)

    for option in options:
        if option.code == lookback_code:
            return option

    return get_default_lookback(interval_code)