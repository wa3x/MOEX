from __future__ import annotations

import pyqtgraph as pg


class ChartCrosshair:
    """
    Кроссхейр для графика:
    - вертикальная линия;
    - горизонтальная линия.

    Этот класс отделён от самого графика, чтобы:
    - не смешивать логику данных и UI-оверлеев;
    - можно было отдельно дорабатывать hover-механику.
    """

    def __init__(self, plot_widget: pg.PlotWidget) -> None:
        """
        Создать и добавить линии кроссхейра на график.

        Args:
            plot_widget:
                Экземпляр графика pyqtgraph, на который нужно добавить линии.
        """
        self.plot_widget = plot_widget

        self.v_line = pg.InfiniteLine(angle=90, movable=False)
        self.h_line = pg.InfiniteLine(angle=0, movable=False)

        self.v_line.setPen(pg.mkPen(color="#6b7280", width=1))
        self.h_line.setPen(pg.mkPen(color="#6b7280", width=1))

        self.plot_widget.addItem(self.v_line, ignoreBounds=True)
        self.plot_widget.addItem(self.h_line, ignoreBounds=True)

        self.hide()

    def show(self) -> None:
        """
        Показать линии кроссхейра.
        """
        self.v_line.show()
        self.h_line.show()

    def hide(self) -> None:
        """
        Скрыть линии кроссхейра.
        """
        self.v_line.hide()
        self.h_line.hide()

    def set_position(self, x_index: int, y_price: float) -> None:
        """
        Установить положение кроссхейра.

        Args:
            x_index:
                Индекс точки по оси X.
            y_price:
                Значение цены по оси Y.
        """
        self.v_line.setPos(x_index)
        self.h_line.setPos(y_price)