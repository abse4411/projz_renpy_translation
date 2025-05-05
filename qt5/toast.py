from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import QTimer, Qt, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QColor

def show_toast(message="Hello!", parent=None, duration=2000,
               bg_color=QColor(0, 0, 0, 180),
               text_color=QColor(255, 255, 255)):
    popup = QWidget(parent, Qt.ToolTip | Qt.FramelessWindowHint)
    popup.setAttribute(Qt.WA_TranslucentBackground)
    popup.setWindowOpacity(0.0)

    layout = QVBoxLayout(popup)
    label = QLabel(message)
    label.setAlignment(Qt.AlignCenter)
    label.setStyleSheet(f"""
        background-color: rgba({bg_color.red()}, {bg_color.green()},
                             {bg_color.blue()}, {bg_color.alpha()});
        color: rgba({text_color.red()}, {text_color.green()},
                    {text_color.blue()}, {text_color.alpha()});
        padding: 10px; border-radius: 5px;
    """)
    layout.addWidget(label)

    screen = QApplication.primaryScreen().availableGeometry()
    popup.resize(screen.width() // 4, screen.height() // 10)
    popup.move(screen.center().x() - popup.width() // 2,
               screen.center().y() - popup.height() // 2)

    # —— 淡入动画 ——
    fade_in_animation = QPropertyAnimation(popup, b"windowOpacity")
    fade_in_animation.setDuration(300)
    fade_in_animation.setStartValue(0.0)
    fade_in_animation.setEndValue(0.9)
    fade_in_animation.setEasingCurve(QEasingCurve.InOutQuad)
    popup._fade_in_animation = fade_in_animation    # ← 保持引用

    # —— 淡出动画 ——
    fade_out_animation = QPropertyAnimation(popup, b"windowOpacity")
    fade_out_animation.setDuration(300)
    fade_out_animation.setStartValue(0.9)
    fade_out_animation.setEndValue(0.0)
    fade_out_animation.setEasingCurve(QEasingCurve.InOutQuad)
    popup._fade_out_animation = fade_out_animation  # ← 保持引用

    fade_out_animation.finished.connect(popup.close)

    popup.show()
    fade_in_animation.start()

    # —— 用 QTimer 在 duration 后触发淡出 ——
    def start_fade_out():
        if fade_in_animation.state() == QPropertyAnimation.Running:
            fade_in_animation.stop()
        fade_out_animation.start()

    popup._timer = QTimer(popup)                    # ← 保持引用
    popup._timer.setSingleShot(True)
    popup._timer.timeout.connect(start_fade_out)
    popup._timer.start(duration)
