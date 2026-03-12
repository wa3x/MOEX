from __future__ import annotations

from typing import Iterable

import pyqtgraph as pg
from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QBrush, QColor, QPainter, QPicture, QPen

from data.models import CandlePoint


class CandlestickItem(pg.GraphicsObject):
    """
    Кастомный элемент pyqtgraph для отрисовки свечного графика.

    Почему вынесено в отдельный класс:
    - логика рисования свечей не должна жить внутри окна или общего графика;
    - так проще отдельно менять внешний вид свечей;
    - при необходимости можно потом добавить объём, подсветку выбранной свечи,
      разные палитры и другие улучшения, не ломая остальной код.

    Как устроена отрисовка:
    - каждая свеча состоит из вертикальной линии (wick / тень),
      которая идёт от low до high;
    - и прямоугольного тела свечи, которое идёт от open до close;
    - если close >= open, свеча считается растущей;
    - если close < open, свеча считается падающей.
    """

    def __init__(self) -> None:
        """
        Инициализировать элемент свечного графика.

        Внутри хранится:
        - self.points: исходные точки;
        - self.picture: кэшированная картинка QPicture, чтобы не рисовать
          всё заново при каждом repaint без необходимости;
        - self.body_width: относительная ширина тела свечи по оси X.
        """
        super().__init__()

        self.points: list[CandlePoint] = []
        self.picture = QPicture()

        # Ширина тела свечи в условных X-координатах.
        # Поскольку свечи располагаются в индексах 0, 1, 2, ...,
        # ширина 0.6 обычно выглядит аккуратно и оставляет зазоры.
        self.body_width = 0.45

        # Цвета и перья вынесены в атрибуты, чтобы их было легко менять.
        self.rise_pen = QPen(QColor("#c9d1d9"))
        self.rise_pen.setWidthF(1.2)
        self.rise_pen.setCosmetic(True)
        self.rise_brush = QBrush(QColor("#7ee787"))

        self.fall_pen = QPen(QColor("#c9d1d9"))
        self.fall_pen.setWidthF(1.2)
        self.fall_pen.setCosmetic(True)
        self.fall_brush = QBrush(QColor("#ff7b72"))

        self.doji_pen = QPen(QColor("#c9d1d9"))
        self.doji_pen.setWidthF(1.2)
        self.doji_pen.setCosmetic(True)
        self.doji_brush = QBrush(QColor("#c9d1d9"))

    def set_points(self, points: Iterable[CandlePoint]) -> None:
        """
        Передать новые точки для отрисовки свечей.

        После получения новых точек:
        - сохраняем их во внутреннее состояние;
        - пересобираем QPicture;
        - сообщаем pyqtgraph, что геометрия элемента могла измениться;
        - инициируем перерисовку.

        Args:
            points:
                Итерируемый набор CandlePoint.
        """
        self.prepareGeometryChange()
        self.points = list(points)
        self.picture = self._build_picture()
        self.update()

    def _build_picture(self) -> QPicture:
        """
        Построить кэшированную картинку со всеми свечами.

        Зачем это нужно:
        - pyqtgraph и Qt могут довольно часто вызывать paint();
        - если каждый раз на лету проходиться по всем свечам,
          это будет менее эффективно;
        - QPicture позволяет один раз "записать" команды рисования,
          а потом быстро воспроизводить их.

        Returns:
            Готовый объект QPicture со свечами.
        """
        picture = QPicture()
        painter = QPainter(picture)

        half_width = self.body_width / 2.0

        for index, point in enumerate(self.points):
            open_price = point.open_price
            high_price = point.high_price
            low_price = point.low_price
            close_price = point.close_price

            # Выбор цветов по типу свечи.
            if close_price > open_price:
                wick_pen = self.rise_pen
                body_brush = self.rise_brush
            elif close_price < open_price:
                wick_pen = self.fall_pen
                body_brush = self.fall_brush
            else:
                wick_pen = self.doji_pen
                body_brush = self.doji_brush

            x = float(index)

            # 1. Сначала рисуем тело свечи без обводки.
            body_height = close_price - open_price

            if body_height == 0:
                # Для doji оставляем тонкую горизонтальную линию тела.
                painter.setPen(wick_pen)
                painter.drawLine(
                    QPointF(x - half_width, close_price),
                    QPointF(x + half_width, close_price),
                )
            else:
                painter.setPen(pg.mkPen(None))
                painter.setBrush(body_brush)

                rect = QRectF(
                    x - half_width,
                    open_price,
                    self.body_width,
                    body_height,
                )
                painter.drawRect(rect)

            # 2. Потом рисуем фитиль поверх тела,
            # чтобы он был виден даже в центральной части свечи.
            painter.setPen(wick_pen)
            painter.setBrush(pg.mkBrush(None))
            painter.drawLine(
                QPointF(x, low_price),
                QPointF(x, high_price),
            )

        painter.end()
        return picture

    def paint(self, painter: QPainter, *args) -> None:
        """
        Нарисовать уже подготовленную QPicture.

        Args:
            painter:
                QPainter, который предоставляет Qt.
            *args:
                Дополнительные аргументы Qt, здесь не используются.
        """
        painter.drawPicture(0, 0, self.picture)

    def boundingRect(self) -> QRectF:
        """
        Вернуть прямоугольник, в котором располагаются все свечи.

        Это нужно Qt для понимания области, которую занимает объект.

        Returns:
            QRectF с границами всех свечей.
            Если данных нет, возвращается маленький пустой прямоугольник.
        """
        if not self.points:
            return QRectF()

        min_x = -0.5
        max_x = len(self.points) - 0.5

        min_y = min(point.low_price for point in self.points)
        max_y = max(point.high_price for point in self.points)

        # Добавляем небольшой вертикальный отступ,
        # чтобы свечи не прилипали к границам области.
        padding = max((max_y - min_y) * 0.02, 0.5)

        return QRectF(
            min_x,
            min_y - padding,
            (max_x - min_x) + 1.0,
            (max_y - min_y) + padding * 2,
        )