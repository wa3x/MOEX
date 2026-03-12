#!/usr/bin/env python3
"""
Точка входа в мини-виджет MOEX.

Запускает окно с графиком акции.
Все настройки берутся из config.py.
"""

from __future__ import annotations

import sys
sys.stdout = sys.stderr = open("/tmp/moex_widget.log", "a")
from PyQt6.QtWidgets import QApplication

from config import APP_NAME, DEFAULT_TICKER, UPDATE_INTERVAL_MS
from ui.main_window import MoexTickerWindow


def main() -> int:
    """
    Точка входа приложения.

    Returns:
        Код завершения Qt-приложения.
    """
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setQuitOnLastWindowClosed(True)

    window = MoexTickerWindow(
        ticker=DEFAULT_TICKER,
        update_ms=UPDATE_INTERVAL_MS,
    )
    window.show()

    exit_code = app.exec()
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())