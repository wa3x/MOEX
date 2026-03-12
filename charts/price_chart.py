from __future__ import annotations

import pyqtgraph as pg
from PyQt6.QtCore import QPointF, Qt

from charts.candlestick_item import CandlestickItem
from charts.crosshair import ChartCrosshair
from data.models import CandlePoint

class PriceChart(pg.PlotWidget):
    """
    Компонент графика цены со свечной отрисовкой.

    Возможности:
    - отображение свечного графика;
    - редкие подписи по оси X;
    - hover мышью;
    - показ времени и O/H/L/C для ближайшей свечи;
    - кроссхейр по позиции мыши;
    - масштабирование колесом мыши;
    - zoom вокруг курсора, а не вокруг центра;
    - горизонтальный drag мышью;
    - двойной клик для сброса масштаба;
    - сохранение пользовательского масштаба между обновлениями данных.
    """

    def __init__(self, hover_label) -> None:
        """
        Инициализировать график.

        Args:
            hover_label:
                QLabel или совместимый объект, в который будет выводиться
                информация о свече под курсором.
        """
        super().__init__()

        self.hover_label = hover_label
        self.points: list[CandlePoint] = []

        # Флаг, показывающий, что пользователь уже вручную менял масштаб
        # или двигал график, поэтому автоподгонка диапазона больше не должна
        # срабатывать на каждом обновлении данных.
        self.user_has_custom_view = False

        self._setup_chart()

        self.candles_item = CandlestickItem()
        self.addItem(self.candles_item)

        self.crosshair = ChartCrosshair(self)

        self.scene().sigMouseMoved.connect(self.on_mouse_moved)
        self.getViewBox().sigXRangeChanged.connect(self._on_x_range_changed)

    def _setup_chart(self) -> None:
        """
        Базовая настройка внешнего вида графика.

        Здесь настраиваем:
        - прозрачный фон;
        - сетку;
        - отключение стандартных кнопок pyqtgraph;
        - стили осей;
        - горизонтальный drag мышью;
        - режим Pan для ViewBox.
        """
        self.setBackground((0, 0, 0, 0))
        self.showGrid(x=False, y=True, alpha=0.2)
        self.setMenuEnabled(False)
        self.hideButtons()

        self.getViewBox().setMouseMode(pg.ViewBox.PanMode)

        # Разрешаем горизонтальное перемещение графика мышью.
        self.setMouseEnabled(x=True, y=False)

        self.getAxis("left").setTextPen(pg.mkPen("#a9b0bb"))
        self.getAxis("bottom").setTextPen(pg.mkPen("#a9b0bb"))
        self.getAxis("left").setPen(pg.mkPen("#4e5561"))
        self.getAxis("bottom").setPen(pg.mkPen("#4e5561"))
        # Для внутридневных интервалов подписи по X будут в две строки
        # (дата и время), поэтому снизу нужно чуть больше места.
        self.getAxis("bottom").setHeight(40)

    def reset_view(self) -> None:
        """
        Сбросить пользовательский масштаб и заново вписать график в окно.

        Это полезно:
        - после сильного zoom;
        - после смены периода;
        - после двойного клика.
        """
        self.user_has_custom_view = False
        self._apply_default_ranges()

    def _apply_default_ranges(self) -> None:
        """
        Установить стандартный масштаб так, чтобы весь график был виден.

        Используется:
        - при первой загрузке данных;
        - при явном сбросе масштаба;
        - при смене периода.
        """
        if not self.points:
            return

        lows = [point.low_price for point in self.points]
        highs = [point.high_price for point in self.points]

        min_y = min(lows)
        max_y = max(highs)
        padding = max((max_y - min_y) * 0.05, 0.5)

        self.setXRange(-1, len(self.points), padding=0)
        self.setYRange(min_y - padding, max_y + padding, padding=0)

        self._update_view_limits()

    def _update_view_limits(self) -> None:
        """
        Обновить ограничения ViewBox, чтобы график не уезжал слишком далеко
        в пустоту при drag и zoom.
        """
        if not self.points:
            return

        lows = [point.low_price for point in self.points]
        highs = [point.high_price for point in self.points]

        min_y = min(lows)
        max_y = max(highs)
        y_padding = max((max_y - min_y) * 0.20, 2.0)

        self.getViewBox().setLimits(
            xMin=-1.0,
            xMax=float(len(self.points)),
            yMin=min_y - y_padding,
            yMax=max_y + y_padding,
        )

    def set_points(
        self,
        points: list[CandlePoint],
        line_color: str | None = None,
        force_reset_view: bool = False,
    ) -> None:
        """
        Передать графику новые свечи и обновить отображение.

        Args:
            points:
                Список CandlePoint для отображения.
            line_color:
                Необязательный аргумент для совместимости интерфейсов.
            force_reset_view:
                Если True, график принудительно сбрасывает масштаб и
                заново вписывает весь диапазон в окно.
        """
        self.points = points
        self.candles_item.set_points(points)

        axis = self.getAxis("bottom")

        if not points:
            axis.setTicks([[]])
            self.crosshair.hide()
            self.hover_label.setText("Наведи мышь на график")
            return

        self._refresh_bottom_axis_ticks()

        if force_reset_view:
            self.user_has_custom_view = False

        self._update_view_limits()

        if not self.user_has_custom_view:
            self._apply_default_ranges()


    def _build_bottom_ticks(
        self,
        points: list[CandlePoint],
        x_min: float | None = None,
        x_max: float | None = None,
    ) -> list[tuple[int, str]]:
        """
        Построить подписи нижней оси X с учётом текущего масштаба.

        Идея:
        - чем больше свечей видно на экране, тем короче и реже подписи;
        - чем сильнее zoom-in, тем подробнее подписи;
        - при смене дня можно показывать дату отдельно, чтобы пользователь
          не терял ориентацию во времени.

        Args:
            points:
                Полный список свечей графика.
            x_min:
                Левая граница видимого диапазона по X.
            x_max:
                Правая граница видимого диапазона по X.

        Returns:
            Список тиков в формате pyqtgraph:
            [(индекс_свечи, подпись), ...]
        """
        total = len(points)
        if total == 0:
            return []

        if x_min is None or x_max is None:
            visible_start = 0
            visible_end = total - 1
        else:
            visible_start = max(0, int(x_min))
            visible_end = min(total - 1, int(x_max))

        if visible_end < visible_start:
            return []

        visible_count = visible_end - visible_start + 1

        if visible_count >= 80:
            target_tick_count = 4
            label_mode = "date_only"
        elif visible_count >= 35:
            target_tick_count = 5
            label_mode = "time_or_date"
        elif visible_count >= 15:
            target_tick_count = 6
            label_mode = "datetime_on_day_change"
        else:
            target_tick_count = 7
            label_mode = "full_datetime"

        step = max(1, visible_count // target_tick_count)

        ticks: list[tuple[int, str]] = []
        used_indexes: set[int] = set()
        previous_tick_date = None

        for index in range(visible_start, visible_end + 1, step):
            point = points[index]
            tick_label = self._format_axis_label(
                point=point,
                previous_tick_date=previous_tick_date,
                label_mode=label_mode,
            )

            ticks.append((index, tick_label))
            used_indexes.add(index)
            previous_tick_date = point.dt.date()

        if visible_end not in used_indexes:
            last_point = points[visible_end]
            tick_label = self._format_axis_label(
                point=last_point,
                previous_tick_date=previous_tick_date,
                label_mode=label_mode,
            )
            ticks.append((visible_end, tick_label))

        return ticks


    def _format_axis_label(
        self,
        point: CandlePoint,
        previous_tick_date,
        label_mode: str,
    ) -> str:
        """
        Подготовить подпись для оси X в зависимости от текущего масштаба.

        Args:
            point:
                Свеча, для которой строится подпись.
            previous_tick_date:
                Дата предыдущего уже добавленного тика.
            label_mode:
                Режим отображения подписи. Возможные значения:
                - date_only
                - time_or_date
                - datetime_on_day_change
                - full_datetime

        Returns:
            Готовая строка подписи для оси X.
        """
        current_dt = point.dt
        current_date = current_dt.date()

        date_text = current_dt.strftime("%d.%m")
        time_text = current_dt.strftime("%H:%M")
        full_text = current_dt.strftime("%d.%m\n%H:%M")

        is_daily_candle = (
            current_dt.hour == 0
            and current_dt.minute == 0
            and current_dt.second == 0
        )

        if is_daily_candle:
            return point.label

        if label_mode == "date_only":
            return date_text

        if label_mode == "time_or_date":
            if previous_tick_date != current_date:
                return date_text
            return time_text

        if label_mode == "datetime_on_day_change":
            if previous_tick_date != current_date:
                return full_text
            return time_text

        return full_text

    def _refresh_bottom_axis_ticks(self) -> None:
        """
        Пересчитать подписи оси X под текущий видимый диапазон графика.

        Метод вызывается:
        - после загрузки новых данных;
        - после zoom;
        - после drag по оси X;
        - после сброса масштаба.
        """
        axis = self.getAxis("bottom")

        if not self.points:
            axis.setTicks([[]])
            return

        (x_min, x_max), _ = self.getViewBox().viewRange()
        ticks = self._build_bottom_ticks(
            self.points,
            x_min=x_min,
            x_max=x_max,
        )
        axis.setTicks([ticks])

    def _on_x_range_changed(self, _view_box, _range) -> None:
        """
        Обработать изменение видимого диапазона по X.

        Когда пользователь приближает или двигает график,
        подписи нижней оси должны адаптироваться под новый масштаб.
        """
        if not self.points:
            return

        self._refresh_bottom_axis_ticks()

    def wheelEvent(self, event) -> None:
        """
        Обработать прокрутку колеса мыши для масштабирования графика.

        Логика:
        - обычное колесо: горизонтальный zoom по оси X вокруг курсора;
        - Shift + колесо: вертикальный zoom по оси Y вокруг курсора.

        Args:
            event:
                Событие колеса мыши Qt.
        """
        if not self.points:
            event.ignore()
            return

        delta = event.angleDelta().y()
        if delta == 0:
            event.ignore()
            return

        self.user_has_custom_view = True

        factor = 0.85 if delta > 0 else 1.15
        modifiers = event.modifiers()

        scene_pos = event.position()
        view_pos = self.getViewBox().mapSceneToView(scene_pos)

        if modifiers & Qt.KeyboardModifier.ShiftModifier:
            self._scale_y_around_anchor(factor, view_pos.y())
        else:
            self._scale_x_around_anchor(factor, view_pos.x())

        event.accept()

    def _scale_x_around_anchor(self, factor: float, anchor_x: float) -> None:
        """
        Масштабировать график по оси X вокруг конкретной точки курсора.

        Args:
            factor:
                Коэффициент изменения масштаба.
                Меньше 1 — приблизить, больше 1 — отдалить.
            anchor_x:
                X-координата точки привязки в координатах графика.
        """
        view_box = self.getViewBox()
        (x_min, x_max), _ = view_box.viewRange()

        left_dist = anchor_x - x_min
        right_dist = x_max - anchor_x

        new_left_dist = left_dist * factor
        new_right_dist = right_dist * factor

        new_x_min = anchor_x - new_left_dist
        new_x_max = anchor_x + new_right_dist

        min_width = 5.0
        max_width = max(float(len(self.points)) + 2.0, min_width)

        current_width = new_x_max - new_x_min

        if current_width < min_width:
            half = min_width / 2.0
            new_x_min = anchor_x - half
            new_x_max = anchor_x + half

        if current_width > max_width:
            half = max_width / 2.0
            new_x_min = anchor_x - half
            new_x_max = anchor_x + half

        hard_min = -1.0
        hard_max = float(len(self.points))

        if new_x_min < hard_min:
            shift = hard_min - new_x_min
            new_x_min += shift
            new_x_max += shift

        if new_x_max > hard_max:
            shift = new_x_max - hard_max
            new_x_min -= shift
            new_x_max -= shift

        view_box.setXRange(new_x_min, new_x_max, padding=0)
        self._update_view_limits()

    def _scale_y_around_anchor(self, factor: float, anchor_y: float) -> None:
        """
        Масштабировать график по оси Y вокруг конкретной точки курсора.

        Args:
            factor:
                Коэффициент изменения масштаба.
                Меньше 1 — приблизить, больше 1 — отдалить.
            anchor_y:
                Y-координата точки привязки в координатах графика.
        """
        view_box = self.getViewBox()
        _, (y_min, y_max) = view_box.viewRange()

        lower_dist = anchor_y - y_min
        upper_dist = y_max - anchor_y

        new_lower_dist = lower_dist * factor
        new_upper_dist = upper_dist * factor

        new_y_min = anchor_y - new_lower_dist
        new_y_max = anchor_y + new_upper_dist

        min_height = 1.0
        current_height = new_y_max - new_y_min

        if current_height < min_height:
            half = min_height / 2.0
            new_y_min = anchor_y - half
            new_y_max = anchor_y + half

        view_box.setYRange(new_y_min, new_y_max, padding=0)
        self._update_view_limits()

    def mouseDoubleClickEvent(self, event) -> None:
        """
        Обработать двойной клик мышью.

        Двойной левый клик сбрасывает масштаб графика к начальному виду.

        Args:
            event:
                Событие мыши Qt.
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self.reset_view()
            event.accept()
            return

        super().mouseDoubleClickEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        """
        Обработать отпускание кнопки мыши.

        После drag считаем, что пользователь вручную изменил viewport,
        поэтому автоподгонку на следующих обновлениях отключаем.

        Args:
            event:
                Событие мыши Qt.
        """
        if event.button() == Qt.MouseButton.LeftButton and self.points:
            self.user_has_custom_view = True

        super().mouseReleaseEvent(event)

    def on_mouse_moved(self, pos: QPointF) -> None:
        """
        Обработать движение мыши по сцене графика.

        Логика:
        - переводим позицию мыши из scene в координаты графика;
        - округляем X до ближайшего индекса свечи;
        - показываем кроссхейр на close выбранной свечи;
        - выводим точное время и O/H/L/C в hover_label.

        Args:
            pos:
                Позиция курсора в координатах scene.
        """
        if not self.points:
            self.crosshair.hide()
            return

        if not self.sceneBoundingRect().contains(pos):
            self.crosshair.hide()
            return

        vb = self.getPlotItem().vb
        mouse_point = vb.mapSceneToView(pos)
        x_index = round(mouse_point.x())

        if x_index < 0 or x_index >= len(self.points):
            self.crosshair.hide()
            return

        point = self.points[x_index]

        self.crosshair.show()
        self.crosshair.set_position(x_index, point.close_price)

        self.hover_label.setText(
            f"{point.dt.strftime('%d.%m.%Y %H:%M')} · "
            f"O {point.open_price:.2f} · "
            f"H {point.high_price:.2f} · "
            f"L {point.low_price:.2f} · "
            f"C {point.close_price:.2f} ₽"
        )