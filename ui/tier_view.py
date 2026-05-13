from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea
from PyQt6.QtCore import Qt
from ui.widgets import FlowLayout, GameCard
from core.utils import get_tier_label_and_color, group_games_by_tier

class TierRow(QWidget):
    def __init__(self, label_text, color, games):
        super().__init__()
        self.label_text = label_text
        self.color = color
        self.games = games
        self.init_ui()
        
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 10)
        
        # Left Label
        self.lbl = QLabel(self.label_text)
        self.lbl.setFixedWidth(60)
        self.lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl.setStyleSheet(f"background-color: {self.color}; color: black; font-weight: bold; border-radius: 5px;")
        
        # Right area for cards
        self.cards_area = QWidget()
        self.cards_layout = FlowLayout(self.cards_area)
        
        for g in self.games:
            card = GameCard(g)
            self.cards_layout.addWidget(card)
            
        layout.addWidget(self.lbl)
        layout.addWidget(self.cards_area)

class TierView(QScrollArea):
    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.setStyleSheet("background-color: #1E1E1E;")
        
        self.main_widget = QWidget()
        self.main_layout = QVBoxLayout(self.main_widget)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setWidget(self.main_widget)
        
    def update_tiers(self, games):
        # Clear layout
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
                
        tiers, sorted_labels = group_games_by_tier(games)
        
        for label in sorted_labels:
            row = TierRow(label, tiers[label]["color"], tiers[label]["games"])
            self.main_layout.addWidget(row)
