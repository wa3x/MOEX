"""
Стили интерфейса.

Стили вынесены в отдельный файл, чтобы не хранить большие CSS-строки
внутри окна и быстрее менять внешний вид.
"""

CARD_STYLE = """
QFrame {
    background-color: rgba(19, 22, 28, 238);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 5px;
}
"""

BUTTON_STYLE = """
QPushButton {
    background-color: rgba(255, 255, 255, 0.06);
    color: #f5f7fa;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 5px;
    padding: 8px 14px;
    font-size: 13px;
    font-weight: 500;
}
QPushButton:hover {
    background-color: rgba(255, 255, 255, 0.10);
    border: 1px solid rgba(255, 255, 255, 0.12);
}
QPushButton:pressed {
    background-color: rgba(255, 255, 255, 0.14);
}
"""

CLOSE_BUTTON_STYLE = """
QPushButton {
    background-color: rgba(255, 255, 255, 0.05);
    color: #d7dde5;
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 5px;
    padding: 6px 0;
    font-size: 13px;
    font-weight: 600;
}
QPushButton:hover {
    background-color: rgba(255, 90, 90, 0.18);
    color: #ffffff;
    border: 1px solid rgba(255, 110, 110, 0.18);
}
QPushButton:pressed {
    background-color: rgba(255, 90, 90, 0.26);
}
"""

COMBO_STYLE = """
QComboBox {
    background-color: rgba(255, 255, 255, 0.06);
    color: #f5f7fa;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 4px;
    padding: 8px 34px 8px 12px;
    min-width: 96px;
    font-size: 13px;
    font-weight: 500;
}

QComboBox:hover {
    background-color: rgba(255, 255, 255, 0.10);
    border: 1px solid rgba(255, 255, 255, 0.12);
}

QComboBox:focus {
    border: 1px solid rgba(120, 180, 255, 0.35);
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 26px;
    border: none;
    background: transparent;
}

QComboBox::down-arrow {
    image: url(ui/assets/chevron_down.svg);
    width: 12px;
    height: 12px;
}
"""

COMBO_POPUP_STYLE = """
QListView {
    background-color: #171b22;
    color: #f5f7fa;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 4px;
    outline: none;
    padding: 0px;
    margin: 0px;
    show-decoration-selected: 1;
}

QListView::item {
    min-height: 28px;
    padding: 0px 10px;
    margin: 0px;
    border: none;
    background-color: #171b22;
}

QListView::item:selected {
    background-color: rgba(120, 180, 255, 0.22);
    color: #ffffff;
}

QListView::item:hover {
    background-color: rgba(255, 255, 255, 0.06);
}
"""

TEXT_PRIMARY = """
QLabel {
    color: #f4f7fb;
    background: transparent;
    border: none;
}
"""

TEXT_MUTED = """
QLabel {
    color: #95a0ae;
    background: transparent;
    border: none;
}
"""

TEXT_PRICE = """
QLabel {
    color: #ffffff;
    background: transparent;
    border: none;
    font-weight: 700;
}
"""

TEXT_CHANGE_POSITIVE = """
QLabel {
    color: #7ee787;
    background: transparent;
    border: none;
    font-weight: 600;
}
"""

TEXT_CHANGE_NEGATIVE = """
QLabel {
    color: #ff7b72;
    background: transparent;
    border: none;
    font-weight: 600;
}
"""