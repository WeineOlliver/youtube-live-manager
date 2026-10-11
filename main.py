"""YouTube Live Manager — QApplication entry point."""
import os
import sys
import traceback
from datetime import datetime

from PyQt6.QtWidgets import QApplication, QMessageBox

from ui.main_window import MainWindow

ERROR_LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "error.log")


def _excepthook(exc_type, exc, tb):
    # Without a custom hook, PyQt6 aborts the whole app on any exception raised in a slot.
    details = "".join(traceback.format_exception(exc_type, exc, tb))
    sys.stderr.write(details)
    try:
        with open(ERROR_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"\n[{datetime.now():%Y-%m-%d %H:%M:%S}]\n{details}")
    except OSError:
        pass
    if QApplication.instance() is not None:
        QMessageBox.critical(
            None,
            "Erro inesperado",
            f"{exc_type.__name__}: {exc}\n\nO app continua aberto. Detalhes em error.log",
        )


def main():
    sys.excepthook = _excepthook
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
