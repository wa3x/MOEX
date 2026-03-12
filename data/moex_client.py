from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

import requests

from data.models import CandleInterval, CandlePoint, LookbackPeriod


class MoexClient:
    """
    Клиент для работы с MOEX ISS API.

    Используется endpoint вида:
        /iss/engines/stock/markets/shares/securities/{ticker}/candles.json

    Клиент отделён от UI, чтобы:
    - было проще менять реализацию API;
    - можно было писать тесты;
    - не смешивать сеть и интерфейс в одном файле.
    """

    # BASE_URL = (
    #     "https://iss.moex.com/iss/engines/stock/markets/shares/"
    #     "securities/{ticker}/candles.json"
    # )
    BASE_URL = (
        "https://iss.moex.com/iss/engines/stock/markets/shares/"
        "boards/TQBR/securities/{ticker}/candles.json"
    )
    def __init__(self, session: Optional[requests.Session] = None) -> None:
        """
        Инициализировать HTTP-клиент.

        Args:
            session:
                Готовая requests.Session.
                Можно передать свою в тестах или для переиспользования соединений.
        """
        self.session = session or requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "MOEX-KDE-Widget/2.0",
                "Accept": "application/json",
            }
        )

    def fetch_prices(
        self,
        ticker: str,
        interval: CandleInterval,
        lookback: LookbackPeriod,
    ) -> list[CandlePoint]:
        """
        Загрузить свечи по тикеру за выбранные таймфрейм и глубину просмотра.

        Args:
            ticker:
                Биржевой тикер, например TATN.
            interval:
                Конфигурация таймфрейма свечи.
            lookback:
                Конфигурация глубины просмотра истории.

        Returns:
            Список CandlePoint в порядке времени.

        Raises:
            requests.RequestException:
                При сетевой ошибке.
            ValueError:
                Если в ответе MOEX нет ожидаемых полей.
        """
        url = self.BASE_URL.format(ticker=ticker.upper())

        now_dt = datetime.now()
        from_dt = now_dt - lookback.delta

        date_from = from_dt.strftime("%Y-%m-%d")
        date_till = now_dt.strftime("%Y-%m-%d")

        params = {
            "interval": interval.moex_interval,
            "from": date_from,
            "till": date_till,
            "iss.meta": "off",
            "iss.only": "candles",
            "candles.columns": "begin,open,high,low,close",
        }

        response = self.session.get(url, params=params, timeout=15)
        response.raise_for_status()

        payload = response.json()

        candles = payload.get("candles", {})
        columns = candles.get("columns", [])
        data = candles.get("data", [])

        if not columns:
            raise ValueError("MOEX не вернул columns для candles")

        if not data:
            return []

        required_fields = ["begin", "open", "high", "low", "close"]
        missing_fields = [field for field in required_fields if field not in columns]
        if missing_fields:
            raise ValueError(f"В ответе MOEX отсутствуют поля: {', '.join(missing_fields)}")

        begin_idx = columns.index("begin")
        open_idx = columns.index("open")
        high_idx = columns.index("high")
        low_idx = columns.index("low")
        close_idx = columns.index("close")

        result: list[CandlePoint] = []

        for row in data:
            begin_raw = row[begin_idx]
            open_raw = row[open_idx]
            high_raw = row[high_idx]
            low_raw = row[low_idx]
            close_raw = row[close_idx]

            if None in (begin_raw, open_raw, high_raw, low_raw, close_raw):
                continue

            try:
                dt = datetime.fromisoformat(begin_raw)

                # Дополнительная точная фильтрация уже после ответа API.
                # Нужна потому, что параметры from/till у MOEX задаются по датам,
                # а не по точному времени внутри суток.
                if dt < from_dt:
                    continue

                point = CandlePoint(
                    dt=dt,
                    label=dt.strftime(interval.label_format),
                    open_price=float(open_raw),
                    high_price=float(high_raw),
                    low_price=float(low_raw),
                    close_price=float(close_raw),
                )
                result.append(point)
            except Exception:
                continue

        return result


    def fetch_current_price(self, ticker: str) -> float | None:
        """
        Получить актуальную цену бумаги с MOEX marketdata.

        Логика:
        - сначала пробуем поле LAST как наиболее ожидаемое "текущее значение";
        - если LAST пустой, пробуем запасные поля;
        - если ничего подходящего нет, возвращаем None.

        Args:
            ticker:
                Биржевой тикер, например TATN.

        Returns:
            Актуальная цена как float, либо None, если цена не найдена.
        """
        url = (
            "https://iss.moex.com/iss/engines/stock/markets/shares/"
            f"boards/TQBR/securities/{ticker.upper()}.json"
        )

        params = {
            "iss.meta": "off",
            "iss.only": "marketdata",
        }

        response = self.session.get(url, params=params, timeout=10)
        response.raise_for_status()

        payload = response.json()
        marketdata = payload.get("marketdata", {})
        columns = marketdata.get("columns", [])
        data = marketdata.get("data", [])

        if not columns or not data:
            return None

        row = data[0]

        candidate_fields = [
            "LAST",
            "MARKETPRICE",
            "LCLOSEPRICE",
            "LEGALCLOSEPRICE",
        ]

        for field_name in candidate_fields:
            if field_name not in columns:
                continue

            value = row[columns.index(field_name)]
            if value is None:
                continue

            try:
                return float(value)
            except (TypeError, ValueError):
                continue

        return None