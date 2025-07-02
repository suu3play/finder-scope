"""
設定ダイアログ
"""
from typing import Optional
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, QLabel, 
    QLineEdit, QSpinBox, QCheckBox, QPushButton, QGroupBox, QComboBox,
    QFileDialog, QFormLayout, QTextEdit, QListWidget, QListWidgetItem
)
from PySide6.QtGui import QFont

from src.models import SettingsManager, AppSettings


class SearchSettingsTab(QWidget):
    """検索設定タブ"""
    
    def __init__(self, settings_manager: SettingsManager, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self) -> None:
        """UI構築"""
        layout = QVBoxLayout(self)
        
        # デフォルト設定グループ
        defaults_group = QGroupBox("デフォルト設定")
        defaults_layout = QFormLayout(defaults_group)
        
        self.use_regex_cb = QCheckBox()
        defaults_layout.addRow("正規表現を使用:", self.use_regex_cb)
        
        self.case_sensitive_cb = QCheckBox()
        defaults_layout.addRow("大文字小文字を区別:", self.case_sensitive_cb)
        
        self.include_subdirs_cb = QCheckBox()
        defaults_layout.addRow("サブディレクトリを含む:", self.include_subdirs_cb)
        
        layout.addWidget(defaults_group)
        
        # パフォーマンス設定グループ
        performance_group = QGroupBox("パフォーマンス設定")
        performance_layout = QFormLayout(performance_group)
        
        self.max_file_size_spin = QSpinBox()
        self.max_file_size_spin.setRange(1, 1000)
        self.max_file_size_spin.setSuffix(" MB")
        performance_layout.addRow("最大ファイルサイズ:", self.max_file_size_spin)
        
        self.max_results_spin = QSpinBox()
        self.max_results_spin.setRange(100, 100000)
        self.max_results_spin.setValue(10000)
        performance_layout.addRow("最大検索結果数:", self.max_results_spin)
        
        layout.addWidget(performance_group)
        
        # 除外設定グループ
        exclusion_group = QGroupBox("除外設定")
        exclusion_layout = QVBoxLayout(exclusion_group)
        
        # 除外拡張子
        exclusion_layout.addWidget(QLabel("除外拡張子（カンマ区切り）:"))
        self.excluded_extensions_edit = QLineEdit()
        self.excluded_extensions_edit.setPlaceholderText(".exe,.dll,.bin,.zip")
        exclusion_layout.addWidget(self.excluded_extensions_edit)
        
        # 除外フォルダ
        exclusion_layout.addWidget(QLabel("除外フォルダ（カンマ区切り）:"))
        self.excluded_folders_edit = QLineEdit()
        self.excluded_folders_edit.setPlaceholderText(".git,__pycache__,node_modules")
        exclusion_layout.addWidget(self.excluded_folders_edit)
        
        layout.addWidget(exclusion_group)
        
        layout.addStretch()
    
    def load_settings(self) -> None:
        """設定を読み込み"""
        search_settings = self.settings_manager.settings.search
        
        self.use_regex_cb.setChecked(search_settings.default_use_regex)
        self.case_sensitive_cb.setChecked(search_settings.default_case_sensitive)
        self.include_subdirs_cb.setChecked(search_settings.default_include_subdirectories)
        self.max_file_size_spin.setValue(search_settings.max_file_size_mb)
        self.max_results_spin.setValue(search_settings.max_results)
        
        self.excluded_extensions_edit.setText(','.join(search_settings.excluded_extensions))
        self.excluded_folders_edit.setText(','.join(search_settings.excluded_folders))
    
    def save_settings(self) -> None:
        """設定を保存"""
        search_settings = self.settings_manager.settings.search
        
        search_settings.default_use_regex = self.use_regex_cb.isChecked()
        search_settings.default_case_sensitive = self.case_sensitive_cb.isChecked()
        search_settings.default_include_subdirectories = self.include_subdirs_cb.isChecked()
        search_settings.max_file_size_mb = self.max_file_size_spin.value()
        search_settings.max_results = self.max_results_spin.value()
        
        # 拡張子とフォルダの解析
        extensions_text = self.excluded_extensions_edit.text().strip()
        search_settings.excluded_extensions = [
            ext.strip() for ext in extensions_text.split(',') if ext.strip()
        ]
        
        folders_text = self.excluded_folders_edit.text().strip()
        search_settings.excluded_folders = [
            folder.strip() for folder in folders_text.split(',') if folder.strip()
        ]


class UISettingsTab(QWidget):
    """UI設定タブ"""
    
    def __init__(self, settings_manager: SettingsManager, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self) -> None:
        """UI構築"""
        layout = QVBoxLayout(self)
        
        # ウィンドウ設定グループ
        window_group = QGroupBox("ウィンドウ設定")
        window_layout = QFormLayout(window_group)
        
        self.width_spin = QSpinBox()
        self.width_spin.setRange(800, 3000)
        window_layout.addRow("幅:", self.width_spin)
        
        self.height_spin = QSpinBox()
        self.height_spin.setRange(600, 2000)
        window_layout.addRow("高さ:", self.height_spin)
        
        self.maximized_cb = QCheckBox()
        window_layout.addRow("最大化で開く:", self.maximized_cb)
        
        layout.addWidget(window_group)
        
        # フォント設定グループ
        font_group = QGroupBox("フォント設定")
        font_layout = QFormLayout(font_group)
        
        self.font_family_combo = QComboBox()
        self.font_family_combo.addItems([
            "Segoe UI", "Arial", "Helvetica", "Verdana", "Tahoma",
            "MS Gothic", "Meiryo UI", "Yu Gothic UI"
        ])
        font_layout.addRow("フォント:", self.font_family_combo)
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 16)
        font_layout.addRow("フォントサイズ:", self.font_size_spin)
        
        layout.addWidget(font_group)
        
        # テーマ設定グループ
        theme_group = QGroupBox("テーマ設定")
        theme_layout = QFormLayout(theme_group)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["default", "dark"])
        theme_layout.addRow("テーマ:", self.theme_combo)
        
        layout.addWidget(theme_group)
        
        # その他設定グループ
        other_group = QGroupBox("その他")
        other_layout = QFormLayout(other_group)
        
        self.show_tooltips_cb = QCheckBox()
        other_layout.addRow("ツールチップを表示:", self.show_tooltips_cb)
        
        self.auto_save_cb = QCheckBox()
        other_layout.addRow("設定を自動保存:", self.auto_save_cb)
        
        layout.addWidget(other_group)
        
        layout.addStretch()
    
    def load_settings(self) -> None:
        """設定を読み込み"""
        ui_settings = self.settings_manager.settings.ui
        
        self.width_spin.setValue(ui_settings.window_width)
        self.height_spin.setValue(ui_settings.window_height)
        self.maximized_cb.setChecked(ui_settings.window_maximized)
        
        # フォント設定
        index = self.font_family_combo.findText(ui_settings.font_family)
        if index >= 0:
            self.font_family_combo.setCurrentIndex(index)
        self.font_size_spin.setValue(ui_settings.font_size)
        
        # テーマ設定
        index = self.theme_combo.findText(ui_settings.theme)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)
        
        self.show_tooltips_cb.setChecked(ui_settings.show_tooltips)
        self.auto_save_cb.setChecked(ui_settings.auto_save_settings)
    
    def save_settings(self) -> None:
        """設定を保存"""
        ui_settings = self.settings_manager.settings.ui
        
        ui_settings.window_width = self.width_spin.value()
        ui_settings.window_height = self.height_spin.value()
        ui_settings.window_maximized = self.maximized_cb.isChecked()
        ui_settings.font_family = self.font_family_combo.currentText()
        ui_settings.font_size = self.font_size_spin.value()
        ui_settings.theme = self.theme_combo.currentText()
        ui_settings.show_tooltips = self.show_tooltips_cb.isChecked()
        ui_settings.auto_save_settings = self.auto_save_cb.isChecked()


class HistoryTab(QWidget):
    """履歴タブ"""
    
    def __init__(self, settings_manager: SettingsManager, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.setup_ui()
        self.load_history()
    
    def setup_ui(self) -> None:
        """UI構築"""
        layout = QVBoxLayout(self)
        
        # 最近使用したフォルダ
        folders_group = QGroupBox("最近使用したフォルダ")
        folders_layout = QVBoxLayout(folders_group)
        
        self.folders_list = QListWidget()
        folders_layout.addWidget(self.folders_list)
        
        folders_buttons = QHBoxLayout()
        self.clear_folders_btn = QPushButton("クリア")
        folders_buttons.addWidget(self.clear_folders_btn)
        folders_buttons.addStretch()
        folders_layout.addLayout(folders_buttons)
        
        layout.addWidget(folders_group)
        
        # 最近使用した検索パターン
        patterns_group = QGroupBox("最近使用した検索パターン")
        patterns_layout = QVBoxLayout(patterns_group)
        
        self.patterns_list = QListWidget()
        patterns_layout.addWidget(self.patterns_list)
        
        patterns_buttons = QHBoxLayout()
        self.clear_patterns_btn = QPushButton("クリア")
        patterns_buttons.addWidget(self.clear_patterns_btn)
        patterns_buttons.addStretch()
        patterns_layout.addLayout(patterns_buttons)
        
        layout.addWidget(patterns_group)
        
        # シグナル接続
        self.clear_folders_btn.clicked.connect(self.clear_folders)
        self.clear_patterns_btn.clicked.connect(self.clear_patterns)
    
    def load_history(self) -> None:
        """履歴を読み込み"""
        # フォルダ履歴
        self.folders_list.clear()
        for folder in self.settings_manager.get_recent_folders():
            self.folders_list.addItem(folder)
        
        # パターン履歴
        self.patterns_list.clear()
        for pattern in self.settings_manager.get_recent_patterns():
            self.patterns_list.addItem(pattern)
    
    def clear_folders(self) -> None:
        """フォルダ履歴をクリア"""
        self.settings_manager.settings.recent_folders.clear()
        self.folders_list.clear()
    
    def clear_patterns(self) -> None:
        """パターン履歴をクリア"""
        self.settings_manager.settings.recent_patterns.clear()
        self.patterns_list.clear()


class SettingsDialog(QDialog):
    """設定ダイアログ"""
    
    def __init__(self, settings_manager: SettingsManager, parent: Optional[QWidget] = None):
        super().__init__(parent)
        print("SettingsDialog初期化開始")  # デバッグ用
        self.settings_manager = settings_manager
        self._dialog_result = None  # ダイアログ結果を保存
        self.setup_ui()
        print("SettingsDialog初期化完了")  # デバッグ用
    
    def setup_ui(self) -> None:
        """UI構築"""
        self.setWindowTitle("設定")
        self.setModal(True)
        self.resize(600, 500)
        
        layout = QVBoxLayout(self)
        
        # タブウィジェット
        self.tab_widget = QTabWidget()
        
        # 各タブを追加
        self.search_tab = SearchSettingsTab(self.settings_manager)
        self.ui_tab = UISettingsTab(self.settings_manager)
        self.history_tab = HistoryTab(self.settings_manager)
        
        self.tab_widget.addTab(self.search_tab, "検索設定")
        self.tab_widget.addTab(self.ui_tab, "UI設定")
        self.tab_widget.addTab(self.history_tab, "履歴")
        
        layout.addWidget(self.tab_widget)
        
        # ボタンエリア
        button_layout = QHBoxLayout()
        
        self.export_btn = QPushButton("設定をエクスポート")
        self.import_btn = QPushButton("設定をインポート")
        self.reset_btn = QPushButton("デフォルトに戻す")
        
        button_layout.addWidget(self.export_btn)
        button_layout.addWidget(self.import_btn)
        button_layout.addWidget(self.reset_btn)
        button_layout.addStretch()
        
        self.ok_btn = QPushButton("OK")
        self.cancel_btn = QPushButton("キャンセル")
        self.apply_btn = QPushButton("適用")
        
        button_layout.addWidget(self.ok_btn)
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.apply_btn)
        
        layout.addLayout(button_layout)
        
        # シグナル接続
        print("設定ダイアログのシグナル接続中...")  # デバッグ用
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        self.apply_btn.clicked.connect(self.apply_settings)
        self.export_btn.clicked.connect(self.export_settings)
        self.import_btn.clicked.connect(self.import_settings)
        self.reset_btn.clicked.connect(self.reset_settings)
        print("設定ダイアログのシグナル接続完了")  # デバッグ用
    
    def accept(self) -> None:
        """OK押下時の処理"""
        try:
            print("設定ダイアログ: OK押下")  # デバッグ用
            self.apply_settings()
            self._dialog_result = QDialog.DialogCode.Accepted
            self.done(QDialog.DialogCode.Accepted)
        except Exception as e:
            print(f"設定ダイアログのOK処理でエラー: {e}")
            self._dialog_result = QDialog.DialogCode.Accepted
            self.done(QDialog.DialogCode.Accepted)  # エラーでも閉じる
    
    def reject(self) -> None:
        """キャンセル押下時の処理"""
        print("設定ダイアログ: キャンセル押下")  # デバッグ用
        self._dialog_result = QDialog.DialogCode.Rejected
        self.done(QDialog.DialogCode.Rejected)
    
    def apply_settings(self) -> None:
        """設定を適用"""
        try:
            print("設定適用開始")  # デバッグ用
            # 各タブの設定を保存
            self.search_tab.save_settings()
            print("検索設定保存完了")
            self.ui_tab.save_settings()
            print("UI設定保存完了")
            
            # 設定ファイルに保存
            if self.settings_manager.save_settings():
                print("設定を保存しました")
            else:
                print("設定の保存に失敗しました")
        except Exception as e:
            print(f"設定適用でエラー: {e}")
    
    def export_settings(self) -> None:
        """設定をエクスポート"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "設定をエクスポート", "finder_scope_settings.json", 
            "JSON Files (*.json)"
        )
        
        if file_path:
            if self.settings_manager.export_settings(Path(file_path)):
                from .dialog_utils import show_info
                show_info(self, f"設定をエクスポートしました:\n{file_path}")
            else:
                from .dialog_utils import show_error
                show_error(self, "設定のエクスポートに失敗しました")
    
    def import_settings(self) -> None:
        """設定をインポート"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "設定をインポート", "", "JSON Files (*.json)"
        )
        
        if file_path:
            if self.settings_manager.import_settings(Path(file_path)):
                # UIに反映
                self.search_tab.load_settings()
                self.ui_tab.load_settings()
                self.history_tab.load_history()
                
                from .dialog_utils import show_info
                show_info(self, f"設定をインポートしました:\n{file_path}")
            else:
                from .dialog_utils import show_error
                show_error(self, "設定のインポートに失敗しました")
    
    def reset_settings(self) -> None:
        """設定をデフォルトに戻す"""
        from .dialog_utils import confirm
        if confirm(self, "設定をデフォルトに戻しますか？\n現在の設定は失われます。"):
            self.settings_manager.reset_to_defaults()
            
            # UIに反映
            self.search_tab.load_settings()
            self.ui_tab.load_settings()
            self.history_tab.load_history()
            
            from .dialog_utils import show_info
            show_info(self, "設定をデフォルトに戻しました")