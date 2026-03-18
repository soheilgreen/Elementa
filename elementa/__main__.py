"""
Elementa — command-line entry point.

Usage
-----
    elementa           # launch the GUI (default)
    python -m elementa # same
"""

import sys


def main() -> None:
    from PyQt6.QtWidgets import QApplication
    from elementa.ui.main_window import ElementaMainWindow

    def _global_excepthook(exc_type, exc_value, exc_traceback):
        import traceback
        import os

        log_path = os.path.join(os.path.expanduser("~"), "elementa_crash.log")
        with open(log_path, "w") as fh:
            traceback.print_exception(exc_type, exc_value, exc_traceback, file=fh)
        print(f"Unhandled exception — crash log written to: {log_path}")
        sys.__excepthook__(exc_type, exc_value, exc_traceback)

    sys.excepthook = _global_excepthook

    app = QApplication(sys.argv)
    app.setApplicationName("Elementa")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Elementa Project")

    window = ElementaMainWindow(auto_show_welcome=True)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
