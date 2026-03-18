import sys
from PyQt6.QtWidgets import QApplication
from elementa.ui.main_window import ElementaMainWindow

def global_excepthook(exc_type, exc_value, exc_traceback):
    import traceback
    with open("crash_log.txt", "w") as f:
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
    print("CRASH LOGGED TO crash_log.txt")
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

sys.excepthook = global_excepthook

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ElementaMainWindow(auto_show_welcome=True)
    window.show()
    sys.exit(app.exec())
