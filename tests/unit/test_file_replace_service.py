"""
ファイル置換サービスのユニットテスト
"""
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from datetime import datetime

from src.models import ReplaceOperation, FileMatch
from src.services import FileReplaceService


class TestFileReplaceService:
    """FileReplaceServiceのテスト"""
    
    def setup_method(self):
        """テストメソッド前の準備"""
        self.service = FileReplaceService()
    
    def test_simple_replacement(self):
        """シンプルな文字列置換のテスト"""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # テストファイル作成
            test_file = temp_path / "test.txt"
            test_file.write_text("Hello world! This is a test world.")
            
            # FileMatchオブジェクト作成
            file_match = FileMatch(
                file_path=test_file,
                filename="test.txt",
                folder_path=temp_path,
                modified_date=datetime.now(),
                file_size=test_file.stat().st_size
            )
            
            # 置換操作設定
            operation = ReplaceOperation(
                search_pattern="world",
                replace_text="universe",
                use_regex=False,
                case_sensitive=True,
                create_backup=False
            )
            operation.add_target_file(file_match)
            
            # 置換実行
            result = self.service.replace(operation)
            
            # 結果確認
            assert result.success_count == 1
            assert result.error_count == 0
            assert result.total_replacements == 2
            
            # ファイル内容確認
            new_content = test_file.read_text()
            assert "Hello universe! This is a test universe." == new_content
    
    def test_regex_replacement(self):
        """正規表現置換のテスト"""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # テストファイル作成
            test_file = temp_path / "test.txt"
            test_file.write_text("Date: 2025-06-27\nAnother date: 2025-12-31")
            
            file_match = FileMatch(
                file_path=test_file,
                filename="test.txt",
                folder_path=temp_path,
                modified_date=datetime.now(),
                file_size=test_file.stat().st_size
            )
            
            # 正規表現で日付を置換
            operation = ReplaceOperation(
                search_pattern=r"\d{4}-\d{2}-\d{2}",
                replace_text="YYYY-MM-DD",
                use_regex=True,
                case_sensitive=True,
                create_backup=False
            )
            operation.add_target_file(file_match)
            
            result = self.service.replace(operation)
            
            assert result.success_count == 1
            assert result.total_replacements == 2
            
            new_content = test_file.read_text()
            assert "Date: YYYY-MM-DD\nAnother date: YYYY-MM-DD" == new_content
    
    def test_case_insensitive_replacement(self):
        """大文字小文字を区別しない置換のテスト"""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            test_file = temp_path / "test.txt"
            test_file.write_text("Test TEST test TeSt")
            
            file_match = FileMatch(
                file_path=test_file,
                filename="test.txt",
                folder_path=temp_path,
                modified_date=datetime.now(),
                file_size=test_file.stat().st_size
            )
            
            operation = ReplaceOperation(
                search_pattern="test",
                replace_text="REPLACED",
                use_regex=False,
                case_sensitive=False,
                create_backup=False
            )
            operation.add_target_file(file_match)
            
            result = self.service.replace(operation)
            
            assert result.success_count == 1
            assert result.total_replacements == 4
            
            new_content = test_file.read_text()
            assert "REPLACED REPLACED REPLACED REPLACED" == new_content
    
    def test_backup_creation(self):
        """バックアップファイル作成のテスト"""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            test_file = temp_path / "test.txt"
            original_content = "Original content"
            test_file.write_text(original_content)
            
            file_match = FileMatch(
                file_path=test_file,
                filename="test.txt",
                folder_path=temp_path,
                modified_date=datetime.now(),
                file_size=test_file.stat().st_size
            )
            
            operation = ReplaceOperation(
                search_pattern="Original",
                replace_text="Modified",
                create_backup=True,
                backup_suffix=".bak"
            )
            operation.add_target_file(file_match)
            
            result = self.service.replace(operation)
            
            assert result.success_count == 1
            assert len(result.backup_files) == 1
            
            # バックアップファイルの確認
            backup_file = result.backup_files[0]
            assert backup_file.exists()
            assert backup_file.read_text() == original_content
            
            # 元ファイルの確認
            assert test_file.read_text() == "Modified content"
    
    def test_preview_replace(self):
        """置換プレビューのテスト"""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            test_file = temp_path / "test.txt"
            test_file.write_text("Line 1: test\nLine 2: another test\nLine 3: no match")
            
            file_match = FileMatch(
                file_path=test_file,
                filename="test.txt",
                folder_path=temp_path,
                modified_date=datetime.now(),
                file_size=test_file.stat().st_size
            )
            
            operation = ReplaceOperation(
                search_pattern="test",
                replace_text="REPLACED",
                create_backup=False
            )
            operation.add_target_file(file_match)
            
            # プレビュー実行
            preview_results = self.service.preview_replace(operation)
            
            assert len(preview_results) == 1
            
            file_preview = preview_results[0]
            assert file_preview["file_path"] == test_file
            assert len(file_preview["changes"]) == 2  # 2行にマッチ
            assert file_preview["total_replacements"] == 2
            
            # 実際のファイルは変更されていない
            assert test_file.read_text() == "Line 1: test\nLine 2: another test\nLine 3: no match"
    
    def test_restore_from_backup(self):
        """バックアップからの復元のテスト"""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # 元ファイル作成
            original_file = temp_path / "original.txt"
            original_content = "Original content"
            original_file.write_text(original_content)
            
            # バックアップファイル作成
            backup_file = temp_path / "original.txt.bak"
            
            file_match = FileMatch(
                file_path=original_file,
                filename="original.txt",
                folder_path=temp_path,
                modified_date=datetime.now(),
                file_size=original_file.stat().st_size
            )
            
            operation = ReplaceOperation(
                search_pattern="Original",
                replace_text="Modified",
                create_backup=True
            )
            operation.add_target_file(file_match)
            
            # 置換実行（バックアップ作成）
            result = self.service.replace(operation)
            backup_path = result.backup_files[0]
            
            # ファイルが変更されていることを確認
            assert original_file.read_text() == "Modified content"
            
            # バックアップから復元
            restore_success = self.service.restore_from_backup(backup_path)
            
            assert restore_success
            assert original_file.read_text() == original_content
    
    def test_cleanup_backups(self):
        """バックアップファイル削除のテスト"""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # バックアップファイル作成
            backup_files = []
            for i in range(3):
                backup_file = temp_path / f"backup{i}.txt.bak"
                backup_file.write_text(f"Backup content {i}")
                backup_files.append(backup_file)
            
            # 削除実行
            deleted_count = self.service.cleanup_backups(backup_files)
            
            assert deleted_count == 3
            
            # ファイルが削除されていることを確認
            for backup_file in backup_files:
                assert not backup_file.exists()
    
    def test_error_handling(self):
        """エラーハンドリングのテスト"""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # 存在しないファイル
            nonexistent_file = temp_path / "nonexistent.txt"
            
            file_match = FileMatch(
                file_path=nonexistent_file,
                filename="nonexistent.txt",
                folder_path=temp_path,
                modified_date=datetime.now(),
                file_size=0
            )
            
            operation = ReplaceOperation(
                search_pattern="test",
                replace_text="replaced"
            )
            operation.add_target_file(file_match)
            
            result = self.service.replace(operation)
            
            assert result.success_count == 0
            assert result.error_count == 1
            assert len(result.failed_files) == 1
    
    def test_invalid_regex_handling(self):
        """無効な正規表現のハンドリングテスト"""
        text = "test string"
        invalid_pattern = "[invalid"
        replacement = "replaced"
        
        # 無効な正規表現でも例外が発生しない
        new_text, count = self.service._perform_replacement(
            text, invalid_pattern, replacement, use_regex=True, case_sensitive=True
        )
        
        # フォールバック処理により結果が返される
        assert isinstance(new_text, str)
        assert isinstance(count, int)