"""
メインウィンドウのUI実装
"""
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QDateEdit, QFileDialog, QGroupBox, QHBoxLayout,
    QHeaderView, QLabel, QLineEdit, QMainWindow, QProgressBar, QPushButton,
    QSplitter, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget
)
from PySide6.QtGui import QIcon, QFont

from src.models import SearchCriteria, SearchResult


class SearchCriteriaWidget(QWidget):
    """検索条件設定ウィジェット"""
    
    search_requested = Signal(SearchCriteria)
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setup_ui()
        self.connect_signals()
    
    def setup_ui(self) -> None:
        """UI構築"""
        layout = QVBoxLayout(self)
        
        # 検索設定グループ
        search_group = QGroupBox("検索設定")
        search_layout = QVBoxLayout(search_group)
        
        # 対象フォルダ
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(QLabel("対象フォルダ:"))
        self.folder_path_edit = QLineEdit()
        self.folder_path_edit.setPlaceholderText("検索対象のフォルダパスを選択してください")
        self.folder_browse_btn = QPushButton("参照...")
        folder_layout.addWidget(self.folder_path_edit)
        folder_layout.addWidget(self.folder_browse_btn)
        search_layout.addLayout(folder_layout)
        
        # ファイル名パターン
        filename_layout = QHBoxLayout()
        filename_layout.addWidget(QLabel("ファイル名:"))
        self.filename_edit = QLineEdit()
        self.filename_edit.setPlaceholderText("検索するファイル名パターン")
        self.filename_regex_cb = QCheckBox("正規表現")
        filename_layout.addWidget(self.filename_edit)
        filename_layout.addWidget(self.filename_regex_cb)
        search_layout.addLayout(filename_layout)
        
        # 拡張子
        extension_layout = QHBoxLayout()
        extension_layout.addWidget(QLabel("拡張子:"))
        self.extension_edit = QLineEdit()
        self.extension_edit.setPlaceholderText("例: .txt,.csv,.log (カンマ区切り)")
        extension_layout.addWidget(self.extension_edit)
        search_layout.addLayout(extension_layout)
        
        # 更新日範囲
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("更新日:"))
        self.date_from_edit = QDateEdit()
        self.date_from_edit.setCalendarPopup(True)
        self.date_from_edit.setSpecialValueText("指定なし")
        self.date_from_edit.setDate(self.date_from_edit.minimumDate())
        date_layout.addWidget(self.date_from_edit)
        date_layout.addWidget(QLabel("〜"))
        self.date_to_edit = QDateEdit()
        self.date_to_edit.setCalendarPopup(True)
        self.date_to_edit.setSpecialValueText("指定なし")
        self.date_to_edit.setDate(self.date_to_edit.maximumDate())
        date_layout.addWidget(self.date_to_edit)
        search_layout.addLayout(date_layout)
        
        # 内容検索
        content_layout = QHBoxLayout()
        content_layout.addWidget(QLabel("内容検索:"))
        self.content_edit = QLineEdit()
        self.content_edit.setPlaceholderText("ファイル内容で検索するキーワード")
        self.content_regex_cb = QCheckBox("正規表現")
        content_layout.addWidget(self.content_edit)
        content_layout.addWidget(self.content_regex_cb)
        search_layout.addLayout(content_layout)
        
        # 置換設定
        replace_layout = QHBoxLayout()
        replace_layout.addWidget(QLabel("置換文字列:"))
        self.replace_edit = QLineEdit()
        self.replace_edit.setPlaceholderText("検索結果を置換する文字列（オプション）")
        replace_layout.addWidget(self.replace_edit)
        search_layout.addLayout(replace_layout)
        
        # 検索オプション
        options_layout = QHBoxLayout()
        self.case_sensitive_cb = QCheckBox("大文字小文字を区別")
        self.include_subdirs_cb = QCheckBox("サブディレクトリを含む")
        self.include_subdirs_cb.setChecked(True)  # デフォルトで有効
        options_layout.addWidget(self.case_sensitive_cb)
        options_layout.addWidget(self.include_subdirs_cb)
        search_layout.addLayout(options_layout)
        
        # 実行ボタン
        button_layout = QHBoxLayout()
        self.search_btn = QPushButton("🔍 検索")
        self.search_btn.setStyleSheet("QPushButton { font-weight: bold; padding: 8px; }")
        self.cancel_btn = QPushButton("⏹ キャンセル")
        self.cancel_btn.setStyleSheet("QPushButton { font-weight: bold; padding: 8px; color: red; }")
        self.cancel_btn.setVisible(False)  # 初期は非表示
        self.replace_btn = QPushButton("🔄 置換")
        self.replace_btn.setStyleSheet("QPushButton { font-weight: bold; padding: 8px; }")
        self.clear_btn = QPushButton("❌ クリア")
        button_layout.addWidget(self.search_btn)
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.replace_btn)
        button_layout.addWidget(self.clear_btn)
        button_layout.addStretch()
        search_layout.addLayout(button_layout)
        
        layout.addWidget(search_group)
    
    def connect_signals(self) -> None:
        """シグナル接続"""
        self.folder_browse_btn.clicked.connect(self.browse_folder)
        self.search_btn.clicked.connect(self.on_search_clicked)
        self.cancel_btn.clicked.connect(self.on_cancel_clicked)
        self.replace_btn.clicked.connect(self.on_replace_clicked)
        self.clear_btn.clicked.connect(self.clear_form)
    
    def browse_folder(self) -> None:
        """フォルダ選択ダイアログ"""
        folder_path = QFileDialog.getExistingDirectory(
            self, "検索対象フォルダを選択", self.folder_path_edit.text()
        )
        if folder_path:
            self.folder_path_edit.setText(folder_path)
    
    def on_search_clicked(self) -> None:
        """検索ボタンクリック処理"""
        print("検索ボタンがクリックされました")  # デバッグ用
        try:
            criteria = self.get_search_criteria()
            print(f"検索条件: {criteria}")  # デバッグ用
            self.search_requested.emit(criteria)
        except ValueError as e:
            print(f"検索条件エラー: {e}")  # デバッグ用
            from .dialog_utils import show_error
            show_error(self, f"検索条件に問題があります:\n{e}")
    
    def get_search_criteria(self) -> SearchCriteria:
        """現在の入力から検索条件を構築"""
        folder_path = self.folder_path_edit.text().strip()
        if not folder_path:
            raise ValueError("対象フォルダを選択してください")
        
        # 拡張子の解析
        extensions = []
        if self.extension_edit.text().strip():
            extensions = [
                ext.strip() 
                for ext in self.extension_edit.text().split(",")
                if ext.strip()
            ]
        
        # 更新日範囲の取得
        date_from = None
        date_to = None
        
        if self.date_from_edit.date() != self.date_from_edit.minimumDate():
            date_from = self.date_from_edit.date().toPython()
            from datetime import datetime
            date_from = datetime.combine(date_from, datetime.min.time())
        
        if self.date_to_edit.date() != self.date_to_edit.maximumDate():
            date_to = self.date_to_edit.date().toPython()
            from datetime import datetime, time
            date_to = datetime.combine(date_to, time.max)
        
        return SearchCriteria(
            target_folder=Path(folder_path),
            filename_pattern=self.filename_edit.text().strip() or None,
            file_extensions=extensions,
            date_from=date_from,
            date_to=date_to,
            content_pattern=self.content_edit.text().strip() or None,
            use_regex=self.filename_regex_cb.isChecked() or self.content_regex_cb.isChecked(),
            case_sensitive=self.case_sensitive_cb.isChecked(),
            include_subdirectories=self.include_subdirs_cb.isChecked()
        )
    
    def clear_form(self) -> None:
        """フォームクリア"""
        self.folder_path_edit.clear()
        self.filename_edit.clear()
        self.extension_edit.clear()
        self.content_edit.clear()
        self.replace_edit.clear()
        self.date_from_edit.setDate(self.date_from_edit.minimumDate())
        self.date_to_edit.setDate(self.date_to_edit.maximumDate())
        self.filename_regex_cb.setChecked(False)
        self.content_regex_cb.setChecked(False)
        self.case_sensitive_cb.setChecked(False)
        self.include_subdirs_cb.setChecked(True)
    
    def on_replace_clicked(self) -> None:
        """置換ボタンクリック処理"""
        try:
            criteria = self.get_search_criteria()
            replace_text = self.replace_edit.text().strip()
            
            if not criteria.content_pattern:
                from .dialog_utils import show_warning
                show_warning(self, "置換を実行するには検索キーワードを入力してください")
                return
            
            if not replace_text:
                from .dialog_utils import confirm
                if not confirm(self, "置換文字列が空です。マッチした文字列を削除しますか？"):
                    return
            
            # TODO: 置換機能の実装
            from .dialog_utils import show_info
            show_info(self, f"置換機能は次のフェーズで実装予定です\n検索: '{criteria.content_pattern}'\n置換: '{replace_text}'")
            
        except ValueError as e:
            from .dialog_utils import show_error
            show_error(self, f"置換条件に問題があります:\n{e}")
    
    def on_cancel_clicked(self) -> None:
        """キャンセルボタンクリック処理"""
        # TODO: 検索キャンセル処理の実装
        print("検索キャンセル要求")
        
        # ボタン状態を切り替え
        self.search_btn.setVisible(True)
        self.cancel_btn.setVisible(False)
        self.search_btn.setEnabled(True)


class SearchResultWidget(QWidget):
    """検索結果表示ウィジェット"""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """UI構築"""
        layout = QVBoxLayout(self)
        
        # 結果ヘッダー
        header_layout = QHBoxLayout()
        self.result_label = QLabel("検索結果: 0件")
        self.result_label.setFont(QFont("", 10, QFont.Weight.Bold))
        header_layout.addWidget(self.result_label)
        header_layout.addStretch()
        
        # 操作ボタン
        self.export_btn = QPushButton("📤 CSV出力")
        self.export_json_btn = QPushButton("📋 JSON出力")
        self.export_html_btn = QPushButton("🌐 HTML出力")
        self.preview_btn = QPushButton("👁 プレビュー")
        self.open_btn = QPushButton("🗂 フォルダを開く")
        header_layout.addWidget(self.export_btn)
        header_layout.addWidget(self.export_json_btn)
        header_layout.addWidget(self.export_html_btn)
        header_layout.addWidget(self.preview_btn)
        header_layout.addWidget(self.open_btn)
        
        layout.addLayout(header_layout)
        
        # 結果テーブル
        self.result_table = QTableWidget()
        self.setup_table()
        layout.addWidget(self.result_table)
    
    def setup_table(self) -> None:
        """テーブル設定"""
        headers = ["ファイル名", "パス", "更新日時", "サイズ", "マッチ数"]
        self.result_table.setColumnCount(len(headers))
        self.result_table.setHorizontalHeaderLabels(headers)
        
        # ヘッダー設定
        header = self.result_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)  # ファイル名
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)      # パス
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)  # 更新日時
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)  # サイズ
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)  # マッチ数
        
        # テーブル設定
        self.result_table.setAlternatingRowColors(True)
        self.result_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.result_table.setSortingEnabled(True)
        
        # ダブルクリックでプレビュー表示
        self.result_table.itemDoubleClicked.connect(self.preview_file)
    
    def update_results(self, search_result: SearchResult) -> None:
        """検索結果の更新"""
        self.result_label.setText(f"検索結果: {search_result.match_count}件")
        
        # テーブルクリア
        self.result_table.setRowCount(0)
        
        # 結果を追加
        for i, file_match in enumerate(search_result.matches):
            self.result_table.insertRow(i)
            
            # データ設定
            self.result_table.setItem(i, 0, QTableWidgetItem(file_match.filename))
            self.result_table.setItem(i, 1, QTableWidgetItem(str(file_match.folder_path)))
            self.result_table.setItem(i, 2, QTableWidgetItem(
                file_match.modified_date.strftime("%Y/%m/%d %H:%M:%S")
            ))
            self.result_table.setItem(i, 3, QTableWidgetItem(file_match.size_formatted))
            self.result_table.setItem(i, 4, QTableWidgetItem(str(file_match.match_count)))
    
    def connect_result_signals(self) -> None:
        """検索結果ウィジェットのシグナル接続"""
        self.export_btn.clicked.connect(self.export_csv)
        self.export_json_btn.clicked.connect(self.export_json)
        self.export_html_btn.clicked.connect(self.export_html)
        self.preview_btn.clicked.connect(self.preview_file)
        self.open_btn.clicked.connect(self.open_folder)
    
    def export_csv(self) -> None:
        """CSV出力"""
        if hasattr(self, 'current_search_result'):
            from PySide6.QtWidgets import QFileDialog
            file_path, _ = QFileDialog.getSaveFileName(
                self, "CSV出力", "search_results.csv", "CSV Files (*.csv)"
            )
            if file_path:
                from src.services import ExportService
                export_service = ExportService()
                success = export_service.export_to_csv(self.current_search_result, Path(file_path))
                if success:
                    from .dialog_utils import show_info
                    show_info(self, f"CSV出力が完了しました\n{file_path}")
                else:
                    from .dialog_utils import show_error
                    show_error(self, "CSV出力に失敗しました")
    
    def export_json(self) -> None:
        """JSON出力"""
        if hasattr(self, 'current_search_result'):
            from PySide6.QtWidgets import QFileDialog
            file_path, _ = QFileDialog.getSaveFileName(
                self, "JSON出力", "search_results.json", "JSON Files (*.json)"
            )
            if file_path:
                from src.services import ExportService
                export_service = ExportService()
                success = export_service.export_to_json(self.current_search_result, Path(file_path))
                if success:
                    print(f"JSON出力完了: {file_path}")
                else:
                    print("JSON出力に失敗しました")
    
    def export_html(self) -> None:
        """HTML出力"""
        if hasattr(self, 'current_search_result'):
            from PySide6.QtWidgets import QFileDialog
            file_path, _ = QFileDialog.getSaveFileName(
                self, "HTML出力", "search_results.html", "HTML Files (*.html)"
            )
            if file_path:
                from src.services import ExportService
                export_service = ExportService()
                success = export_service.export_to_html(self.current_search_result, Path(file_path))
                if success:
                    print(f"HTML出力完了: {file_path}")
                else:
                    print("HTML出力に失敗しました")
    
    def preview_file(self) -> None:
        """ファイルプレビュー"""
        current_row = self.result_table.currentRow()
        if current_row >= 0 and hasattr(self, 'current_search_result'):
            file_match = self.current_search_result.matches[current_row]
            
            from .preview_dialog import FilePreviewDialog
            dialog = FilePreviewDialog(file_match, self)
            dialog.exec()
    
    def open_folder(self) -> None:
        """フォルダを開く"""
        current_row = self.result_table.currentRow()
        if current_row >= 0 and hasattr(self, 'current_search_result'):
            file_match = self.current_search_result.matches[current_row]
            folder_path = file_match.folder_path
            
            import os
            import platform
            
            try:
                if platform.system() == "Windows":
                    os.startfile(folder_path)
                elif platform.system() == "Darwin":  # macOS
                    os.system(f"open '{folder_path}'")
                else:  # Linux
                    os.system(f"xdg-open '{folder_path}'")
                print(f"フォルダを開きました: {folder_path}")
            except Exception as e:
                print(f"フォルダを開けませんでした: {e}")


class MainWindow(QMainWindow):
    """メインウィンドウ"""
    
    def __init__(self):
        super().__init__()
        print("MainWindow初期化開始")  # デバッグ用
        self.settings_dialog_shown = False  # 設定ダイアログ表示フラグ
        self.setup_ui()
        self.connect_signals()
        print("MainWindow初期化完了")  # デバッグ用
    
    def setup_ui(self) -> None:
        """UI構築"""
        print("UI構築開始")  # デバッグ用
        self.setWindowTitle("📁 Finder Scope - ファイル検索・置換ツール")
        self.setMinimumSize(1000, 700)
        
        # 設定マネージャー初期化
        print("設定マネージャー初期化中...")  # デバッグ用
        from src.models import SettingsManager
        self.settings_manager = SettingsManager()
        print("設定マネージャー初期化完了")  # デバッグ用
        
        # メニューバー作成
        print("メニューバー作成中...")  # デバッグ用
        self.create_menu_bar()
        print("メニューバー作成完了")  # デバッグ用
        
        # 中央ウィジェット
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # メインレイアウト
        main_layout = QVBoxLayout(central_widget)
        
        # スプリッター（上下分割）
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # 検索条件ウィジェット
        self.search_criteria_widget = SearchCriteriaWidget()
        splitter.addWidget(self.search_criteria_widget)
        
        # 検索結果ウィジェット
        self.search_result_widget = SearchResultWidget()
        self.search_result_widget.connect_result_signals()
        splitter.addWidget(self.search_result_widget)
        
        # 分割比率設定（検索条件:結果 = 1:2）
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        main_layout.addWidget(splitter)
        
        # ステータスバー（進捗表示）
        self.status_widget = QWidget()
        status_layout = QHBoxLayout(self.status_widget)
        status_layout.setContentsMargins(5, 5, 5, 5)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_label = QLabel("準備完了")
        self.status_label.setFont(QFont("", 9))
        
        status_layout.addWidget(self.progress_bar)
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        
        main_layout.addWidget(self.status_widget)
    
    def create_menu_bar(self) -> None:
        """メニューバー作成"""
        menubar = self.menuBar()
        
        # ファイルメニュー
        file_menu = menubar.addMenu("ファイル(&F)")
        
        # 設定メニュー項目
        settings_action = file_menu.addAction("設定(&S)...")
        settings_action.setShortcut("Ctrl+Shift+,")  # ショートカットを変更
        settings_action.triggered.connect(self.show_settings_dialog)
        
        file_menu.addSeparator()
        
        # 終了メニュー項目
        exit_action = file_menu.addAction("終了(&X)")
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        
        # ヘルプメニュー
        help_menu = menubar.addMenu("ヘルプ(&H)")
        
        # バージョン情報メニュー項目
        about_action = help_menu.addAction("Finder Scopeについて(&A)")
        about_action.triggered.connect(self.show_about_dialog)
    
    def show_settings_dialog(self) -> None:
        """設定ダイアログを表示"""
        # 重複表示を防ぐ
        if self.settings_dialog_shown:
            return
        
        try:
            self.settings_dialog_shown = True
            from .settings_dialog import SettingsDialog
            dialog = SettingsDialog(self.settings_manager, self)
            result = dialog.exec()
            print(f"設定ダイアログ結果: {result}")  # デバッグ用
        except Exception as e:
            print(f"設定ダイアログエラー: {e}")
        finally:
            self.settings_dialog_shown = False
    
    def show_about_dialog(self) -> None:
        """バージョン情報ダイアログを表示"""
        from .dialog_utils import AboutDialog
        dialog = AboutDialog(self)
        dialog.exec()
    
    def connect_signals(self) -> None:
        """シグナル接続"""
        self.search_criteria_widget.search_requested.connect(self.on_search_requested)
        self.async_search_service = None
    
    def on_search_requested(self, criteria: SearchCriteria) -> None:
        """検索要求処理"""
        print(f"検索要求: {criteria}")
        
        # 非同期検索サービスで検索実行
        from src.services import AsyncSearchService
        
        if self.async_search_service is None:
            self.async_search_service = AsyncSearchService()
        
        # 検索ワーカーを開始
        worker = self.async_search_service.start_search(criteria)
        
        # シグナル接続
        worker.search_started.connect(self.on_search_started)
        worker.search_finished.connect(self.on_search_finished)
        worker.search_error.connect(self.on_search_error)
        worker.progress_updated.connect(self.on_progress_updated)
        worker.file_processed.connect(self.on_file_processed)
        
        # ワーカー開始
        worker.start()
        
        # UIの状態を検索中に変更
        self.set_searching_state(True)
    
    def on_search_started(self) -> None:
        """検索開始時の処理"""
        self.update_status("検索を開始しています...")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.show_progress(True)
    
    def on_search_finished(self, result) -> None:
        """検索完了時の処理"""
        self.search_result_widget.update_results(result)
        self.search_result_widget.current_search_result = result
        
        self.update_status(f"検索完了: {result.get_summary()}")
        self.show_progress(False)
        self.set_searching_state(False)
        
        print(f"検索完了: {result.get_summary()}")
    
    def on_search_error(self, error_message: str) -> None:
        """検索エラー時の処理"""
        self.update_status(f"検索エラー: {error_message}")
        self.show_progress(False)
        self.set_searching_state(False)
        
        from .dialog_utils import show_error
        show_error(self, f"検索中にエラーが発生しました:\n{error_message}")
    
    def on_progress_updated(self, progress: int, status: str) -> None:
        """進捗更新時の処理"""
        self.progress_bar.setValue(progress)
        self.update_status(status)
    
    def on_file_processed(self, file_path: str) -> None:
        """ファイル処理時の処理"""
        # 必要に応じて処理中のファイル名を表示
        pass
    
    def set_searching_state(self, is_searching: bool) -> None:
        """検索中状態の設定"""
        # 検索条件ウィジェットの状態変更
        search_widget = self.search_criteria_widget
        search_widget.search_btn.setVisible(not is_searching)
        search_widget.cancel_btn.setVisible(is_searching)
        search_widget.search_btn.setEnabled(not is_searching)
        
        # キャンセルボタンのシグナル接続
        if is_searching:
            search_widget.cancel_btn.clicked.connect(self.cancel_search)
    
    def cancel_search(self) -> None:
        """検索キャンセル"""
        if self.async_search_service:
            self.async_search_service.cancel_search()
            self.update_status("検索をキャンセルしました")
            self.show_progress(False)
            self.set_searching_state(False)
    
    def show_progress(self, visible: bool = True) -> None:
        """進捗バー表示制御"""
        self.progress_bar.setVisible(visible)
    
    def update_progress(self, value: int) -> None:
        """進捗更新"""
        self.progress_bar.setValue(value)
    
    def update_status(self, message: str) -> None:
        """ステータスメッセージ更新"""
        self.status_label.setText(message)
    
    def closeEvent(self, event) -> None:
        """ウィンドウクローズ時の処理"""
        # 検索処理を停止
        if self.async_search_service:
            self.async_search_service.cleanup()
        
        super().closeEvent(event)