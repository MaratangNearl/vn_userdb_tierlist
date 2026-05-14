import os
import shutil
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QSpinBox, QSlider, QTextEdit, 
                             QPushButton, QFileDialog, QMessageBox, QWidget, 
                             QFormLayout, QComboBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from core.database import add_game, update_game
from core.vndb_api import VndbFetchThread
from core.utils import load_config, save_config
from ui.translations import TRANSLATIONS

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = load_config()
        self.lang = self.config.get("language", "한국어")
        self.texts = TRANSLATIONS.get(self.lang, TRANSLATIONS["한국어"])
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(self.texts["btn_settings"])
        self.setFixedWidth(400)
        layout = QVBoxLayout(self)
        
        form = QFormLayout()
        
        # Language
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(TRANSLATIONS.keys())
        self.lang_combo.setCurrentText(self.lang)
        form.addRow(self.texts["settings_lang"], self.lang_combo)
        
        # Title Language
        self.title_combo = QComboBox()
        self.title_combo.addItem(self.texts["settings_title_original"], "original")
        self.title_combo.addItem(self.texts["settings_title_en"], "en")
        
        index = self.title_combo.findData(self.config.get("title_lang", "original"))
        if index >= 0:
            self.title_combo.setCurrentIndex(index)
        
        form.addRow(self.texts["settings_title_lang"], self.title_combo)
        
        layout.addLayout(form)
        
        # Copyright
        layout.addWidget(QLabel(f"<b>{self.texts['settings_copyright']}</b>"))
        self.copy_label = QLabel(self.texts["copyright_text"])
        self.copy_label.setWordWrap(True)
        self.copy_label.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(self.copy_label)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_save = QPushButton(self.texts["btn_save"])
        btn_save.clicked.connect(self.save_settings)
        btn_cancel = QPushButton(self.texts["btn_cancel"])
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

    def save_settings(self):
        self.config["language"] = self.lang_combo.currentText()
        self.config["title_lang"] = self.title_combo.currentData()
        save_config(self.config)
        self.accept()

class GameDialog(QDialog):
    def __init__(self, parent=None, game_data=None):
        super().__init__(parent)
        self.game_data = game_data
        self.cover_path = game_data['cover_image_path'] if game_data else ""
        
        config = load_config()
        self.lang = config.get("language", "한국어")
        self.texts = TRANSLATIONS.get(self.lang, TRANSLATIONS["한국어"])
        
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(self.texts["btn_add"] if not self.game_data else self.texts["btn_edit"])
        self.resize(500, 400)
        
        main_layout = QHBoxLayout(self)
        
        # Left: Image
        left_layout = QVBoxLayout()
        self.img_label = QLabel()
        self.img_label.setFixedSize(150, 220)
        self.img_label.setStyleSheet("background-color: #333; border: 1px solid #555;")
        self.img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if self.cover_path and os.path.exists(self.cover_path):
            pixmap = QPixmap(self.cover_path).scaled(150, 220, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            self.img_label.setPixmap(pixmap)
        else:
            self.img_label.setText(self.texts["label_no_img"])
            
        btn_vndb = QPushButton(self.texts["btn_vndb_fetch"])
        btn_vndb.clicked.connect(self.fetch_vndb)
        
        btn_local = QPushButton(self.texts["btn_local_img"])
        btn_local.clicked.connect(self.load_local_image)
        
        left_layout.addWidget(self.img_label)
        left_layout.addWidget(btn_vndb)
        left_layout.addWidget(btn_local)
        left_layout.addStretch()
        
        # Right: Form
        right_layout = QVBoxLayout()
        
        # Title
        right_layout.addWidget(QLabel(self.texts["label_title"]))
        self.title_input = QLineEdit()
        right_layout.addWidget(self.title_input)
        
        # VNDB URL
        right_layout.addWidget(QLabel(self.texts["label_vndb"]))
        self.vndb_input = QLineEdit()
        right_layout.addWidget(self.vndb_input)
        
        # Score
        right_layout.addWidget(QLabel(self.texts["label_score"]))
        score_layout = QHBoxLayout()
        self.score_slider = QSlider(Qt.Orientation.Horizontal)
        self.score_slider.setRange(0, 100)
        self.score_spin = QSpinBox()
        self.score_spin.setRange(0, 100)
        
        self.score_slider.valueChanged.connect(self.score_spin.setValue)
        self.score_spin.valueChanged.connect(self.score_slider.setValue)
        
        score_layout.addWidget(self.score_slider)
        score_layout.addWidget(self.score_spin)
        right_layout.addLayout(score_layout)
        
        # Comment
        right_layout.addWidget(QLabel(self.texts["label_comment"]))
        self.comment_input = QTextEdit()
        right_layout.addWidget(self.comment_input)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_save = QPushButton(self.texts["btn_save"])
        btn_save.clicked.connect(self.save_data)
        btn_cancel = QPushButton(self.texts["btn_cancel"])
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)
        
        right_layout.addLayout(btn_layout)
        
        main_layout.addLayout(left_layout)
        main_layout.addLayout(right_layout)
        
        # Load data if editing
        if self.game_data:
            self.title_input.setText(self.game_data['title'])
            self.vndb_input.setText(self.game_data['vndb_url'])
            self.score_spin.setValue(self.game_data['score'])
            self.comment_input.setPlainText(self.game_data['comment'])

    def fetch_vndb(self):
        url = self.vndb_input.text().strip()
        if not url:
            QMessageBox.warning(self, self.texts["msg_warning"], self.texts["msg_vndb_empty"])
            return
            
        self.thread = VndbFetchThread(url)
        self.thread.finished.connect(self.on_vndb_success)
        self.thread.error.connect(self.on_vndb_error)
        self.thread.start()
        
    def on_vndb_success(self, title, alttitle, image_path):
        config = load_config()
        title_lang = config.get("title_lang", "original")
        
        # Use alttitle if available and requested
        final_title = alttitle if title_lang == "original" and alttitle else title
        
        if not self.title_input.text():
            self.title_input.setText(final_title)
        
        if image_path:
            self.cover_path = image_path
            pixmap = QPixmap(image_path).scaled(150, 220, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            self.img_label.setPixmap(pixmap)
        
        QMessageBox.information(self, self.texts["msg_info"], self.texts["msg_vndb_success"])
        
    def on_vndb_error(self, err_msg):
        QMessageBox.warning(self, self.texts["msg_error"], err_msg)
        
    def load_local_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, self.texts["btn_local_img"], "", "Images (*.png *.jpg *.jpeg)")
        if file_path:
            # Copy to data/covers
            os.makedirs(os.path.join("data", "covers"), exist_ok=True)
            dest_path = os.path.join("data", "covers", os.path.basename(file_path))
            shutil.copy(file_path, dest_path)
            self.cover_path = dest_path
            
            pixmap = QPixmap(self.cover_path).scaled(150, 220, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            self.img_label.setPixmap(pixmap)

    def save_data(self):
        title = self.title_input.text().strip()
        if not title:
            QMessageBox.warning(self, self.texts["msg_warning"], self.texts["msg_title_empty"])
            return
            
        # Duplicate check
        from core.database import get_all_games
        all_games = get_all_games()
        for g in all_games:
            if g['title'] == title:
                if not self.game_data or g['id'] != self.game_data['id']:
                    QMessageBox.warning(self, self.texts["msg_warning"], self.texts["msg_title_exists"])
                    return
            
        score = self.score_spin.value()
        comment = self.comment_input.toPlainText().strip()
        vndb_url = self.vndb_input.text().strip()
        
        if self.game_data:
            update_game(self.game_data['id'], title, score, comment, vndb_url, self.cover_path)
        else:
            add_game(title, score, comment, vndb_url, self.cover_path)
            
        self.accept()
