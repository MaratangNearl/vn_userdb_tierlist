from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QSplitter, QListWidget, QPushButton, QToolBar,
                             QMessageBox, QFileDialog, QListWidgetItem, QSizePolicy)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QIcon, QDesktopServices
from core.database import get_all_games, delete_game
from core.utils import export_tier_list, backup_data, restore_data
from ui.tier_view import TierView
from ui.dialogs import GameDialog
import os
import sys

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("비주얼 노벨 티어리스트")
        self.resize(1280, 800)
        
        self.games = []
        self.init_ui()
        self.refresh_data()
        
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left Panel (List)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self.edit_game_dialog)
        left_layout.addWidget(self.list_widget)
        
        # Right Panel (Tier View)
        self.tier_view = TierView()
        
        splitter.addWidget(left_widget)
        splitter.addWidget(self.tier_view)
        splitter.setSizes([300, 980])
        
        main_layout.addWidget(splitter)
        
        # Toolbar
        toolbar = QToolBar()
        self.addToolBar(Qt.ToolBarArea.BottomToolBarArea, toolbar)
        
        btn_add = QPushButton("추가")
        btn_add.clicked.connect(self.add_game_dialog)
        toolbar.addWidget(btn_add)
        
        btn_edit = QPushButton("편집")
        btn_edit.clicked.connect(self.edit_game_dialog)
        toolbar.addWidget(btn_edit)
        
        btn_del = QPushButton("삭제")
        btn_del.clicked.connect(self.delete_selected_game)
        toolbar.addWidget(btn_del)
        
        toolbar.addSeparator()
        
        btn_export = QPushButton("이미지 내보내기")
        btn_export.clicked.connect(self.export_image)
        toolbar.addWidget(btn_export)
        
        btn_backup = QPushButton("백업")
        btn_backup.clicked.connect(self.backup_db)
        toolbar.addWidget(btn_backup)
        
        btn_restore = QPushButton("복원")
        btn_restore.clicked.connect(self.restore_db)
        toolbar.addWidget(btn_restore)
        
        # Spacer
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)
        
        # GitHub Button
        btn_github = QPushButton(" GitHub")
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        icon_path = os.path.join(base_path, "assets", "github.png")
        btn_github.setIcon(QIcon(icon_path))
        btn_github.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://github.com/MaratangNearl/vn_userdb_tierlist")))
        toolbar.addWidget(btn_github)
        
    def refresh_data(self):
        self.games = get_all_games()
        
        # Update List
        self.list_widget.clear()
        for g in self.games:
            item = QListWidgetItem(f"[{g['score']}] {g['title']}")
            item.setData(Qt.ItemDataRole.UserRole, g)
            self.list_widget.addItem(item)
            
        # Update Tier View
        self.tier_view.update_tiers(self.games)
        
    def add_game_dialog(self):
        dlg = GameDialog(self)
        if dlg.exec():
            self.refresh_data()
            
    def edit_game_dialog(self):
        item = self.list_widget.currentItem()
        if not item:
            QMessageBox.warning(self, "경고", "편집할 게임을 선택하세요.")
            return
            
        game_data = item.data(Qt.ItemDataRole.UserRole)
        dlg = GameDialog(self, game_data)
        if dlg.exec():
            self.refresh_data()
            
    def delete_selected_game(self):
        item = self.list_widget.currentItem()
        if not item:
            QMessageBox.warning(self, "경고", "삭제할 게임을 선택하세요.")
            return
            
        game_data = item.data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(self, "확인", f"'{game_data['title']}'을(를) 삭제하시겠습니까?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                                     
        if reply == QMessageBox.StandardButton.Yes:
            delete_game(game_data['id'])
            self.refresh_data()
            
    def export_image(self):
        if not self.games:
            QMessageBox.warning(self, "경고", "내보낼 데이터가 없습니다.")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(self, "이미지 내보내기", "", "JPEG Images (*.jpg)")
        if file_path:
            if not file_path.lower().endswith(".jpg"):
                file_path += ".jpg"
            if export_tier_list(self.games, file_path):
                QMessageBox.information(self, "성공", "이미지를 성공적으로 내보냈습니다.")
            else:
                QMessageBox.warning(self, "오류", "이미지 내보내기 실패.")
                
    def backup_db(self):
        dest_folder = QFileDialog.getExistingDirectory(self, "백업 폴더 선택")
        if dest_folder:
            zip_path = backup_data(dest_folder)
            QMessageBox.information(self, "백업 완료", f"백업 파일이 생성되었습니다:\n{zip_path}")
            
    def restore_db(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "복원 파일 선택", "", "Zip Files (*.zip)")
        if file_path:
            reply = QMessageBox.warning(self, "데이터 덮어쓰기 경고", 
                                        "현재 데이터를 덮어씁니다. 진행하시겠습니까?",
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                if restore_data(file_path):
                    self.refresh_data()
                    QMessageBox.information(self, "복원 완료", "데이터가 복원되었습니다.")
                else:
                    QMessageBox.warning(self, "오류", "복원 중 오류가 발생했습니다.")
