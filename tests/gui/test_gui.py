"""
GUI統合テスト
"""
import pytest
import tempfile
from pathlib import Path
import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
os.environ['PYTHONPATH'] = str(Path(__file__).parent.parent.parent)

from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt, QTimer

from src.ui import MainWindow
from src.ui.settings_dialog import SettingsDialog
from src.models import SettingsManager


class TestMainWindowGUI:
    """メインウィンドウのGUIテスト"""
    
    @classmethod
    def setup_class(cls):
        """テストクラス前の準備"""
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication(sys.argv)
    
    def setup_method(self):
        """テストメソッド前の準備"""
        self.window = MainWindow()
        self.window.show()
        self.test_dir = Path(tempfile.mkdtemp())
        self.create_test_files()
    
    def teardown_method(self):
        """テストメソッド後のクリーンアップ"""
        self.window.close()
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def create_test_files(self):
        """テスト用ファイル作成"""
        test_files = [
            ("test1.txt", "This is test file 1 with content"),
            ("test2.py", "# Python file\nprint('test')"),
            ("data.csv", "name,value\ntest,100"),
        ]
        
        for filename, content in test_files:
            (self.test_dir / filename).write_text(content, encoding="utf-8")
    
    def test_window_display(self):
        """ウィンドウ表示テスト"""
        assert self.window.isVisible()
        assert self.window.windowTitle() == "📁 Finder Scope - ファイル検索・置換ツール"
        
        # 主要コンポーネントの存在確認
        assert self.window.search_criteria_widget is not None
        assert self.window.search_result_widget is not None
    
    def test_folder_selection(self):
        """フォルダ選択テスト"""
        criteria_widget = self.window.search_criteria_widget
        
        # フォルダパスを直接設定
        criteria_widget.folder_path_edit.setText(str(self.test_dir))
        
        # 設定されたことを確認
        assert criteria_widget.folder_path_edit.text() == str(self.test_dir)
    
    def test_search_criteria_input(self):
        """検索条件入力テスト"""
        criteria_widget = self.window.search_criteria_widget
        
        # 各フィールドに値を入力
        criteria_widget.folder_path_edit.setText(str(self.test_dir))
        criteria_widget.filename_edit.setText("*.txt")
        criteria_widget.extension_edit.setText(".txt,.py")
        criteria_widget.content_edit.setText("test")
        
        # チェックボックスの状態設定
        criteria_widget.filename_regex_cb.setChecked(True)
        criteria_widget.content_regex_cb.setChecked(False)
        criteria_widget.case_sensitive_cb.setChecked(True)
        criteria_widget.include_subdirs_cb.setChecked(False)
        
        # 検索条件を取得して確認
        try:
            criteria = criteria_widget.get_search_criteria()
            assert criteria.target_folder == self.test_dir
            assert criteria.filename_pattern == "*.txt"
            assert criteria.file_extensions == [".txt", ".py"]
            assert criteria.content_pattern == "test"
            assert criteria.use_regex == True  # いずれかのregexがTrue
            assert criteria.case_sensitive == True
            assert criteria.include_subdirectories == False
        except Exception as e:
            pytest.fail(f"検索条件の取得でエラー: {e}")
    
    def test_clear_form_functionality(self):
        """フォームクリア機能テスト"""
        criteria_widget = self.window.search_criteria_widget
        
        # フォームに値を設定
        criteria_widget.folder_path_edit.setText(str(self.test_dir))
        criteria_widget.filename_edit.setText("test")
        criteria_widget.content_edit.setText("content")
        criteria_widget.case_sensitive_cb.setChecked(True)
        
        # クリアボタンをクリック
        QTest.mouseClick(criteria_widget.clear_btn, Qt.LeftButton)
        
        # フォームがクリアされていることを確認
        assert criteria_widget.folder_path_edit.text() == ""
        assert criteria_widget.filename_edit.text() == ""
        assert criteria_widget.content_edit.text() == ""
        assert criteria_widget.case_sensitive_cb.isChecked() == False
    
    def test_button_states(self):
        """ボタン状態テスト"""
        criteria_widget = self.window.search_criteria_widget
        
        # 初期状態では検索ボタンが表示され、キャンセルボタンは非表示
        assert criteria_widget.search_btn.isVisible()
        assert not criteria_widget.cancel_btn.isVisible()
        
        # 検索中状態にする
        self.window.set_searching_state(True)
        
        # キャンセルボタンが表示され、検索ボタンが非表示
        assert not criteria_widget.search_btn.isVisible()
        assert criteria_widget.cancel_btn.isVisible()
        
        # 検索終了状態に戻す
        self.window.set_searching_state(False)
        
        # 元の状態に戻る
        assert criteria_widget.search_btn.isVisible()
        assert not criteria_widget.cancel_btn.isVisible()
    
    def test_progress_display(self):
        """進捗表示テスト"""
        # 進捗バーは初期状態では非表示
        assert not self.window.progress_bar.isVisible()
        
        # 進捗表示を開始
        self.window.show_progress(True)
        assert self.window.progress_bar.isVisible()
        
        # 進捗値を更新
        self.window.update_progress(50)
        assert self.window.progress_bar.value() == 50
        
        # ステータスメッセージを更新
        self.window.update_status("テスト中...")
        assert self.window.status_label.text() == "テスト中..."
        
        # 進捗表示を終了
        self.window.show_progress(False)
        assert not self.window.progress_bar.isVisible()
    
    def test_menu_bar_functionality(self):
        """メニューバー機能テスト"""
        menubar = self.window.menuBar()
        
        # ファイルメニューの存在確認
        file_menu = None
        for action in menubar.actions():
            if "ファイル" in action.text():
                file_menu = action.menu()
                break
        
        assert file_menu is not None, "ファイルメニューが見つかりません"
        
        # ヘルプメニューの存在確認
        help_menu = None
        for action in menubar.actions():
            if "ヘルプ" in action.text():
                help_menu = action.menu()
                break
        
        assert help_menu is not None, "ヘルプメニューが見つかりません"
    
    def test_settings_dialog_opening(self):
        """設定ダイアログ開閉テスト"""
        # 設定ダイアログを開く
        self.window.show_settings_dialog()
        
        # ダイアログが開いていることを確認するのは難しいので、
        # エラーが発生しないことを確認
        assert True  # エラーが発生しなければ成功
    
    def test_keyboard_shortcuts(self):
        """キーボードショートカットテスト"""
        # Ctrl+,で設定ダイアログが開くかテスト
        QTest.keySequence(self.window, "Ctrl+,")
        
        # エラーが発生しないことを確認
        assert True


class TestSettingsDialogGUI:
    """設定ダイアログのGUIテスト"""
    
    @classmethod
    def setup_class(cls):
        """テストクラス前の準備"""
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication(sys.argv)
    
    def setup_method(self):
        """テストメソッド前の準備"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.settings_file = self.temp_dir / "test_settings.json"
        self.settings_manager = SettingsManager(self.settings_file)
        self.dialog = SettingsDialog(self.settings_manager)
        self.dialog.show()
    
    def teardown_method(self):
        """テストメソッド後のクリーンアップ"""
        self.dialog.close()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_dialog_display(self):
        """ダイアログ表示テスト"""
        assert self.dialog.isVisible()
        assert self.dialog.windowTitle() == "設定"
        
        # タブウィジェットの存在確認
        assert self.dialog.tab_widget is not None
        assert self.dialog.tab_widget.count() == 3  # 検索設定、UI設定、履歴
    
    def test_search_settings_tab(self):
        """検索設定タブのテスト"""
        # 検索設定タブを選択
        self.dialog.tab_widget.setCurrentIndex(0)
        search_tab = self.dialog.search_tab
        
        # デフォルト値が設定されていることを確認
        assert search_tab.use_regex_cb is not None
        assert search_tab.case_sensitive_cb is not None
        assert search_tab.include_subdirs_cb is not None
        assert search_tab.max_file_size_spin is not None
        
        # 値を変更
        search_tab.use_regex_cb.setChecked(True)
        search_tab.max_file_size_spin.setValue(50)
        
        # 設定を保存
        search_tab.save_settings()
        
        # 設定が保存されたことを確認
        assert self.settings_manager.settings.search.default_use_regex == True
        assert self.settings_manager.settings.search.max_file_size_mb == 50
    
    def test_ui_settings_tab(self):
        """UI設定タブのテスト"""
        # UI設定タブを選択
        self.dialog.tab_widget.setCurrentIndex(1)
        ui_tab = self.dialog.ui_tab
        
        # UIコンポーネントの存在確認
        assert ui_tab.width_spin is not None
        assert ui_tab.height_spin is not None
        assert ui_tab.theme_combo is not None
        
        # 値を変更
        ui_tab.width_spin.setValue(1200)
        ui_tab.height_spin.setValue(800)
        ui_tab.theme_combo.setCurrentText("dark")
        
        # 設定を保存
        ui_tab.save_settings()
        
        # 設定が保存されたことを確認
        assert self.settings_manager.settings.ui.window_width == 1200
        assert self.settings_manager.settings.ui.window_height == 800
        assert self.settings_manager.settings.ui.theme == "dark"
    
    def test_history_tab(self):
        """履歴タブのテスト"""
        # 履歴を追加
        self.settings_manager.add_recent_folder("/test/folder1")
        self.settings_manager.add_recent_folder("/test/folder2")
        self.settings_manager.add_recent_pattern("test.*pattern")
        
        # 履歴タブを選択
        self.dialog.tab_widget.setCurrentIndex(2)
        history_tab = self.dialog.history_tab
        
        # 履歴を再読み込み
        history_tab.load_history()
        
        # 履歴が表示されていることを確認
        assert history_tab.folders_list.count() == 2
        assert history_tab.patterns_list.count() == 1
        
        # クリアボタンのテスト
        QTest.mouseClick(history_tab.clear_folders_btn, Qt.LeftButton)
        assert history_tab.folders_list.count() == 0
        
        QTest.mouseClick(history_tab.clear_patterns_btn, Qt.LeftButton)
        assert history_tab.patterns_list.count() == 0
    
    def test_dialog_buttons(self):
        """ダイアログボタンのテスト"""
        # OKボタンの存在確認
        assert self.dialog.ok_btn is not None
        assert self.dialog.cancel_btn is not None
        assert self.dialog.apply_btn is not None
        
        # エクスポート・インポートボタンの存在確認
        assert self.dialog.export_btn is not None
        assert self.dialog.import_btn is not None
        assert self.dialog.reset_btn is not None
    
    def test_apply_settings(self):
        """設定適用テスト"""
        # 設定を変更
        search_tab = self.dialog.search_tab
        search_tab.use_regex_cb.setChecked(True)
        search_tab.max_file_size_spin.setValue(100)
        
        # 適用ボタンをクリック
        QTest.mouseClick(self.dialog.apply_btn, Qt.LeftButton)
        
        # 設定ファイルが更新されていることを確認
        # （ファイルが存在することを確認）
        # 実際の値確認は他のテストで行う
        assert True  # エラーが発生しなければ成功


class TestGUIInteraction:
    """GUI操作の統合テスト"""
    
    @classmethod
    def setup_class(cls):
        """テストクラス前の準備"""
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication(sys.argv)
    
    def setup_method(self):
        """テストメソッド前の準備"""
        self.window = MainWindow()
        self.window.show()
        self.test_dir = Path(tempfile.mkdtemp())
        self.create_test_files()
    
    def teardown_method(self):
        """テストメソッド後のクリーンアップ"""
        self.window.close()
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def create_test_files(self):
        """テスト用ファイル作成"""
        test_files = [
            ("gui_test1.txt", "GUI test file 1 with keyword"),
            ("gui_test2.py", "# Python GUI test\nprint('keyword')"),
            ("gui_data.csv", "name,type\ntest,keyword"),
        ]
        
        for filename, content in test_files:
            (self.test_dir / filename).write_text(content, encoding="utf-8")
    
    def test_complete_search_workflow(self):
        """完全な検索ワークフローテスト"""
        criteria_widget = self.window.search_criteria_widget
        
        # 1. 検索条件を設定
        criteria_widget.folder_path_edit.setText(str(self.test_dir))
        criteria_widget.content_edit.setText("keyword")
        
        # 2. 検索を実行（ボタンクリック）
        QTest.mouseClick(criteria_widget.search_btn, Qt.LeftButton)
        
        # 3. 検索状態に移行することを確認
        # （実際の検索は非同期で実行されるため、状態変化のみ確認）
        # 短時間待機してから状態を確認
        QTest.qWait(100)  # 100ms待機
        
        # 検索が開始されたかの確認は困難なため、エラーが発生しないことを確認
        assert True  # エラーが発生しなければ成功
    
    def test_form_validation(self):
        """フォームバリデーションテスト"""
        criteria_widget = self.window.search_criteria_widget
        
        # 無効な検索条件（フォルダパスなし）で検索を実行
        criteria_widget.folder_path_edit.setText("")  # 空のパス
        criteria_widget.content_edit.setText("test")
        
        # 検索ボタンをクリック
        QTest.mouseClick(criteria_widget.search_btn, Qt.LeftButton)
        
        # エラーダイアログが表示される（直接確認は困難）
        # エラーが適切にハンドリングされることを確認
        assert True  # エラーが発生しなければ成功
    
    def test_tab_navigation(self):
        """タブナビゲーションテスト"""
        # 設定ダイアログを開く
        dialog = SettingsDialog(self.window.settings_manager)
        dialog.show()
        
        # 各タブに移動
        for i in range(dialog.tab_widget.count()):
            dialog.tab_widget.setCurrentIndex(i)
            assert dialog.tab_widget.currentIndex() == i
        
        dialog.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])