import sys
from PySide6.QtWidgets import QApplication, QWidget, QHBoxLayout, QPushButton, QLabel
from PySide6.QtGui import QCloseEvent, QHideEvent, QPainter, QColor, QResizeEvent, QPainterPath, QShowEvent
from PySide6.QtCore import QEvent, QObject, Qt, QRect, QPoint, QSize, QTimer, QThread, Signal, QTime


class LoadWidget(QWidget):

    def __init__(self, parent=None, info="加载中"):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 50);")
        self.m_showText = info
        self.m_count = 0
        self.m_timer = QTimer()
        self.m_timer.setInterval(500)
        self.m_thread = QThread()
        self.m_thread.started.connect(self.m_timer.start)
        self.m_thread.finished.connect(self.m_timer.stop)
        self.m_timer.timeout.connect(self.on_update_widget)
        self.m_timer.moveToThread(self.m_thread)
        if parent:
            parent.installEventFilter(self)
            self.on_parent_resize()
        else:
            self.hide()

    def refresh_show(self, parent=None):
        if parent is not None:
            self.setParent(parent)
            self.on_parent_resize()
        self.show()

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if watched == self.parent() and event.type() == QEvent.Resize:
            self.on_parent_resize(event)
        if watched == self.parent() and event.type() == QEvent.Close:
            self.close()
        return super().eventFilter(watched, event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        centerPos = QPoint(self.width() / 2, self.height() / 2)
        painterPath = QPainterPath()
        rect_length = 70
        rect_radius = 30
        painter.setBrush(QColor(0, 0, 0, 200))
        painterPath.moveTo(centerPos.x() - rect_length / 2, centerPos.y() - rect_length / 2 - rect_radius)
        painterPath.lineTo(centerPos.x() + rect_length / 2, centerPos.y() - rect_length / 2 - rect_radius)
        painterPath.arcTo(centerPos.x() + rect_length / 2 - rect_radius,
                          centerPos.y() - rect_length / 2 - rect_radius, rect_radius * 2, rect_radius * 2, 90, -90)
        painterPath.lineTo(centerPos.x() + rect_length / 2 + rect_radius, centerPos.y() + rect_length / 2)
        painterPath.arcTo(centerPos.x() + rect_length / 2 - rect_radius,
                          centerPos.y() + rect_length / 2 - rect_radius, rect_radius * 2, rect_radius * 2, 0, -90)
        painterPath.lineTo(centerPos.x() - rect_length / 2, centerPos.y() + rect_length / 2 + rect_radius)
        painterPath.arcTo(centerPos.x() - rect_length / 2 - rect_radius,
                          centerPos.y() + rect_length / 2 - rect_radius, rect_radius * 2, rect_radius * 2, -90, -90)
        painterPath.lineTo(centerPos.x() - rect_length / 2 - rect_radius, centerPos.y() - rect_length / 2)
        painterPath.arcTo(centerPos.x() - rect_length / 2 - rect_radius,
                          centerPos.y() - rect_length / 2 - rect_radius, rect_radius * 2, rect_radius * 2, -180, -90)
        painter.drawPath(painterPath)

        painter.setPen(QColor(255, 255, 255))
        font = painter.font()
        font.setPointSize(16)
        painter.setFont(font)

        text_size = QSize(80, 40)
        painter.drawText(
            QRect(centerPos.x() - text_size.width() / 2,
                  centerPos.y() - text_size.height() / 2, text_size.width(), text_size.height()), Qt.AlignCenter,
            f"{self.m_showText}{'.'*self.m_count}")

    def on_parent_resize(self, event=None):
        # 当父级窗口大小变化时调用此方法
        self.resize(self.parent().geometry().width(), self.parent().geometry().height())

    def showEvent(self, event: QShowEvent) -> None:
        self.m_thread.start()
        return super().showEvent(event)

    def hideEvent(self, event: QHideEvent) -> None:
        self.m_thread.quit()
        self.m_thread.wait()
        return super().hideEvent(event)

    def resizeEvent(self, event: QResizeEvent) -> None:
        self.update()
        return super().resizeEvent(event)

    def closeEvent(self, event: QCloseEvent) -> None:
        self.m_thread.quit()
        self.m_thread.wait()
        return super().closeEvent(event)

    def on_update_widget(self):
        if self.m_count >= 3:
            self.m_count = 0
        else:
            self.m_count += 1
        self.update()


class mainWindow(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.load_widget = LoadWidget(self)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = mainWindow()
    widget.show()
    sys.exit(app.exec())
