import os
import sys
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QListWidget, QListWidgetItem, QPushButton, 
                             QToolBar, QMessageBox, QFileDialog, QSplitter,
                             QSizePolicy)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QFontMetrics, QFontDatabase, QFont
from core.database import get_all_games, delete_game
from core.utils import (load_config, save_config, export_tier_list, 
                        backup_data, restore_data)
from ui.tier_view import TierView
from ui.dialogs import SettingsDialog, GameDialog
from ui.translations import TRANSLATIONS

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.lang = self.config.get("language", "한국어")
        self.texts = TRANSLATIONS.get(self.lang, TRANSLATIONS["한국어"])
        self.palette_mode = False
        self.list_sort_order = 'desc'
        self.tier_sort_order = 'desc'
        self.games = []
        
        self.init_fonts()
        self.init_ui()
        self.apply_theme()
        self.refresh_data()

    def init_fonts(self):
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
        font_kr = os.path.join(base_path, "assets", "NotoSansKR.otf")
        font_jp = os.path.join(base_path, "assets", "NotoSansJP.otf")
        
        if os.path.exists(font_kr):
            QFontDatabase.addApplicationFont(font_kr)
        if os.path.exists(font_jp):
            QFontDatabase.addApplicationFont(font_jp)
        
        self.update_app_font()

    def update_app_font(self):
        # Choose font family based on language
        if self.lang == "日本語":
            family = "Noto Sans JP"
        else:
            family = "Noto Sans KR"
        
        from PyQt6.QtWidgets import QApplication
        font = QFont(family, 10)
        QApplication.instance().setFont(font)

    def init_ui(self):
        self.setWindowTitle(self.texts["app_title"])
        self.resize(1280, 720)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Splitter for List and Tier View
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left Panel (List)
        left_container = QWidget()
        left_container.setMinimumWidth(250)
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        self.btn_list_sort = QPushButton()
        self.btn_list_sort.clicked.connect(self.toggle_list_sort)
        left_layout.addWidget(self.btn_list_sort)
        
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list_widget.itemDoubleClicked.connect(self.edit_game_dialog)
        left_layout.addWidget(self.list_widget)
        
        # Right Panel (Tier View)
        right_container = QWidget()
        right_container.setMinimumWidth(500)
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        self.btn_tier_sort = QPushButton()
        self.btn_tier_sort.clicked.connect(self.toggle_tier_sort)
        right_layout.addWidget(self.btn_tier_sort)
        
        self.tier_view = TierView()
        right_layout.addWidget(self.tier_view)
        
        self.splitter.addWidget(left_container)
        self.splitter.addWidget(right_container)
        self.splitter.setCollapsible(0, False)
        self.splitter.setCollapsible(1, False)
        self.splitter.setStretchFactor(0, 0) # List doesn't need much stretch
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([250, 1030])
        self.splitter.setHandleWidth(10)
        
        main_layout.addWidget(self.splitter)
        
        # Toolbar
        self.init_toolbar()
        self.update_ui_texts()

    def init_toolbar(self):
        self.toolbar = QToolBar()
        self.toolbar.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.BottomToolBarArea, self.toolbar)
        
        self.btn_add = QPushButton(self.texts["btn_add"])
        self.btn_add.clicked.connect(self.add_game_dialog)
        self.toolbar.addWidget(self.btn_add)
        
        self.btn_edit = QPushButton(self.texts["btn_edit"])
        self.btn_edit.clicked.connect(self.edit_game_dialog)
        self.toolbar.addWidget(self.btn_edit)
        
        self.btn_del = QPushButton(self.texts["btn_del"])
        self.btn_del.clicked.connect(self.delete_selected_game)
        self.toolbar.addWidget(self.btn_del)
        
        self.toolbar.addSeparator()
        
        self.btn_export = QPushButton(self.texts["btn_export"])
        self.btn_export.clicked.connect(self.export_image)
        self.toolbar.addWidget(self.btn_export)
        
        self.btn_backup = QPushButton(self.texts["btn_backup"])
        self.btn_backup.clicked.connect(self.backup_db)
        self.toolbar.addWidget(self.btn_backup)
        
        self.btn_restore = QPushButton(self.texts["btn_restore"])
        self.btn_restore.clicked.connect(self.restore_db)
        self.toolbar.addWidget(self.btn_restore)
        
        self.toolbar.addSeparator()
        
        # Palette Button
        self.btn_palette = QPushButton(self.texts["btn_palette"])
        self.btn_palette.clicked.connect(self.toggle_palette_mode)
        self.toolbar.addWidget(self.btn_palette)
        
        # Theme Toggle
        self.btn_theme = QPushButton("🌙" if self.config.get("theme", "dark") == "dark" else "☀️")
        self.btn_theme.clicked.connect(self.toggle_theme)
        self.toolbar.addWidget(self.btn_theme)
        
        # Settings Button
        self.btn_settings = QPushButton("⚙️")
        self.btn_settings.clicked.connect(self.open_settings)
        self.toolbar.addWidget(self.btn_settings)

        # Spacer
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.toolbar.addWidget(spacer)
        
        # GitHub Button
        self.btn_github = QPushButton(" GitHub")
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        icon_path = os.path.join(base_path, "assets", "github.png")
        if os.path.exists(icon_path):
            self.btn_github.setIcon(QIcon(icon_path))
        from PyQt6.QtGui import QDesktopServices
        from PyQt6.QtCore import QUrl
        self.btn_github.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://github.com/MaratangNearl/vn_userdb_tierlist")))
        self.toolbar.addWidget(self.btn_github)

    def toggle_list_sort(self):
        self.list_sort_order = 'asc' if self.list_sort_order == 'desc' else 'desc'
        self.update_sort_buttons()
        self.refresh_data()

    def toggle_tier_sort(self):
        self.tier_sort_order = 'asc' if self.tier_sort_order == 'desc' else 'desc'
        self.update_sort_buttons()
        self.refresh_data()

    def update_sort_buttons(self):
        l_arr = "▲" if self.list_sort_order == 'asc' else "▼"
        t_arr = "▲" if self.tier_sort_order == 'asc' else "▼"
        self.btn_list_sort.setText(f"{self.texts['btn_list_sort']} ({l_arr})")
        self.btn_tier_sort.setText(f"{self.texts['btn_tier_sort']} ({t_arr})")

    def toggle_palette_mode(self):
        self.palette_mode = not self.palette_mode
        self.apply_theme()
        if self.palette_mode:
            QMessageBox.information(self, self.texts["btn_palette"], self.texts["msg_palette_hint"])

    def toggle_theme(self):
        current = self.config.get("theme", "dark")
        new_theme = "light" if current == "dark" else "dark"
        self.config["theme"] = new_theme
        save_config(self.config)
        self.btn_theme.setText("🌙" if new_theme == "dark" else "☀️")
        self.apply_theme()

    def apply_theme(self):
        theme = self.config.get("theme", "dark")
        if theme == "dark":
            style = """
                QMainWindow, QDialog, QFrame, QLabel, QCheckBox, QRadioButton, QGroupBox, QToolButton { 
                    background-color: #121212; color: #E0E0E0; 
                }
                QPushButton { 
                    background-color: #2D2D2D; border: 1px solid #3D3D3D; padding: 5px 10px; border-radius: 4px;
                    color: #E0E0E0; height: 28px; min-height: 28px; max-height: 28px;
                    font-size: 12px;
                }
                QPushButton:hover { background-color: #3D3D3D; }
                QListWidget { background-color: #1E1E1E; border: 1px solid #333; border-radius: 4px; }
                QToolBar { 
                    background-color: #1E1E1E; border-top: 1px solid #333; 
                    padding: 4px; height: 36px; min-height: 36px; max-height: 36px;
                }
                QLineEdit, QTextEdit, QSpinBox, QComboBox { 
                    background-color: #2D2D2D; color: #E0E0E0; border: 1px solid #3D3D3D; padding: 3px;
                }
                QComboBox QAbstractItemView {
                    background-color: #2D2D2D; color: #E0E0E0; selection-background-color: #3D3D3D;
                }
                QScrollBar:vertical {
                    border: none; background: #121212; width: 10px; margin: 0px;
                }
                QScrollBar::handle:vertical {
                    background: #3D3D3D; min-height: 20px; border-radius: 5px;
                }
                QScrollBar::handle:vertical:hover { background: #4D4D4D; }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
                QSplitter::handle { background: #333; }
                QColorDialog { background-color: #1E1E1E; }
                QColorDialog QLabel, QColorDialog QPushButton, QColorDialog QLineEdit, QColorDialog QSpinBox { 
                    color: #E0E0E0; background-color: #2D2D2D; 
                }
            """
            from PyQt6.QtWidgets import QApplication
            QApplication.instance().setStyleSheet(style)
            
            # Check for custom background color
            bg = self.config.get("bg_color")
            if bg:
                self.tier_view.setStyleSheet(f"background-color: {bg}; border: none;")
                self.tier_view.main_widget.setStyleSheet(f"background-color: {bg};")
            else:
                self.tier_view.setStyleSheet("background-color: #1E1E1E; border: none;")
                self.tier_view.main_widget.setStyleSheet("background-color: #1E1E1E;")
        else:
            style = """
                QMainWindow, QDialog, QFrame, QLabel, QCheckBox, QRadioButton, QGroupBox, QToolButton { 
                    background-color: #F0F2F5; color: #2C3E50; 
                }
                QPushButton { 
                    background-color: #FFFFFF; border: 1px solid #DCDFE6; padding: 5px 10px; border-radius: 6px;
                    color: #606266; font-weight: 500; height: 28px; min-height: 28px; max-height: 28px;
                    font-size: 12px;
                }
                QPushButton:hover { background-color: #ECF5FF; border-color: #C6E2FF; color: #409EFF; }
                QListWidget { background-color: #FFFFFF; border: 1px solid #DCDFE6; border-radius: 8px; }
                QToolBar { 
                    background-color: #FFFFFF; border-top: 1px solid #DCDFE6; 
                    padding: 4px; height: 36px; min-height: 36px; max-height: 36px;
                }
                QLineEdit, QTextEdit, QSpinBox, QComboBox { 
                    background-color: #FFFFFF; color: #2C3E50; border: 1px solid #DCDFE6; padding: 3px;
                }
                QScrollBar:vertical {
                    border: none; background: #F0F2F5; width: 10px; margin: 0px;
                }
                QScrollBar::handle:vertical {
                    background: #DCDFE6; min-height: 20px; border-radius: 5px;
                }
                QScrollBar::handle:vertical:hover { background: #C0C4CC; }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
                QSplitter::handle { background: #DCDFE6; }
                QColorDialog { background-color: #F0F2F5; color: #2C3E50; }
                QColorDialog QPushButton { height: 24px; min-height: 24px; }
            """
            from PyQt6.QtWidgets import QApplication
            QApplication.instance().setStyleSheet(style)
            
            # Check for custom background color
            bg = self.config.get("bg_color")
            if bg:
                self.tier_view.setStyleSheet(f"background-color: {bg}; border: none;")
                self.tier_view.main_widget.setStyleSheet(f"background-color: {bg};")
            else:
                self.tier_view.setStyleSheet("background-color: #F0F2F5; border: none;")
                self.tier_view.main_widget.setStyleSheet("background-color: #F0F2F5;")
        
        if self.palette_mode:
            self.btn_palette.setStyleSheet("background-color: #F44336; color: white; border-radius: 5px; font-weight: bold; height: 28px; min-height: 28px; max-height: 28px;")
        else:
            self.btn_palette.setStyleSheet("")

    def open_settings(self):
        dlg = SettingsDialog(self)
        if dlg.exec():
            self.load_settings()
            self.apply_theme()
            self.update_ui_texts()
            self.refresh_data()

    def load_settings(self):
        self.config = load_config()
        self.lang = self.config.get("language", "한국어")
        self.texts = TRANSLATIONS.get(self.lang, TRANSLATIONS["한국어"])
        self.update_app_font()

    def update_ui_texts(self):
        self.setWindowTitle(self.texts["app_title"])
        self.btn_add.setText(self.texts["btn_add"])
        self.btn_edit.setText(self.texts["btn_edit"])
        self.btn_del.setText(self.texts["btn_del"])
        self.btn_export.setText(self.texts["btn_export"])
        self.btn_backup.setText(self.texts["btn_backup"])
        self.btn_restore.setText(self.texts["btn_restore"])
        self.btn_palette.setText(self.texts["btn_palette"])
        self.update_sort_buttons()

    def refresh_data(self):
        new_games = get_all_games()
        if not new_games:
            self.games = []
            self.list_widget.clear()
            self.tier_view.update_tiers([], self.tier_sort_order)
            return

        # Mode change detection
        distinct_scores = set(g['score'] for g in new_games)
        is_score_based = len(distinct_scores) <= 10
        was_score_based = len(set(g['score'] for g in self.games)) <= 10 if self.games else is_score_based
        
        if self.games and was_score_based != is_score_based and self.config.get("colors"):
            reply = QMessageBox.question(self, self.texts["msg_warning"], self.texts["msg_range_reset_warn"],
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.config["colors"] = {}
                save_config(self.config)

        from core.utils import sort_games
        self.games = sort_games(new_games, self.list_sort_order)
        
        # Update List
        self.list_widget.clear()
        metrics = QFontMetrics(self.list_widget.font())
        available_width = self.list_widget.width() - 40
        if available_width < 50: available_width = 200 # Default if layout not ready
        
        for g in self.games:
            full_text = f"[{g['score']}] {g['title']}"
            elided_text = metrics.elidedText(full_text, Qt.TextElideMode.ElideRight, available_width)
            
            item = QListWidgetItem(elided_text)
            if g.get('comment'):
                base_path = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
                icon_path = os.path.join(base_path, "assets", "comment.png")
                if os.path.exists(icon_path):
                    item.setIcon(QIcon(icon_path))
            item.setData(Qt.ItemDataRole.UserRole, g)
            self.list_widget.addItem(item)
            
        self.tier_view.update_tiers(new_games, self.tier_sort_order)
        
    def add_game_dialog(self):
        dlg = GameDialog(self)
        if dlg.exec():
            self.refresh_data()
            
    def edit_game_dialog(self):
        items = self.list_widget.selectedItems()
        if len(items) > 1:
            QMessageBox.warning(self, self.texts["msg_warning"], self.texts["msg_edit_multi_warn"])
            return
        if not items:
            QMessageBox.warning(self, self.texts["msg_warning"], self.texts["msg_select_game"])
            return
            
        game_data = items[0].data(Qt.ItemDataRole.UserRole)
        dlg = GameDialog(self, game_data)
        if dlg.exec():
            self.refresh_data()
            
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            self.edit_game_dialog()
        super().keyPressEvent(event)

    def delete_selected_game(self):
        items = self.list_widget.selectedItems()
        if not items:
            return
            
        if len(items) == 1:
            game_data = items[0].data(Qt.ItemDataRole.UserRole)
            confirm_msg = self.texts["msg_confirm_delete"].format(game_data['title'])
        else:
            confirm_msg = self.texts["msg_confirm_delete"].format(f"{len(items)} items")
            
        reply = QMessageBox.question(self, self.texts["msg_delete_title"], confirm_msg,
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                                     
        if reply == QMessageBox.StandardButton.Yes:
            for item in items:
                game_data = item.data(Qt.ItemDataRole.UserRole)
                delete_game(game_data['id'])
            self.refresh_data()
            
    def export_image(self):
        if not self.games:
            return
        file_path, _ = QFileDialog.getSaveFileName(self, self.texts["btn_export"], "", "JPEG Images (*.jpg)")
        if file_path:
            if not file_path.lower().endswith(".jpg"):
                file_path += ".jpg"
            if export_tier_list(self.games, file_path, self.config.get("theme", "dark")):
                QMessageBox.information(self, self.texts["msg_info"], self.texts["msg_export_success"])
            else:
                QMessageBox.warning(self, self.texts["msg_error"], self.texts["msg_export_fail"])
                
    def backup_db(self):
        dest_folder = QFileDialog.getExistingDirectory(self, self.texts["btn_backup"])
        if dest_folder:
            zip_path = backup_data(dest_folder)
            QMessageBox.information(self, self.texts["btn_backup"], self.texts["msg_backup_done"].format(zip_path))
            
    def restore_db(self):
        file_path, _ = QFileDialog.getOpenFileName(self, self.texts["btn_restore"], "", "Zip Files (*.zip)")
        if file_path:
            reply = QMessageBox.warning(self, self.texts["btn_restore"], 
                                         self.texts["msg_restore_warn"],
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                if restore_data(file_path):
                    self.load_settings()
                    self.apply_theme()
                    self.update_ui_texts()
                    self.refresh_data()
                    QMessageBox.information(self, self.texts["msg_info"], self.texts["msg_restore_done"])
                else:
                    QMessageBox.warning(self, self.texts["msg_error"], self.texts["msg_restore_fail"])
