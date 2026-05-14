from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLayout, QSizePolicy
from PyQt6.QtCore import Qt, QPoint, QRect, QSize
from PyQt6.QtGui import QPixmap, QFontMetrics

class FlowLayout(QLayout):
    def __init__(self, parent=None, margin=-1, hSpacing=-1, vSpacing=-1):
        super().__init__(parent)
        self._item_list = []
        if margin >= 0:
            self.setContentsMargins(margin, margin, margin, margin)
        self._h_spacing = hSpacing
        self._v_spacing = vSpacing

    def addItem(self, item):
        self._item_list.append(item)

    def horizontalSpacing(self):
        if self._h_spacing >= 0:
            return self._h_spacing
        else:
            return 10

    def verticalSpacing(self):
        if self._v_spacing >= 0:
            return self._v_spacing
        else:
            return 10

    def count(self):
        return len(self._item_list)

    def itemAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._item_list:
            size = size.expandedTo(item.minimumSize())
        m = self.contentsMargins()
        size += QSize(m.left() + m.right(), m.top() + m.bottom())
        return size

    def _do_layout(self, rect, test_only):
        x, y = rect.x(), rect.y()
        line_height = 0
        
        m = self.contentsMargins()
        effective_rect = rect.adjusted(+m.left(), +m.top(), -m.right(), -m.bottom())
        x = effective_rect.x()
        y = effective_rect.y()
        
        for item in self._item_list:
            wid = item.widget()
            space_x = self.horizontalSpacing()
            space_y = self.verticalSpacing()
            
            next_x = x + item.sizeHint().width() + space_x
            if next_x - space_x > effective_rect.right() and line_height > 0:
                x = effective_rect.x()
                y = y + line_height + space_y
                next_x = x + item.sizeHint().width() + space_x
                line_height = 0
                
            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))
                
            x = next_x
            line_height = max(line_height, item.sizeHint().height())
            
        return y + line_height - rect.y() + m.bottom()


class GameCard(QWidget):
    def __init__(self, game_data, show_score=False):
        super().__init__()
        self.game_data = game_data
        self.show_score = show_score
        self.init_ui()
        
    def init_ui(self):
        self.setFixedSize(130, 200)
        self.setStyleSheet("""
            GameCard {
                background-color: #333;
                border-radius: 5px;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Cover
        self.img_label = QLabel()
        self.img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        path = self.game_data.get('cover_image_path')
        if path:
            pixmap = QPixmap(path).scaled(130, 160, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            self.img_label.setPixmap(pixmap)
        self.img_label.setFixedSize(130, 160)
        
        # Title area
        self.title_area = QWidget()
        self.title_area.setFixedHeight(40)
        self.title_area.setStyleSheet("""
            QWidget {
                background-color: #222; 
                border-bottom-left-radius: 5px; 
                border-bottom-right-radius: 5px;
            }
        """)
        title_layout = QHBoxLayout(self.title_area)
        title_layout.setContentsMargins(2, 2, 2, 2)
        title_layout.setSpacing(2)
        
        if self.show_score:
            self.score_label = QLabel(str(self.game_data['score']))
            self.score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.score_label.setStyleSheet("""
                background-color: #E53935;
                color: #FFFFFF;
                border-radius: 3px;
                font-weight: bold;
                font-size: 10px;
                padding: 1px;
            """)
            self.score_label.setFixedWidth(28)
            title_layout.addWidget(self.score_label)
        
        self.title_label = QLabel()
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setWordWrap(True)
        self.title_label.setStyleSheet("background-color: transparent; color: #FFF; font-size: 11px;")
        
        metrics = QFontMetrics(self.title_label.font())
        available_width = 120 - (30 if self.show_score else 0)
        full_text = self.game_data['title']
        
        # Limit to 2 lines (~available_width * 1.8)
        if metrics.horizontalAdvance(full_text) > available_width * 1.8:
            elided = metrics.elidedText(full_text, Qt.TextElideMode.ElideRight, int(available_width * 1.8))
            self.title_label.setText(elided)
        else:
            self.title_label.setText(full_text)
            
        title_layout.addWidget(self.title_label)
        
        layout.addWidget(self.img_label)
        layout.addWidget(self.title_area)
