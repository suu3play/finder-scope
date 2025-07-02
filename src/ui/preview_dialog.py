"""
ファイルプレビューダイアログ
"""
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QSplitter, QListWidget, QListWidgetItem,
    QGroupBox, QScrollArea, QWidget, QFrame
)
from PySide6.QtGui import QFont, QTextCharFormat, QTextCursor

from src.models import FileMatch, ContentMatch


class ContentMatchWidget(QWidget):
    """コンテンツマッチ表示ウィジェット"""
    
    def __init__(self, content_match: ContentMatch, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.content_match = content_match
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """UI構築"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # マッチ情報ヘッダー
        header_layout = QHBoxLayout()
        line_label = QLabel(f"行 {self.content_match.line_number}:")
        line_label.setFont(QFont("", 9, QFont.Weight.Bold))
        header_layout.addWidget(line_label)
        header_layout.addStretch()
        
        position_label = QLabel(f"位置: {self.content_match.start_position}-{self.content_match.end_position}")
        position_label.setFont(QFont("", 8))
        position_label.setStyleSheet("color: #666;")
        header_layout.addWidget(position_label)
        
        layout.addLayout(header_layout)
        
        # マッチ内容表示
        content_label = QLabel(self.content_match.context_preview)
        content_label.setFont(QFont("Consolas, Monaco, monospace", 9))
        content_label.setWordWrap(True)
        content_label.setStyleSheet("""
            QLabel {
                background-color: #ffffcc;
                border: 1px solid #ddd;
                padding: 5px;
                border-radius: 3px;
            }
        """)
        layout.addWidget(content_label)
        
        # 区切り線
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)


class FilePreviewDialog(QDialog):
    """ファイルプレビューダイアログ"""
    
    def __init__(self, file_match: FileMatch, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.file_match = file_match
        self.setup_ui()
        self.load_file_content()
    
    def setup_ui(self) -> None:
        """UI構築"""
        self.setWindowTitle(f"ファイルプレビュー - {self.file_match.filename}")
        self.setModal(True)
        self.resize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # ファイル情報ヘッダー
        info_group = QGroupBox("ファイル情報")
        info_layout = QVBoxLayout(info_group)
        
        # ファイル詳細
        details = [
            f"ファイル名: {self.file_match.filename}",
            f"パス: {self.file_match.file_path}",
            f"サイズ: {self.file_match.size_formatted}",
            f"更新日時: {self.file_match.modified_date.strftime('%Y/%m/%d %H:%M:%S')}",
            f"マッチ数: {self.file_match.match_count} 箇所"
        ]
        
        for detail in details:
            label = QLabel(detail)
            label.setFont(QFont("", 9))
            info_layout.addWidget(label)
        
        layout.addWidget(info_group)
        
        # メインコンテンツエリア
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左側: マッチ一覧
        if self.file_match.matches:
            matches_group = QGroupBox(f"マッチ一覧 ({len(self.file_match.matches)}件)")
            matches_layout = QVBoxLayout(matches_group)
            
            # スクロールエリア
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_widget = QWidget()
            scroll_layout = QVBoxLayout(scroll_widget)
            
            for content_match in self.file_match.matches:
                match_widget = ContentMatchWidget(content_match)
                scroll_layout.addWidget(match_widget)
            
            scroll_layout.addStretch()
            scroll_area.setWidget(scroll_widget)
            matches_layout.addWidget(scroll_area)
            
            splitter.addWidget(matches_group)
        
        # 右側: ファイル内容表示
        content_group = QGroupBox("ファイル内容")
        content_layout = QVBoxLayout(content_group)
        
        self.content_text = QTextEdit()
        self.content_text.setFont(QFont("Consolas, Monaco, monospace", 9))
        self.content_text.setReadOnly(True)
        content_layout.addWidget(self.content_text)
        
        splitter.addWidget(content_group)
        
        # 分割比率設定
        if self.file_match.matches:
            splitter.setStretchFactor(0, 1)
            splitter.setStretchFactor(1, 2)
        
        layout.addWidget(splitter)
        
        # ボタンエリア
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.open_file_btn = QPushButton("📝 外部エディタで開く")
        self.open_folder_btn = QPushButton("🗂 フォルダを開く")
        self.close_btn = QPushButton("閉じる")
        
        button_layout.addWidget(self.open_file_btn)
        button_layout.addWidget(self.open_folder_btn)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
        
        # シグナル接続
        self.open_file_btn.clicked.connect(self.open_file)
        self.open_folder_btn.clicked.connect(self.open_folder)
        self.close_btn.clicked.connect(self.accept)
    
    def load_file_content(self) -> None:
        """ファイル内容を読み込み"""
        try:
            with self.file_match.file_path.open('r', encoding='utf-8') as f:
                content = f.read()
            
            self.content_text.setPlainText(content)
            
            # マッチ箇所をハイライト
            if self.file_match.matches:
                self.highlight_matches()
                
        except UnicodeDecodeError:
            self.content_text.setPlainText("※ バイナリファイルまたは非対応エンコーディングのため表示できません")
        except Exception as e:
            self.content_text.setPlainText(f"※ ファイル読み込みエラー: {e}")
    
    def highlight_matches(self) -> None:
        """マッチ箇所をハイライト"""
        cursor = self.content_text.textCursor()
        
        # ハイライト形式
        highlight_format = QTextCharFormat()
        highlight_format.setBackground(Qt.GlobalColor.yellow)
        highlight_format.setForeground(Qt.GlobalColor.black)
        
        # 各マッチをハイライト
        for content_match in self.file_match.matches:
            # 行番号から位置を計算
            document = self.content_text.document()
            block = document.findBlockByLineNumber(content_match.line_number - 1)
            
            if block.isValid():
                start_pos = block.position() + content_match.start_position
                end_pos = block.position() + content_match.end_position
                
                cursor.setPosition(start_pos)
                cursor.setPosition(end_pos, QTextCursor.MoveMode.KeepAnchor)
                cursor.setCharFormat(highlight_format)
    
    def open_file(self) -> None:
        """外部エディタでファイルを開く"""
        import os
        import platform
        
        try:
            file_path = str(self.file_match.file_path)
            
            if platform.system() == "Windows":
                os.startfile(file_path)
            elif platform.system() == "Darwin":  # macOS
                os.system(f"open '{file_path}'")
            else:  # Linux
                os.system(f"xdg-open '{file_path}'")
                
            print(f"ファイルを開きました: {file_path}")
            
        except Exception as e:
            print(f"ファイルを開けませんでした: {e}")
    
    def open_folder(self) -> None:
        """フォルダを開く"""
        import os
        import platform
        
        try:
            folder_path = str(self.file_match.folder_path)
            
            if platform.system() == "Windows":
                os.startfile(folder_path)
            elif platform.system() == "Darwin":  # macOS
                os.system(f"open '{folder_path}'")
            else:  # Linux
                os.system(f"xdg-open '{folder_path}'")
                
            print(f"フォルダを開きました: {folder_path}")
            
        except Exception as e:
            print(f"フォルダを開けませんでした: {e}")