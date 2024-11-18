from PySide6.QtWidgets import QApplication
import sys
from load_widget import mainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = mainWindow()
    widget.show()
    sys.exit(app.exec())
