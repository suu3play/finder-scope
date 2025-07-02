"""
各種ダイアログユーティリティ
"""
from typing import Optional, Tuple
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QMessageBox, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTextEdit, QCheckBox, QWidget, QProgressDialog,
    QInputDialog, QFileDialog
)
from PySide6.QtGui import QIcon, QFont, QPixmap


class MessageDialog:
    """メッセージダイアログのユーティリティクラス"""
    
    @staticmethod
    def show_info(parent: Optional[QWidget], title: str, message: str) -> None:
        """情報ダイアログを表示"""
        QMessageBox.information(parent, title, message)
    
    @staticmethod
    def show_warning(parent: Optional[QWidget], title: str, message: str) -> None:
        """警告ダイアログを表示"""
        QMessageBox.warning(parent, title, message)
    
    @staticmethod
    def show_error(parent: Optional[QWidget], title: str, message: str) -> None:
        """エラーダイアログを表示"""
        QMessageBox.critical(parent, title, message)
    
    @staticmethod
    def show_question(parent: Optional[QWidget], title: str, message: str, 
                     yes_text: str = "はい", no_text: str = "いいえ") -> bool:
        """確認ダイアログを表示（True: はい, False: いいえ）"""
        reply = QMessageBox.question(
            parent, title, message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes
    
    @staticmethod
    def show_detailed_error(parent: Optional[QWidget], title: str, message: str, 
                          details: str) -> None:
        """詳細付きエラーダイアログを表示"""
        msg_box = QMessageBox(parent)
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setDetailedText(details)
        msg_box.exec()


class ProgressDialog(QProgressDialog):
    """カスタマイズされた進捗ダイアログ"""
    
    def __init__(self, title: str, cancel_text: str = "キャンセル", 
                 minimum: int = 0, maximum: int = 100, parent: Optional[QWidget] = None):
        super().__init__(title, cancel_text, minimum, maximum, parent)
        
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.setAutoClose(True)
        self.setAutoReset(True)
        
        # ウィンドウを中央に配置
        if parent:
            self.move(
                parent.x() + (parent.width() - self.width()) // 2,
                parent.y() + (parent.height() - self.height()) // 2
            )
    
    def update_progress(self, value: int, status: str = "") -> None:
        """進捗とステータスを更新"""
        self.setValue(value)
        if status:
            self.setLabelText(status)


class InputDialog:
    """入力ダイアログのユーティリティクラス"""
    
    @staticmethod
    def get_text(parent: Optional[QWidget], title: str, label: str, 
                default_text: str = "") -> Tuple[str, bool]:
        """テキスト入力ダイアログ（戻り値: (入力テキスト, OK押下)）"""
        text, ok = QInputDialog.getText(parent, title, label, text=default_text)
        return text, ok
    
    @staticmethod
    def get_multiline_text(parent: Optional[QWidget], title: str, label: str, 
                         default_text: str = "") -> Tuple[str, bool]:
        """複数行テキスト入力ダイアログ"""
        text, ok = QInputDialog.getMultiLineText(parent, title, label, text=default_text)
        return text, ok
    
    @staticmethod
    def get_choice(parent: Optional[QWidget], title: str, label: str, 
                  choices: list, default_index: int = 0) -> Tuple[str, bool]:
        """選択肢ダイアログ"""
        choice, ok = QInputDialog.getItem(parent, title, label, choices, default_index, False)
        return choice, ok


class ConfirmReplaceDialog(QDialog):
    """置換確認ダイアログ"""
    
    def __init__(self, search_pattern: str, replace_text: str, file_count: int, 
                 match_count: int, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.search_pattern = search_pattern
        self.replace_text = replace_text
        self.file_count = file_count
        self.match_count = match_count
        
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """UI構築"""
        self.setWindowTitle("置換確認")
        self.setModal(True)
        self.resize(500, 300)
        
        layout = QVBoxLayout(self)
        
        # 確認メッセージ
        message = f"""以下の内容で置換を実行しますか？
        
検索パターン: "{self.search_pattern}"
置換文字列: "{self.replace_text}"

対象ファイル数: {self.file_count} 件
マッチ箇所数: {self.match_count} 箇所"""
        
        message_label = QLabel(message)
        message_label.setFont(QFont("", 10))
        layout.addWidget(message_label)
        
        # バックアップオプション
        self.backup_checkbox = QCheckBox("バックアップファイルを作成する")
        self.backup_checkbox.setChecked(True)
        layout.addWidget(self.backup_checkbox)
        
        # ボタンエリア
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.ok_button = QPushButton("実行")
        self.ok_button.setStyleSheet("QPushButton { font-weight: bold; }")
        self.cancel_button = QPushButton("キャンセル")
        
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        # シグナル接続
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
    
    def create_backup(self) -> bool:
        """バックアップ作成フラグを取得"""
        return self.backup_checkbox.isChecked()


class AboutDialog(QDialog):
    """アプリケーション情報ダイアログ"""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """UI構築"""
        self.setWindowTitle("Finder Scope について")
        self.setModal(True)
        self.resize(400, 300)
        
        layout = QVBoxLayout(self)
        
        # アプリケーション情報
        app_info = """
📁 Finder Scope

ファイル検索・置換ツール

バージョン: 1.0.0
開発: Claude Code Project

主な機能:
• 高速ファイル検索（名前・内容・拡張子・更新日）
• 正規表現対応
• ファイル内容の置換（バックアップ付き）
• CSV/JSON/HTMLエクスポート
• ファイルプレビュー
• 非同期処理による高い応答性

© 2025 Claude Code Project
MIT License
        """.strip()
        
        info_label = QLabel(app_info)
        info_label.setFont(QFont("", 9))
        info_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(info_label)
        
        # 閉じるボタン
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_button = QPushButton("閉じる")
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        
        # シグナル接続
        close_button.clicked.connect(self.accept)


class FileDialogUtils:
    """ファイルダイアログのユーティリティクラス"""
    
    @staticmethod
    def get_save_file(parent: Optional[QWidget], title: str, default_name: str = "", 
                     file_filter: str = "All Files (*.*)") -> Optional[str]:
        """保存ファイル選択ダイアログ"""
        file_path, _ = QFileDialog.getSaveFileName(parent, title, default_name, file_filter)
        return file_path if file_path else None
    
    @staticmethod
    def get_open_file(parent: Optional[QWidget], title: str, 
                     file_filter: str = "All Files (*.*)") -> Optional[str]:
        """開くファイル選択ダイアログ"""
        file_path, _ = QFileDialog.getOpenFileName(parent, title, "", file_filter)
        return file_path if file_path else None
    
    @staticmethod
    def get_folder(parent: Optional[QWidget], title: str, 
                  default_path: str = "") -> Optional[str]:
        """フォルダ選択ダイアログ"""
        folder_path = QFileDialog.getExistingDirectory(parent, title, default_path)
        return folder_path if folder_path else None


# 便利関数
def show_error(parent: Optional[QWidget], message: str, details: str = "") -> None:
    """エラーメッセージを表示"""
    print(f"show_error呼び出し: {message}")  # デバッグ用
    try:
        if details:
            MessageDialog.show_detailed_error(parent, "エラー", message, details)
        else:
            MessageDialog.show_error(parent, "エラー", message)
    except Exception as e:
        print(f"show_errorでエラー: {e}")  # デバッグ用


def show_info(parent: Optional[QWidget], message: str) -> None:
    """情報メッセージを表示"""
    MessageDialog.show_info(parent, "情報", message)


def show_warning(parent: Optional[QWidget], message: str) -> None:
    """警告メッセージを表示"""
    MessageDialog.show_warning(parent, "警告", message)


def confirm(parent: Optional[QWidget], message: str) -> bool:
    """確認ダイアログを表示"""
    return MessageDialog.show_question(parent, "確認", message)