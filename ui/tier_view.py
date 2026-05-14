from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QColorDialog, QMessageBox
from PyQt6.QtCore import Qt, pyqtSignal
from ui.widgets import FlowLayout, GameCard
from core.utils import get_tier_label_and_color, group_games_by_tier, get_contrast_color, load_config, save_config

class ClickableLabel(QLabel):
    clicked = pyqtSignal()
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        elif event.button() == Qt.MouseButton.RightButton:
            # Handle reset in on_label_clicked/mousePressEvent
            self.clicked.emit() 
        event.accept() # Stop bubbling

class TierRow(QWidget):
    def __init__(self, label_text, color, games, is_range=False):
        super().__init__()
        self.label_text = label_text
        self.color = color
        self.games = games
        self.is_range = is_range
        self.init_ui()
        
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 10)
        
        # Left Label
        self.lbl = ClickableLabel(self.label_text)
        self.lbl.setFixedWidth(60)
        self.lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.update_label_style()
        self.lbl.clicked.connect(self.on_label_clicked)
        
        # Right area for cards
        self.cards_area = QWidget()
        self.cards_layout = FlowLayout(self.cards_area)
        
        for g in self.games:
            card = GameCard(g, show_score=self.is_range)
            self.cards_layout.addWidget(card)
            
        layout.addWidget(self.lbl)
        layout.addWidget(self.cards_area)

    def update_label_style(self):
        text_color = get_contrast_color(self.color)
        self.lbl.setStyleSheet(f"background-color: {self.color}; color: {text_color}; font-weight: bold; border-radius: 5px;")

    def on_label_clicked(self):
        main_win = self.window()
        if hasattr(main_win, 'palette_mode') and main_win.palette_mode:
            from PyQt6.QtGui import QCursor
            # Detect which button was pressed via QCursor/QApplication or just by passing event info
            # Since clicked signal doesn't have event, we check if it was right click
            from PyQt6.QtWidgets import QApplication
            is_right = QApplication.mouseButtons() == Qt.MouseButton.RightButton
            
            if is_right:
                # Reset color
                config = load_config()
                if "colors" in config and self.label_text in config["colors"]:
                    del config["colors"][self.label_text]
                    save_config(config)
                    if hasattr(main_win, 'config'):
                        main_win.config = config
                    
                    # Correctly get default color
                    from core.utils import TIER_COLORS, get_tier_label_and_color
                    if "~" in self.label_text:
                        default_color = TIER_COLORS.get(self.label_text, "#78909C")
                    else:
                        try:
                            _, default_color = get_tier_label_and_color(int(self.label_text))
                        except:
                            default_color = "#78909C"
                    
                    self.color = default_color
                    self.update_label_style()
                return

            dlg_title = main_win.texts.get("btn_color_select", "Select Color")
            dialog = QColorDialog(self)
            dialog.setWindowTitle(dlg_title)
            dialog.setOption(QColorDialog.ColorDialogOption.DontUseNativeDialog)
            
            # Apply Fusion style and aggressive styling to override OS defaults
            from PyQt6.QtWidgets import QStyleFactory
            dialog.setStyle(QStyleFactory.create("Fusion"))
            dialog.setAutoFillBackground(True)
            
            theme = main_win.config.get("theme", "dark")
            if theme == "dark":
                dialog.setStyleSheet("""
                    QColorDialog, QWidget { background-color: #1E1E1E !important; color: #E0E0E0 !important; }
                    QPushButton { background-color: #3D3D3D !important; border: 1px solid #555 !important; padding: 2px; }
                    QColorPicker, QColorLuminancePicker { background-color: transparent !important; }
                """)
            else:
                dialog.setStyleSheet("""
                    QColorDialog, QWidget { background-color: #F0F2F5 !important; color: #2C3E50 !important; }
                    QPushButton { background-color: #FFFFFF !important; border: 1px solid #DCDFE6 !important; padding: 2px; }
                """)

            if dialog.exec():
                color = dialog.selectedColor()
                if color.isValid():
                    self.color = color.name()
                    config = load_config()
                    if "colors" not in config: config["colors"] = {}
                    config["colors"][self.label_text] = self.color
                    save_config(config)
                    if hasattr(main_win, 'config'):
                        main_win.config = config
                    self.update_label_style()

class TierView(QScrollArea):
    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.main_widget = QWidget()
        self.rows_layout = QVBoxLayout(self.main_widget)
        self.rows_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setWidget(self.main_widget)
        self.apply_background()

    def apply_background(self):
        config = load_config()
        bg = config.get("bg_color")
        if bg:
            self.setStyleSheet(f"background-color: {bg}; border: none;")
            self.main_widget.setStyleSheet(f"background-color: {bg};")
        else:
            # Default theme handled by main_window apply_theme
            pass

    def mousePressEvent(self, event):
        main_win = self.window()
        if hasattr(main_win, 'palette_mode') and main_win.palette_mode:
            if event.button() == Qt.MouseButton.RightButton:
                # Reset background color
                config = load_config()
                if "bg_color" in config:
                    del config["bg_color"]
                    save_config(config)
                    if hasattr(main_win, 'config'):
                        main_win.config = config
                    self.apply_background()
                    # Trigger main window theme apply to restore default
                    main_win.apply_theme()
                event.accept()
                return

            dlg_title = main_win.texts.get("btn_color_select", "Select Color")
            dialog = QColorDialog(self)
            dialog.setWindowTitle(dlg_title)
            dialog.setOption(QColorDialog.ColorDialogOption.DontUseNativeDialog)
            
            from PyQt6.QtWidgets import QStyleFactory
            dialog.setStyle(QStyleFactory.create("Fusion"))
            dialog.setAutoFillBackground(True)
            
            theme = main_win.config.get("theme", "dark")
            if theme == "dark":
                dialog.setStyleSheet("""
                    QColorDialog, QWidget { background-color: #1E1E1E !important; color: #E0E0E0 !important; }
                    QPushButton { background-color: #3D3D3D !important; border: 1px solid #555 !important; padding: 2px; }
                    QColorPicker, QColorLuminancePicker { background-color: transparent !important; }
                """)
            else:
                dialog.setStyleSheet("""
                    QColorDialog, QWidget { background-color: #F0F2F5 !important; color: #2C3E50 !important; }
                    QPushButton { background-color: #FFFFFF !important; border: 1px solid #DCDFE6 !important; padding: 2px; }
                """)

            if dialog.exec():
                color = dialog.selectedColor()
                if color.isValid():
                    config = load_config()
                    config["bg_color"] = color.name()
                    save_config(config)
                    if hasattr(main_win, 'config'):
                        main_win.config = config
                    self.apply_background()
            event.accept()
            return # Prevent further processing
        super().mousePressEvent(event)
        
    def update_tiers(self, games, order='desc'):
        # Clear existing rows
        while self.rows_layout.count():
            item = self.rows_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        if not games:
            return
            
        tiers, is_range = group_games_by_tier(games, order)
        
        # Sort labels based on order
        sorted_labels = sorted(tiers.keys(), reverse=(order == 'desc'))
        
        for label in sorted_labels:
            row = TierRow(label, tiers[label]['color'], tiers[label]['games'], is_range)
            self.rows_layout.addWidget(row)
            
        self.rows_layout.addStretch()
