import sys
from PySide6.QtWidgets import QApplication, QWidget, QPushButton
from PySide6.QtGui import QCloseEvent, QHideEvent, QPainter, QColor, QResizeEvent, QPainterPath, QShowEvent
from PySide6.QtCore import QEvent, QObject, Qt, QRect, QPoint, QSize, QTimer, QThread, Signal, QEventLoop


class WorkThread(QThread):
    send_finish_sig = Signal(list)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.m_func = None
        self.m_args = None
        self.m_kwargs = None

    def set_func(self, func, *args, **kwargs):
        self.m_func = func
        self.m_args = args
        self.m_kwargs = kwargs

    def run(self):
        try:
            result = None
            if self.m_func:
                if len(self.m_args) > 0 and len(self.m_kwargs) > 0:
                    result = self.m_func(*self.m_args, **self.m_kwargs)
                elif len(self.m_args) > 0:
                    result = self.m_func(*self.m_args)
                elif len(self.m_kwargs) > 0:
                    result = self.m_func(**self.m_kwargs)
                else:
                    result = self.m_func()
        except Exception as e:
            print(f"load_widget线程函数执行出错:{e}")
        finally:
            self.m_func = None
            self.m_args = None
            self.m_kwargs = None
            self.send_finish_sig.emit([result])


class LoadWidget(QWidget):
    _instance = None

    @staticmethod
    def get_instance(parent=None, info=""):
        if LoadWidget._instance is None:
            LoadWidget._instance = LoadWidget(parent, info)
        else:
            if parent is not None:
                LoadWidget._instance.setParent(parent)
            if len(info) > 0:
                LoadWidget._instance.setInfoText(info)
        return LoadWidget._instance

    @staticmethod
    def show_load_widget(parent=None, info=""):
        if parent is None and LoadWidget._instance.parent() is None:
            parent = QApplication.activeWindow()
        LoadWidget.get_instance(parent, info).show()

    @staticmethod
    def start_exec_func(info, func, *args, **kwargs):
        return LoadWidget.get_instance(info=info).set_func(func, *args, **kwargs)

    @staticmethod
    def hide_load_widget():
        LoadWidget.get_instance().hide()

    def __init__(self, parent=None, info=""):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        if len(info) > 0:
            self.m_showText = info
        else:
            self.m_showText = "加载中"
        self.m_results = None
        self.m_count = 3
        self.m_loop = QEventLoop(self)
        self.m_workThread = WorkThread(self)
        self.m_workThread.send_finish_sig.connect(self.recv_finish_sig)
        self.m_timer = QTimer(self)
        self.m_timer.setInterval(500)
        self.m_timer.timeout.connect(self.on_update_widget)
        self.setParent(parent)
        self.hide()

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if watched == self.parent() and event.type() == QEvent.Resize:
            self.on_parent_resize(event)
        if watched == self.parent() and event.type() == QEvent.Close:
            self.close()
        return super().eventFilter(watched, event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(5, 5, 5, 100))  # 设置整个窗口的背景颜色

        centerPos = QPoint(self.width() / 2, self.height() / 2)
        painterPath = QPainterPath()
        rect_length = 80
        rect_radius = 40
        painter.setBrush(QColor(50, 50, 50))
        painter.setPen(QColor(50, 50, 50))
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
        font.setPointSize(14)
        painter.setFont(font)

        text_size = QSize(rect_length, rect_length)

        showText = f"{self.m_showText}\n{'.'*self.m_count}"

        painter.drawText(
            QRect(centerPos.x() - text_size.width() / 2,
                  centerPos.y() - text_size.height() / 2, text_size.width(), text_size.height()), Qt.AlignCenter,
            showText)

    def showEvent(self, event: QShowEvent) -> None:
        self.m_timer.start()
        self.m_count = 3
        return super().showEvent(event)

    def hideEvent(self, event: QHideEvent) -> None:
        self.m_timer.stop()
        return super().hideEvent(event)

    def resizeEvent(self, event: QResizeEvent) -> None:
        self.update()
        return super().resizeEvent(event)

    def closeEvent(self, event: QCloseEvent) -> None:
        self.m_timer.stop()
        return super().closeEvent(event)

    def set_func(self, func, *args, **kwargs):
        if self.m_workThread.isRunning():
            self.hide()
            return None
        else:
            self.m_workThread.set_func(func, *args, **kwargs)
            self.m_workThread.start()
            self.show()
            self.m_loop.exec()
            self.m_workThread.quit()
            self.m_workThread.wait()
            return self.m_results[0]

    def recv_finish_sig(self, results):
        self.m_results = results
        self.m_loop.quit()
        self.hide()

    def setInfoText(self, info):
        self.m_showText = info

    def on_update_widget(self):
        if self.m_count >= 3:
            self.m_count = 0
        else:
            self.m_count += 1
        self.update()

    def setParent(self, parent):
        if self.parent() is not None:
            self.removeEventFilter(self.parent())
        super().setParent(parent)
        if parent:
            parent.installEventFilter(self)
            self.on_parent_resize()

    def on_parent_resize(self, event=None):
        # 当父级窗口大小变化时调用此方法
        self.resize(self.parent().geometry().width(), self.parent().geometry().height())


class mainWindow(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        btn = QPushButton(self)
        btn.clicked.connect(self.on_clicked)
        # LoadWidget.get_instance(self)
        # LoadWidget.show_load_widget(self)
        # QApplication.processEvents()
        # LoadWidget.start_exec_func(self.test_func)
        # QTimer.singleShot(1, lambda: LoadWidget.start_exec_func(self.test_func))

    def on_clicked(self):
        # LoadWidget.show_load_widget(self)
        LoadWidget.get_instance(self)
        LoadWidget.start_exec_func('执行中', self.test_func, 3)

    def test_func(self, cnt):
        cnt = cnt
        while cnt > 0:
            print(f"{cnt}")
            cnt -= 1
            self.thread().sleep(1)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = mainWindow()
    widget.show()
    sys.exit(app.exec())
