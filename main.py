import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFontDatabase, QFont, QIcon
from core.database import init_db
from core.utils import load_config
from ui.main_window import MainWindow

def main():
    # Initialize DB
    init_db()
    
    app = QApplication(sys.argv)
    
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(os.path.dirname(__file__))
    font_path = os.path.join(base_path, "assets", "NotoSansKR.otf")
    if os.path.exists(font_path):
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id != -1:
            font_families = QFontDatabase.applicationFontFamilies(font_id)
            if font_families:
                app.setFont(QFont(font_families[0]))
    
    # Set App Icon
    icon_path = os.path.join(base_path, "assets", "icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Show main window
    window = MainWindow()
    window.apply_theme()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
