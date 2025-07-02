"""
統合テスト
"""
import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch
import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
os.environ['PYTHONPATH'] = str(Path(__file__).parent.parent.parent)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt

from src.models import SearchCriteria, SettingsManager
from src.services import FileSearchService, AsyncSearchService, ExportService
from src.ui import MainWindow


class TestFileSearchIntegration:
    """ファイル検索サービスの統合テスト"""
    
    @classmethod
    def setup_class(cls):
        """テストクラス前の準備"""
        import sys
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication(sys.argv)
    
    def setup_method(self):
        """テストメソッド前の準備"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.service = FileSearchService()
        self.create_test_files()
    
    def teardown_method(self):
        """テストメソッド後のクリーンアップ"""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def create_test_files(self):
        """統合テスト用ファイル作成"""
        # 様々な形式のファイル作成
        test_files = [
            ("document.txt", "This is a test document with important content."),
            ("data.csv", "name,age,city\nJohn,25,Tokyo\nJane,30,Osaka"),
            ("config.json", '{"test": true, "value": 42}'),
            ("script.py", "# Python script\nprint('Hello world')\ntest_var = 'test'"),
            ("readme.md", "# Test Project\nThis is a test README file."),
            ("log.log", "ERROR: Test error occurred\nINFO: System started\nWARN: Warning message"),
            ("large_file.txt", "Large content line.\n" * 10000),  # 大きなファイル
        ]
        
        # メインディレクトリ
        for filename, content in test_files:
            file_path = self.test_dir / filename
            file_path.write_text(content, encoding="utf-8")
        
        # サブディレクトリも作成
        sub_dir = self.test_dir / "subdir"
        sub_dir.mkdir()
        
        sub_files = [
            ("nested.txt", "Nested file content with test keyword."),
            ("hidden.bak", "Backup file content"),
            ("temp.tmp", "Temporary file"),
        ]
        
        for filename, content in sub_files:
            file_path = sub_dir / filename
            file_path.write_text(content, encoding="utf-8")
    
    def test_comprehensive_search(self):
        """包括的検索テスト"""
        # 内容検索
        criteria = SearchCriteria(
            target_folder=self.test_dir,
            content_pattern="test",
            include_subdirectories=True
        )
        
        result = self.service.search_files(criteria)
        
        # 結果検証
        assert result.match_count > 0
        assert len(result.matches) > 0
        
        # 特定のファイルが含まれていることを確認
        filenames = [match.filename for match in result.matches]
        assert "document.txt" in filenames
        assert "script.py" in filenames
        assert "nested.txt" in filenames
    
    def test_extension_filtering(self):
        """拡張子フィルタリングテスト"""
        criteria = SearchCriteria(
            target_folder=self.test_dir,
            file_extensions=[".txt", ".py"],
            include_subdirectories=True
        )
        
        result = self.service.search_files(criteria)
        
        # 結果の拡張子を確認
        for match in result.matches:
            assert match.file_path.suffix in [".txt", ".py"]
    
    def test_date_filtering(self):
        """日付フィルタリングテスト"""
        # 1時間前から現在まで
        date_from = datetime.now() - timedelta(hours=1)
        date_to = datetime.now()
        
        criteria = SearchCriteria(
            target_folder=self.test_dir,
            date_from=date_from,
            date_to=date_to,
            include_subdirectories=True
        )
        
        result = self.service.search_files(criteria)
        
        # 作成したファイルは全て範囲内にあるはず
        assert result.match_count > 0
    
    def test_regex_search(self):
        """正規表現検索テスト"""
        criteria = SearchCriteria(
            target_folder=self.test_dir,
            content_pattern=r"test.*content",
            use_regex=True,
            include_subdirectories=True
        )
        
        result = self.service.search_files(criteria)
        
        # 正規表現にマッチするファイルが見つかるはず
        assert result.match_count > 0
    
    def test_case_sensitive_search(self):
        """大文字小文字を区別する検索テスト"""
        # 大文字小文字を区別しない
        criteria1 = SearchCriteria(
            target_folder=self.test_dir,
            content_pattern="ERROR",
            case_sensitive=False,
            include_subdirectories=True
        )
        
        result1 = self.service.search_files(criteria1)
        
        # 大文字小文字を区別する
        criteria2 = SearchCriteria(
            target_folder=self.test_dir,
            content_pattern="error",  # 小文字
            case_sensitive=True,
            include_subdirectories=True
        )
        
        result2 = self.service.search_files(criteria2)
        
        # 大文字小文字を区別しない方が多く見つかるはず
        assert result1.match_count >= result2.match_count


class TestAsyncSearchIntegration:
    """非同期検索の統合テスト"""
    
    @classmethod
    def setup_class(cls):
        """テストクラス前の準備"""
        import sys
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication(sys.argv)
    
    def setup_method(self):
        """テストメソッド前の準備"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.service = AsyncSearchService()
        self.create_test_files()
    
    def teardown_method(self):
        """テストメソッド後のクリーンアップ"""
        self.service.cleanup()
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def create_test_files(self):
        """テスト用ファイル作成"""
        # 複数のファイルを作成（非同期処理のテスト用）
        for i in range(50):
            file_path = self.test_dir / f"file_{i:03d}.txt"
            content = f"Test file number {i}\nContent with test keyword."
            file_path.write_text(content, encoding="utf-8")
    
    def test_async_search_completion(self):
        """非同期検索完了テスト"""
        criteria = SearchCriteria(
            target_folder=self.test_dir,
            content_pattern="test",
            include_subdirectories=True
        )
        
        # 結果を受信するためのフラグ
        search_completed = False
        search_result = None
        
        def on_search_finished(result):
            nonlocal search_completed, search_result
            search_completed = True
            search_result = result
        
        # 検索開始
        worker = self.service.start_search(criteria)
        worker.search_finished.connect(on_search_finished)
        worker.start()
        
        # 完了まで待機
        worker.wait(10000)  # 最大10秒
        
        # 結果確認
        assert search_completed
        assert search_result is not None
        assert search_result.match_count > 0
    
    def test_async_search_cancellation(self):
        """非同期検索キャンセルテスト"""
        # 重い検索を作成
        criteria = SearchCriteria(
            target_folder=self.test_dir,
            content_pattern=".*",  # 全てにマッチ
            use_regex=True,
            include_subdirectories=True
        )
        
        # 検索開始
        worker = self.service.start_search(criteria)
        worker.start()
        
        # すぐにキャンセル
        self.service.cancel_search()
        
        # 完了まで待機
        worker.wait(5000)
        
        # キャンセルされたことを確認
        assert worker.is_cancelled()


class TestExportIntegration:
    """エクスポート機能の統合テスト"""
    
    def setup_method(self):
        """テストメソッド前の準備"""
        self.export_service = ExportService()
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def teardown_method(self):
        """テストメソッド後のクリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_sample_result(self):
        """サンプル検索結果作成"""
        from src.models import SearchResult, FileMatch, ContentMatch
        
        # テストファイル作成
        test_file = self.temp_dir / "test.txt"
        test_file.write_text("Test content", encoding="utf-8")
        
        # FileMatchオブジェクト作成
        file_match = FileMatch(
            file_path=test_file,
            filename="test.txt",
            folder_path=self.temp_dir,
            modified_date=datetime.now(),
            file_size=12,
            content_matches=[
                ContentMatch(line_number=1, line_content="Test content", matched_text="Test")
            ]
        )
        
        return SearchResult(matches=[file_match])
    
    def test_csv_export(self):
        """CSV出力テスト"""
        result = self.create_sample_result()
        output_path = self.temp_dir / "export_test.csv"
        
        success = self.export_service.export_to_csv(result, output_path)
        
        assert success
        assert output_path.exists()
        
        # CSV内容確認
        content = output_path.read_text(encoding="utf-8")
        assert "test.txt" in content
        assert "Test content" in content
    
    def test_json_export(self):
        """JSON出力テスト"""
        result = self.create_sample_result()
        output_path = self.temp_dir / "export_test.json"
        
        success = self.export_service.export_to_json(result, output_path)
        
        assert success
        assert output_path.exists()
        
        # JSON内容確認
        content = output_path.read_text(encoding="utf-8")
        assert "test.txt" in content
        assert "Test content" in content
    
    def test_html_export(self):
        """HTML出力テスト"""
        result = self.create_sample_result()
        output_path = self.temp_dir / "export_test.html"
        
        success = self.export_service.export_to_html(result, output_path)
        
        assert success
        assert output_path.exists()
        
        # HTML内容確認
        content = output_path.read_text(encoding="utf-8")
        assert "<html>" in content
        assert "test.txt" in content


class TestSettingsIntegration:
    """設定管理の統合テスト"""
    
    def setup_method(self):
        """テストメソッド前の準備"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.settings_file = self.temp_dir / "test_settings.json"
    
    def teardown_method(self):
        """テストメソッド後のクリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_settings_persistence(self):
        """設定の永続化テスト"""
        settings_manager = SettingsManager(self.settings_file)
        
        # 設定を変更
        settings_manager.settings.search.default_use_regex = True
        settings_manager.settings.ui.window_width = 1200
        settings_manager.add_recent_folder("/test/folder")
        settings_manager.add_recent_pattern("test.*pattern")
        
        # 保存
        assert settings_manager.save_settings()
        assert self.settings_file.exists()
        
        # 新しいインスタンスで読み込み
        new_manager = SettingsManager(self.settings_file)
        
        # 設定が保持されていることを確認
        assert new_manager.settings.search.default_use_regex == True
        assert new_manager.settings.ui.window_width == 1200
        assert "/test/folder" in new_manager.get_recent_folders()
        assert "test.*pattern" in new_manager.get_recent_patterns()
    
    def test_settings_export_import(self):
        """設定のエクスポート・インポートテスト"""
        settings_manager = SettingsManager(self.settings_file)
        
        # 設定を変更
        settings_manager.settings.search.max_file_size_mb = 100
        settings_manager.settings.ui.theme = "dark"
        
        # エクスポート
        export_path = self.temp_dir / "exported_settings.json"
        assert settings_manager.export_settings(export_path)
        assert export_path.exists()
        
        # 新しいマネージャーでインポート
        new_manager = SettingsManager()
        assert new_manager.import_settings(export_path)
        
        # 設定が正しくインポートされていることを確認
        assert new_manager.settings.search.max_file_size_mb == 100
        assert new_manager.settings.ui.theme == "dark"


class TestMainWindowIntegration:
    """メインウィンドウの統合テスト"""
    
    @classmethod
    def setup_class(cls):
        """テストクラス前の準備"""
        import sys
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication(sys.argv)
    
    def setup_method(self):
        """テストメソッド前の準備"""
        self.window = MainWindow()
        self.test_dir = Path(tempfile.mkdtemp())
        self.create_test_files()
    
    def teardown_method(self):
        """テストメソッド後のクリーンアップ"""
        self.window.close()
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def create_test_files(self):
        """テスト用ファイル作成"""
        test_file = self.test_dir / "test.txt"
        test_file.write_text("Test content for UI testing", encoding="utf-8")
    
    def test_window_initialization(self):
        """ウィンドウ初期化テスト"""
        assert self.window.windowTitle() == "📁 Finder Scope - ファイル検索・置換ツール"
        assert self.window.search_criteria_widget is not None
        assert self.window.search_result_widget is not None
    
    def test_search_criteria_input(self):
        """検索条件入力テスト"""
        criteria_widget = self.window.search_criteria_widget
        
        # 検索条件を設定
        criteria_widget.folder_path_edit.setText(str(self.test_dir))
        criteria_widget.content_edit.setText("test")
        criteria_widget.include_subdirs_cb.setChecked(True)
        
        # 検索条件を取得
        try:
            criteria = criteria_widget.get_search_criteria()
            assert criteria.target_folder == self.test_dir
            assert criteria.content_pattern == "test"
            assert criteria.include_subdirectories == True
        except ValueError:
            pytest.fail("有効な検索条件でエラーが発生しました")
    
    def test_form_clear(self):
        """フォームクリア機能テスト"""
        criteria_widget = self.window.search_criteria_widget
        
        # フォームに値を設定
        criteria_widget.folder_path_edit.setText(str(self.test_dir))
        criteria_widget.filename_edit.setText("test")
        criteria_widget.content_edit.setText("content")
        
        # クリア実行
        criteria_widget.clear_form()
        
        # クリアされていることを確認
        assert criteria_widget.folder_path_edit.text() == ""
        assert criteria_widget.filename_edit.text() == ""
        assert criteria_widget.content_edit.text() == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])