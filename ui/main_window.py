from __future__ import annotations

from datetime import datetime

import requests
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListView,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from charts.price_chart import PriceChart
from config import WINDOW_HEIGHT, WINDOW_WIDTH
from data.moex_client import MoexClient
from data.period_service import (
    INTERVALS,
    get_default_lookback,
    get_interval,
    get_lookback,
    get_lookback_options,
)
from services.analytics import calc_change, get_last_price
from ui.styles import (
    BUTTON_STYLE,
    CARD_STYLE,
    CLOSE_BUTTON_STYLE,
    COMBO_POPUP_STYLE,
    COMBO_STYLE,
    TEXT_CHANGE_NEGATIVE,
    TEXT_CHANGE_POSITIVE,
    TEXT_MUTED,
    TEXT_PRICE,
    TEXT_PRIMARY,
)


class HeaderValue(QLabel):
    """
    Удобный QLabel для шапки виджета.

    Используется для крупной цены, заголовка тикера и второстепенного текста.
    """

    def __init__(self, text: str, size: int, bold: bool = False) -> None:
        """
        Создать текстовый элемент с нужным размером шрифта.

        Args:
            text:
                Начальный текст.
            size:
                Размер шрифта.
            bold:
                Делать ли текст жирным.
        """
        super().__init__(text)

        font = QFont()
        font.setPointSize(size)
        font.setBold(bold)
        self.setFont(font)
        self.setStyleSheet(TEXT_PRIMARY)


class MoexTickerWindow(QWidget):
    """
    Главное окно мини-виджета MOEX.

    Отвечает за:
    - сборку интерфейса;
    - выбор периода;
    - запрос данных через MoexClient;
    - передачу данных на график;
    - отображение цены, изменения и статуса.

    Сеть, аналитика и график вынесены в отдельные модули,
    поэтому здесь осталась только orchestration-логика.
    """

    def __init__(self, ticker: str, update_ms: int) -> None:
        """
        Инициализировать окно виджета.

        Args:
            ticker:
                Тикер Московской биржи, например TATN.
            update_ms:
                Интервал автообновления в миллисекундах.
        """
        super().__init__()

        self.ticker = ticker.upper()
        self.update_ms = update_ms
        self.client = MoexClient()
        self.drag_pos = None
        self.current_interval = get_interval("1H")
        self.current_lookback = get_default_lookback("1H")

        self._setup_window()
        self._build_ui()
        self._setup_timer()

        self.refresh_data()

    def _setup_window(self) -> None:
        """
        Настроить поведение и внешний вид окна.

        Окно делается:
        - без рамки;
        - поверх остальных;
        - с прозрачным фоном;
        - фиксированного размера.
        """
        self.setWindowTitle(f"{self.ticker} MOEX Widget")
        self.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

    def _build_ui(self) -> None:
        """
        Собрать интерфейс главного окна.

        Интерфейс состоит из:
        - карточки;
        - строки с тикером и ценой;
        - строки управления периодом;
        - графика;
        - hover-строки для точки под курсором;
        - нижней строки статуса и кнопок.
        """
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(10, 10, 10, 10)

        self.card = QFrame()
        self.card.setStyleSheet(CARD_STYLE)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(14, 12, 14, 12)
        card_layout.setSpacing(8)

        top_row = QHBoxLayout()

        left_col = QVBoxLayout()
        self.ticker_label = HeaderValue(f"{self.ticker} · MOEX", 13, bold=True)
        self.time_label = HeaderValue("Обновление: —", 9, bold=False)
        self.time_label.setStyleSheet(TEXT_MUTED)

        left_col.addWidget(self.ticker_label)
        left_col.addWidget(self.time_label)

        right_col = QVBoxLayout()
        self.price_label = HeaderValue("—", 20, bold=True)
        self.change_label = HeaderValue("—", 11, bold=True)
        self.price_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.change_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.price_label.setStyleSheet(TEXT_PRICE)
        self.change_label.setStyleSheet(TEXT_MUTED)

        right_col.addWidget(self.price_label)
        right_col.addWidget(self.change_label)

        top_row.addLayout(left_col, 1)
        top_row.addLayout(right_col)

        controls_row = QHBoxLayout()

        self.interval_combo = QComboBox()
        self.interval_combo.setStyleSheet(COMBO_STYLE)
        self._configure_combo_popup_view(self.interval_combo)

        for code, interval in INTERVALS.items():
            self.interval_combo.addItem(code, code)

        self.interval_combo.setCurrentText("1H")
        self.interval_combo.currentIndexChanged.connect(self.on_interval_changed)

        self.lookback_combo = QComboBox()
        self.lookback_combo.setStyleSheet(COMBO_STYLE)
        self._configure_combo_popup_view(self.lookback_combo)
        self.lookback_combo.currentIndexChanged.connect(self.on_lookback_changed)

        self._reload_lookback_combo()

        self.period_info_label = QLabel(
            f"{self.current_interval.title} · {self.current_lookback.title}"
        )
        self.period_info_label.setStyleSheet(TEXT_MUTED)

        controls_row.addWidget(self.interval_combo)
        controls_row.addWidget(self.lookback_combo)
        controls_row.addWidget(self.period_info_label)
        controls_row.addStretch()

        self.hover_label = QLabel("Наведи мышь на график")
        self.hover_label.setStyleSheet(TEXT_MUTED)

        self.chart = PriceChart(self.hover_label)

        bottom_row = QHBoxLayout()

        self.status_label = QLabel("Загрузка…")
        self.status_label.setStyleSheet(TEXT_MUTED)

        self.refresh_btn = QPushButton("Обновить")
        self.refresh_btn.setStyleSheet(BUTTON_STYLE)
        self.refresh_btn.clicked.connect(self.refresh_data)

        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedWidth(36)
        self.close_btn.setStyleSheet(CLOSE_BUTTON_STYLE)
        self.close_btn.clicked.connect(self.quit_application)

        bottom_row.addWidget(self.status_label, 1)
        bottom_row.addWidget(self.refresh_btn)
        bottom_row.addWidget(self.close_btn)

        card_layout.addLayout(top_row)
        card_layout.addLayout(controls_row)
        card_layout.addWidget(self.chart, 1)
        card_layout.addWidget(self.hover_label)
        card_layout.addLayout(bottom_row)

        outer_layout.addWidget(self.card)

    def _setup_timer(self) -> None:
        """
        Настроить таймер периодического обновления данных.
        """
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_data)
        self.timer.start(self.update_ms)

    def _configure_combo_popup_view(self, combo: QComboBox) -> None:
        """
        Назначить QComboBox собственный QListView без рамки и лишних отступов.

        Args:
            combo:
                Экземпляр QComboBox, которому нужно назначить popup-view.
        """
        view = QListView(combo)
        view.setStyleSheet(COMBO_POPUP_STYLE)
        view.setFrameShape(QFrame.Shape.NoFrame)
        view.setSpacing(0)
        view.setUniformItemSizes(True)
        view.setContentsMargins(0, 0, 0, 0)

        if view.viewport() is not None:
            view.viewport().setContentsMargins(0, 0, 0, 0)
            view.viewport().setAutoFillBackground(False)

        combo.setView(view)

    def _reload_lookback_combo(self) -> None:
        """
        Пересобрать список доступных lookback-периодов
        для текущего выбранного таймфрейма.

        Логика:
        - очищаем combo;
        - загружаем допустимые варианты для текущего interval;
        - выбираем либо текущий lookback, если он допустим,
          либо default для этого interval.
        """
        self.lookback_combo.blockSignals(True)
        self.lookback_combo.clear()

        options = get_lookback_options(self.current_interval.code)

        for option in options:
            self.lookback_combo.addItem(option.code, option.code)

        allowed_codes = {option.code for option in options}

        if self.current_lookback.code not in allowed_codes:
            self.current_lookback = get_default_lookback(self.current_interval.code)

        self.lookback_combo.setCurrentText(self.current_lookback.code)
        self.lookback_combo.blockSignals(False)

    def on_interval_changed(self) -> None:
        """
        Обработать смену таймфрейма свечи.

        После смены:
        - обновляется текущий interval;
        - под него пересобирается список lookback;
        - при необходимости выбирается новый lookback по умолчанию;
        - сбрасывается zoom графика;
        - запускается загрузка данных.
        """
        interval_code = self.interval_combo.currentData()
        self.current_interval = get_interval(interval_code)
        self.current_lookback = get_default_lookback(self.current_interval.code)

        self._reload_lookback_combo()

        self.period_info_label.setText(
            f"{self.current_interval.title} · {self.current_lookback.title}"
        )

        self.chart.reset_view()
        self.refresh_data()

    def on_lookback_changed(self) -> None:
        """
        Обработать смену глубины просмотра.

        После смены:
        - обновляется текущий lookback;
        - сбрасывается zoom графика;
        - запускается новая загрузка данных.
        """
        lookback_code = self.lookback_combo.currentData()
        self.current_lookback = get_lookback(self.current_interval.code, lookback_code)

        self.period_info_label.setText(
            f"{self.current_interval.title} · {self.current_lookback.title}"
        )

        self.chart.reset_view()
        self.refresh_data()

    def refresh_data(self) -> None:
        """
        Загрузить свежие данные, применить аналитику и обновить интерфейс.

        Порядок:
        1. Загружаем свечи через MoexClient.
        2. Дофильтровываем точки под выбранный период.
        3. Считаем последнюю цену и изменение.
        4. Обновляем график и подписи.

        Ошибки не валят приложение, а выводятся в строке статуса.
        """
        try:
            points = self.client.fetch_prices(
                self.ticker,
                self.current_interval,
                self.current_lookback,
            )

            if not points:
                self.status_label.setText("Нет данных для выбранного периода")
                self.price_label.setText("—")
                self.change_label.setText("—")
                self.change_label.setStyleSheet(TEXT_MUTED)
                self.hover_label.setText("Наведи мышь на график")
                self.period_info_label.setText(
                    f"{self.current_interval.title} · {self.current_lookback.title}"
                )
                self.chart.set_points([], "#7cc6ff", force_reset_view=True)
                return

            period_last_price = get_last_price(points)
            actual_price = self.client.fetch_current_price(self.ticker)
            diff, diff_pct = calc_change(points)

            display_price = actual_price if actual_price is not None else period_last_price
            self.price_label.setText(f"{display_price:.2f} ₽")

            sign = "+" if diff >= 0 else ""
            self.change_label.setText(f"{sign}{diff:.2f} ₽  ({sign}{diff_pct:.2f}%)")

            if diff >= 0:
                color = "#7ee787"
                self.change_label.setStyleSheet(TEXT_CHANGE_POSITIVE)
            else:
                color = "#ff7b72"
                self.change_label.setStyleSheet(TEXT_CHANGE_NEGATIVE)

            self.chart.set_points(points, color, force_reset_view=False)

            now_str = datetime.now().strftime("%H:%M:%S")
            self.time_label.setText(f"Обновлено: {now_str}")
            self.period_info_label.setText(
                f"{self.current_interval.title} · {self.current_lookback.title}"
            )
            self.status_label.setText("Данные получены с MOEX")
        except requests.RequestException as exc:
            self.status_label.setText(f"Сетевая ошибка: {exc}")
        except Exception as exc:
            self.status_label.setText(f"Ошибка: {exc}")

    def quit_application(self) -> None:
        """
        Полностью завершить приложение по кнопке закрытия.

        Почему это нужно:
        - обычный self.close() закрывает окно, но не всегда гарантирует
          завершение процесса Qt;
        - у нас есть активный QTimer, и в некоторых сценариях процесс может
          оставаться жить в памяти;
        - явный вызов QApplication.instance().quit() надёжнее завершает app loop.
        """
        app = QApplication.instance()

        if hasattr(self, "timer") and self.timer.isActive():
            self.timer.stop()

        self.close()

        if app is not None:
            app.quit()

    def mousePressEvent(self, event) -> None:
        """
        Начать перетаскивание окна мышью.

        Args:
            event:
                Событие мыши Qt.
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event) -> None:
        """
        Перетаскивать окно мышью.

        Args:
            event:
                Событие мыши Qt.
        """
        if self.drag_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event) -> None:
        """
        Завершить перетаскивание окна.

        Args:
            event:
                Событие мыши Qt.
        """
        self.drag_pos = None
        event.accept()

    def closeEvent(self, event) -> None:
        """
        Обработать закрытие окна.

        Здесь явно останавливаем таймер, чтобы не оставалось фоновой активности,
        и принимаем событие закрытия.

        Args:
            event:
                Событие закрытия Qt.
        """
        if hasattr(self, "timer") and self.timer.isActive():
            self.timer.stop()

        event.accept()