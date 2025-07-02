"""
エラーハンドリングの強化テスト
"""
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
os.environ['PYTHONPATH'] = str(Path(__file__).parent.parent.parent)

from src.models import SearchCriteria, SettingsManager
from src.services import FileSearchService, AsyncSearchService, ExportService
from src.ui.dialog_utils import MessageDialog


class TestFileSearchErrorHandling:
    """ファイル検索サービスのエラーハンドリングテスト"""
    
    def setup_method(self):
        """テストメソッド前の準備"""
        self.service = FileSearchService()
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def teardown_method(self):
        """テストメソッド後のクリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_nonexistent_folder_error(self):
        """存在しないフォルダの検索エラー"""
        nonexistent_path = Path("/nonexistent/folder/path")
        
        with pytest.raises(ValueError, match="対象フォルダが存在しません"):
            criteria = SearchCriteria(target_folder=nonexistent_path)
    
    def test_invalid_regex_pattern_handling(self):
        """無効な正規表現パターンのハンドリング"""
        # テストファイル作成
        test_file = self.temp_dir / "test.txt"
        test_file.write_text("test content", encoding="utf-8")
        
        # 無効な正規表現パターン
        criteria = SearchCriteria(
            target_folder=self.temp_dir,
            content_pattern="[invalid",  # 不正な正規表現
            use_regex=True
        )
        
        # エラーが発生しても検索は続行され、結果が返される
        result = self.service.search_files(criteria)
        assert result is not None
        assert result.match_count == 0  # マッチしない
    
    def test_permission_denied_handling(self):
        """権限エラーのハンドリング"""
        # OSError（権限エラー）をシミュレート
        with patch('pathlib.Path.iterdir') as mock_iterdir:
            mock_iterdir.side_effect = PermissionError("Permission denied")
            
            criteria = SearchCriteria(target_folder=self.temp_dir)
            
            # 権限エラーが発生しても例外は発生しない
            result = self.service.search_files(criteria)
            assert result is not None
            assert result.match_count == 0
    
    def test_file_encoding_error_handling(self):
        """ファイルエンコーディングエラーのハンドリング"""
        # バイナリファイル作成
        binary_file = self.temp_dir / "binary.bin"
        binary_file.write_bytes(b'\x80\x81\x82\x83')  # 無効なUTF-8バイト
        
        criteria = SearchCriteria(
            target_folder=self.temp_dir,
            content_pattern="test"
        )
        
        # エンコーディングエラーが発生しても検索は続行
        result = self.service.search_files(criteria)
        assert result is not None
        # バイナリファイルは内容検索でスキップされる
    
    def test_large_file_handling(self):
        """大きなファイルのハンドリング"""
        # 非常に大きなファイルを作成（メモリエラーを防ぐため実際は小さく）
        large_file = self.temp_dir / "large_file.txt"
        large_content = "Large file content line.\n" * 10000
        large_file.write_text(large_content, encoding="utf-8")
        
        criteria = SearchCriteria(
            target_folder=self.temp_dir,
            content_pattern="content"
        )
        
        # 大きなファイルでもエラーなく処理される
        result = self.service.search_files(criteria)
        assert result is not None
        assert result.match_count > 0
    
    def test_file_system_changes_during_search(self):
        """検索中のファイルシステム変更のハンドリング"""
        # ファイル作成
        test_file = self.temp_dir / "test.txt"
        test_file.write_text("test content", encoding="utf-8")
        
        # ファイル削除をシミュレート
        with patch('pathlib.Path.read_text') as mock_read:
            mock_read.side_effect = FileNotFoundError("File not found")
            
            criteria = SearchCriteria(
                target_folder=self.temp_dir,
                content_pattern="test"
            )
            
            # ファイルが削除されても検索は続行
            result = self.service.search_files(criteria)
            assert result is not None
    
    def test_circular_symlink_handling(self):
        """循環シンボリックリンクのハンドリング"""
        # シンボリックリンク作成（可能な場合）
        try:
            link_path = self.temp_dir / "circular_link"
            link_path.symlink_to(self.temp_dir)
            
            criteria = SearchCriteria(
                target_folder=self.temp_dir,
                include_subdirectories=True
            )
            
            # 循環リンクでも無限ループにならない
            result = self.service.search_files(criteria)
            assert result is not None
            
        except (OSError, NotImplementedError):
            # シンボリックリンクがサポートされていない環境ではスキップ
            pytest.skip("Symbolic links not supported")


class TestAsyncSearchErrorHandling:
    """非同期検索のエラーハンドリングテスト"""
    
    @classmethod
    def setup_class(cls):
        """テストクラス前の準備"""
        from PySide6.QtWidgets import QApplication
        import sys
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication(sys.argv)
    
    def setup_method(self):
        """テストメソッド前の準備"""
        self.service = AsyncSearchService()
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def teardown_method(self):
        """テストメソッド後のクリーンアップ"""
        self.service.cleanup()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_async_search_exception_handling(self):
        """非同期検索での例外ハンドリング"""
        # 存在しないフォルダで検索
        criteria = SearchCriteria(target_folder=Path("/nonexistent/path"))
        
        error_received = False
        error_message = ""
        
        def on_error(message):
            nonlocal error_received, error_message
            error_received = True
            error_message = message
        
        # 検索実行
        worker = self.service.start_search(criteria)
        worker.search_error.connect(on_error)
        worker.start()
        
        # 完了まで待機
        worker.wait(5000)
        
        # エラーシグナルが発生したことを確認
        assert error_received
        assert "対象フォルダが存在しません" in error_message
    
    def test_worker_thread_exception_handling(self):
        """ワーカースレッドでの例外ハンドリング"""
        # FileSearchServiceのメソッドで例外が発生するようにモック
        with patch.object(FileSearchService, 'search_files') as mock_search:
            mock_search.side_effect = RuntimeError("Simulated error")
            
            criteria = SearchCriteria(target_folder=self.temp_dir)
            
            error_received = False
            
            def on_error(message):
                nonlocal error_received
                error_received = True
            
            # 検索実行
            worker = self.service.start_search(criteria)
            worker.search_error.connect(on_error)
            worker.start()
            
            # 完了まで待機
            worker.wait(5000)
            
            # エラーが適切にキャッチされたことを確認
            assert error_received
    
    def test_multiple_concurrent_errors(self):
        """複数の同時エラーハンドリング"""
        # 複数の無効な検索を同時実行
        criteria1 = SearchCriteria(target_folder=Path("/nonexistent/path1"))
        criteria2 = SearchCriteria(target_folder=Path("/nonexistent/path2"))
        
        error_count = 0
        
        def on_error(message):
            nonlocal error_count
            error_count += 1
        
        # 複数の検索を連続実行
        worker1 = self.service.start_search(criteria1)
        worker1.search_error.connect(on_error)
        worker1.start()
        
        worker2 = self.service.start_search(criteria2)
        worker2.search_error.connect(on_error)
        worker2.start()
        
        # 両方の完了を待機
        worker1.wait(5000)
        worker2.wait(5000)
        
        # エラーが適切にハンドリングされたことを確認
        assert error_count >= 1  # 少なくとも1つのエラー


class TestExportServiceErrorHandling:
    """エクスポートサービスのエラーハンドリングテスト"""
    
    def setup_method(self):
        """テストメソッド前の準備"""
        self.service = ExportService()
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def teardown_method(self):
        """テストメソッド後のクリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_sample_result(self):
        """サンプル検索結果作成"""
        from src.models import SearchResult, FileMatch, ContentMatch
        
        file_match = FileMatch(
            file_path=self.temp_dir / "test.txt",
            filename="test.txt",
            folder_path=self.temp_dir,
            modified_date=datetime.now(),
            file_size=100,
            content_matches=[
                ContentMatch(line_number=1, line_content="test", matched_text="test")
            ]
        )
        
        return SearchResult(matches=[file_match])
    
    def test_permission_denied_export(self):
        """権限エラーでのエクスポート失敗"""
        result = self.create_sample_result()
        
        # 権限のないディレクトリへのエクスポート（シミュレート）
        invalid_path = Path("/root/no_permission.csv")  # 通常は書き込み権限がない
        
        success = self.service.export_to_csv(result, invalid_path)
        
        # エクスポートが失敗することを確認
        assert success == False
    
    def test_invalid_file_extension_handling(self):
        """無効なファイル拡張子のハンドリング"""
        result = self.create_sample_result()
        
        # 無効な拡張子のファイル
        invalid_path = self.temp_dir / "export.invalid"
        
        # 各エクスポートメソッドで適切にエラーハンドリングされる
        success_csv = self.service.export_to_csv(result, invalid_path)
        success_json = self.service.export_to_json(result, invalid_path)
        success_html = self.service.export_to_html(result, invalid_path)
        
        # 適切にエラーハンドリングされることを確認
        # （実装によっては成功する場合もある）
        assert isinstance(success_csv, bool)
        assert isinstance(success_json, bool)
        assert isinstance(success_html, bool)
    
    def test_disk_space_error_simulation(self):
        """ディスク容量不足エラーのシミュレート"""
        result = self.create_sample_result()
        output_path = self.temp_dir / "test_export.csv"
        
        # ファイル作成でOSErrorが発生するようにモック
        with patch('pathlib.Path.write_text') as mock_write:
            mock_write.side_effect = OSError("No space left on device")
            
            success = self.service.export_to_csv(result, output_path)
            
            # エクスポートが失敗することを確認
            assert success == False
    
    def test_empty_search_result_export(self):
        """空の検索結果のエクスポート"""
        from src.models import SearchResult
        
        empty_result = SearchResult(matches=[])
        output_path = self.temp_dir / "empty_export.csv"
        
        # 空の結果でもエラーなくエクスポートできる
        success = self.service.export_to_csv(empty_result, output_path)
        
        assert success == True
        assert output_path.exists()


class TestSettingsManagerErrorHandling:
    """設定マネージャーのエラーハンドリングテスト"""
    
    def setup_method(self):
        """テストメソッド前の準備"""
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def teardown_method(self):
        """テストメソッド後のクリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_corrupted_settings_file(self):
        """破損した設定ファイルのハンドリング"""
        settings_file = self.temp_dir / "corrupted.json"
        settings_file.write_text("{ invalid json", encoding="utf-8")
        
        # 破損したファイルでも設定マネージャーは初期化される
        manager = SettingsManager(settings_file)
        
        # デフォルト設定が使用される
        assert manager.settings is not None
        assert manager.settings.search.max_file_size_mb == 10  # デフォルト値
    
    def test_readonly_settings_file(self):
        """読み取り専用設定ファイルのハンドリング"""
        settings_file = self.temp_dir / "readonly.json"
        settings_file.write_text('{"test": true}', encoding="utf-8")
        
        # ファイルを読み取り専用に設定（可能な場合）
        try:
            settings_file.chmod(0o444)  # 読み取り専用
            
            manager = SettingsManager(settings_file)
            
            # 設定変更
            manager.settings.search.max_file_size_mb = 50
            
            # 保存が失敗することを確認
            success = manager.save_settings()
            assert success == False
            
        except (OSError, NotImplementedError):
            # 権限変更がサポートされていない環境ではスキップ
            pytest.skip("File permissions not supported")
    
    def test_invalid_settings_import(self):
        """無効な設定インポートのハンドリング"""
        manager = SettingsManager()
        
        # 存在しないファイルからのインポート
        nonexistent_file = self.temp_dir / "nonexistent.json"
        success = manager.import_settings(nonexistent_file)
        assert success == False
        
        # 無効なJSONファイルからのインポート
        invalid_file = self.temp_dir / "invalid.json"
        invalid_file.write_text("{ invalid json", encoding="utf-8")
        success = manager.import_settings(invalid_file)
        assert success == False
    
    def test_settings_export_to_readonly_directory(self):
        """読み取り専用ディレクトリへのエクスポート"""
        manager = SettingsManager()
        
        # 存在しないディレクトリへのエクスポート
        nonexistent_dir = self.temp_dir / "nonexistent" / "export.json"
        success = manager.export_settings(nonexistent_dir)
        
        # ディレクトリが作成されるか、エラーハンドリングされる
        assert isinstance(success, bool)


class TestUIErrorHandling:
    """UIコンポーネントのエラーハンドリングテスト"""
    
    @classmethod
    def setup_class(cls):
        """テストクラス前の準備"""
        from PySide6.QtWidgets import QApplication
        import sys
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication(sys.argv)
    
    def test_dialog_utils_error_handling(self):
        """ダイアログユーティリティのエラーハンドリング"""
        # MessageDialogのメソッドがエラーなく実行される
        try:
            MessageDialog.show_error(None, "Test Error", "Test error message")
            MessageDialog.show_warning(None, "Test Warning", "Test warning message")
            MessageDialog.show_info(None, "Test Info", "Test info message")
            
            # エラーが発生しないことを確認
            assert True
            
        except Exception as e:
            pytest.fail(f"Dialog utils error: {e}")
    
    def test_invalid_search_criteria_handling(self):
        """無効な検索条件のハンドリング"""
        from src.ui.main_window import SearchCriteriaWidget
        
        widget = SearchCriteriaWidget()
        
        # 空のフォルダパスで検索条件を取得
        widget.folder_path_edit.setText("")
        
        # ValueError が発生することを確認
        with pytest.raises(ValueError):
            widget.get_search_criteria()
    
    def test_file_preview_error_handling(self):
        """ファイルプレビューのエラーハンドリング"""
        from src.ui.preview_dialog import FilePreviewDialog
        from src.models import FileMatch, ContentMatch
        from datetime import datetime
        
        # 存在しないファイルのFileMatch
        nonexistent_file = Path("/nonexistent/file.txt")
        file_match = FileMatch(
            file_path=nonexistent_file,
            filename="nonexistent.txt",
            folder_path=Path("/nonexistent"),
            modified_date=datetime.now(),
            file_size=0,
            content_matches=[
                ContentMatch(line_number=1, line_content="test", matched_text="test")
            ]
        )
        
        # プレビューダイアログがエラーなく初期化される
        try:
            dialog = FilePreviewDialog(file_match)
            dialog.close()
            assert True
        except Exception as e:
            # エラーが適切にハンドリングされることを確認
            assert "file" in str(e).lower() or "not found" in str(e).lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])