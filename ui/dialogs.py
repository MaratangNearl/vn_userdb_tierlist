import os
import shutil
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QSpinBox, QSlider, QTextEdit, 
                             QPushButton, QFileDialog, QMessageBox, QWidget)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from core.database import add_game, update_game
from core.vndb_api import VndbFetchThread

class GameDialog(QDialog):
    def __init__(self, parent=None, game_data=None):
        super().__init__(parent)
        self.game_data = game_data
        self.cover_path = game_data['cover_image_path'] if game_data else ""
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("게임 추가" if not self.game_data else "게임 편집")
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
            self.img_label.setText("이미지 없음")
            
        btn_vndb = QPushButton("VNDB API 연동")
        btn_vndb.clicked.connect(self.fetch_vndb)
        
        btn_local = QPushButton("로컬 이미지")
        btn_local.clicked.connect(self.load_local_image)
        
        left_layout.addWidget(self.img_label)
        left_layout.addWidget(btn_vndb)
        left_layout.addWidget(btn_local)
        left_layout.addStretch()
        
        # Right: Form
        right_layout = QVBoxLayout()
        
        # Title
        right_layout.addWidget(QLabel("제목 (필수):"))
        self.title_input = QLineEdit()
        right_layout.addWidget(self.title_input)
        
        # VNDB URL
        right_layout.addWidget(QLabel("VNDB 주소 또는 ID:"))
        self.vndb_input = QLineEdit()
        right_layout.addWidget(self.vndb_input)
        
        # Score
        right_layout.addWidget(QLabel("평점 (0~100):"))
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
        right_layout.addWidget(QLabel("코멘트:"))
        self.comment_input = QTextEdit()
        right_layout.addWidget(self.comment_input)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("저장")
        btn_save.clicked.connect(self.save_data)
        btn_cancel = QPushButton("취소")
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
            QMessageBox.warning(self, "경고", "VNDB 주소나 ID를 입력해주세요.")
            return
            
        self.thread = VndbFetchThread(url)
        self.thread.finished.connect(self.on_vndb_success)
        self.thread.error.connect(self.on_vndb_error)
        self.thread.start()
        
    def on_vndb_success(self, title, image_path):
        if not self.title_input.text():
            self.title_input.setText(title)
        self.cover_path = image_path
        pixmap = QPixmap(image_path).scaled(150, 220, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
        self.img_label.setPixmap(pixmap)
        QMessageBox.information(self, "성공", "VNDB에서 정보를 성공적으로 불러왔습니다.")
        
    def on_vndb_error(self, err_msg):
        QMessageBox.warning(self, "오류", err_msg)
        
    def load_local_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "이미지 선택", "", "Images (*.png *.jpg *.jpeg)")
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
            QMessageBox.warning(self, "경고", "제목을 입력해주세요.")
            return
            
        score = self.score_spin.value()
        comment = self.comment_input.toPlainText().strip()
        vndb_url = self.vndb_input.text().strip()
        
        if self.game_data:
            update_game(self.game_data['id'], title, score, comment, vndb_url, self.cover_path)
        else:
            add_game(title, score, comment, vndb_url, self.cover_path)
            
        self.accept()
