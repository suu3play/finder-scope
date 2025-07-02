"""
ファイル検索サービスのユニットテスト
"""
import pytest
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from src.models import SearchCriteria
from src.services import FileSearchService


class TestFileSearchService:
    """FileSearchServiceのテスト"""
    
    def setup_method(self):
        """テストメソッド前の準備"""
        self.service = FileSearchService()
    
    def test_empty_folder_search(self):
        """空フォルダの検索"""
        with TemporaryDirectory() as temp_dir:
            criteria = SearchCriteria(target_folder=Path(temp_dir))
            result = self.service.search(criteria)
            
            assert result.match_count == 0
            assert result.total_files_scanned == 0
    
    def test_filename_search(self):
        """ファイル名検索"""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # テストファイル作成
            (temp_path / "test_file.txt").write_text("content")
            (temp_path / "another.txt").write_text("content")
            (temp_path / "test_data.py").write_text("content")
            
            # "test"を含むファイル名で検索
            criteria = SearchCriteria(
                target_folder=temp_path,
                filename_pattern="test"
            )
            result = self.service.search(criteria)
            
            assert result.match_count == 2
            assert result.total_files_scanned == 3
            
            # マッチしたファイル名を確認
            matched_names = [match.filename for match in result.matches]
            assert "test_file.txt" in matched_names
            assert "test_data.py" in matched_names
            assert "another.txt" not in matched_names
    
    def test_extension_filter(self):
        """拡張子フィルタ"""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # 様々な拡張子のファイルを作成
            (temp_path / "file1.txt").write_text("content")
            (temp_path / "file2.py").write_text("content")
            (temp_path / "file3.log").write_text("content")
            (temp_path / "file4.txt").write_text("content")
            
            # .txtファイルのみ検索
            criteria = SearchCriteria(
                target_folder=temp_path,
                file_extensions=[".txt"]
            )
            result = self.service.search(criteria)
            
            assert result.match_count == 2
            
            # マッチしたファイル名を確認
            matched_names = [match.filename for match in result.matches]
            assert all(name.endswith(".txt") for name in matched_names)
    
    def test_content_search(self):
        """ファイル内容検索"""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # 異なる内容のファイル作成
            (temp_path / "file1.txt").write_text("This contains target word")
            (temp_path / "file2.txt").write_text("No match here")
            (temp_path / "file3.txt").write_text("Another target found")
            
            # "target"を含む内容で検索
            criteria = SearchCriteria(
                target_folder=temp_path,
                content_pattern="target"
            )
            result = self.service.search(criteria)
            
            assert result.match_count == 2
            assert result.total_content_matches == 2
            
            # マッチした内容を確認
            for file_match in result.matches:
                if file_match.filename == "file1.txt":
                    assert len(file_match.matches) == 1
                    assert file_match.matches[0].matched_text == "target"
                elif file_match.filename == "file3.txt":
                    assert len(file_match.matches) == 1
                    assert file_match.matches[0].matched_text == "target"
    
    def test_case_sensitivity(self):
        """大文字小文字の区別"""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # 大文字小文字を含むファイル作成
            (temp_path / "Test.txt").write_text("Content with Test")
            (temp_path / "test.txt").write_text("Content with test")
            
            # 大文字小文字を区別する検索
            criteria_sensitive = SearchCriteria(
                target_folder=temp_path,
                filename_pattern="Test",
                case_sensitive=True
            )
            result_sensitive = self.service.search(criteria_sensitive)
            assert result_sensitive.match_count == 1
            assert result_sensitive.matches[0].filename == "Test.txt"
            
            # 大文字小文字を区別しない検索
            criteria_insensitive = SearchCriteria(
                target_folder=temp_path,
                filename_pattern="test",
                case_sensitive=False
            )
            result_insensitive = self.service.search(criteria_insensitive)
            assert result_insensitive.match_count == 2
    
    def test_regex_search(self):
        """正規表現検索"""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # テストファイル作成
            (temp_path / "file001.txt").write_text("content")
            (temp_path / "file002.txt").write_text("content")
            (temp_path / "fileabc.txt").write_text("content")
            
            # 数字で終わるファイル名を検索
            criteria = SearchCriteria(
                target_folder=temp_path,
                filename_pattern=r"file\d+\.txt",
                use_regex=True
            )
            result = self.service.search(criteria)
            
            assert result.match_count == 2
            matched_names = [match.filename for match in result.matches]
            assert "file001.txt" in matched_names
            assert "file002.txt" in matched_names
            assert "fileabc.txt" not in matched_names
    
    def test_subdirectory_search(self):
        """サブディレクトリ検索"""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # サブディレクトリとファイル作成
            sub_dir = temp_path / "subdir"
            sub_dir.mkdir()
            
            (temp_path / "root.txt").write_text("content")
            (sub_dir / "sub.txt").write_text("content")
            
            # サブディレクトリを含む検索
            criteria_with_sub = SearchCriteria(
                target_folder=temp_path,
                include_subdirectories=True
            )
            result_with_sub = self.service.search(criteria_with_sub)
            assert result_with_sub.match_count == 2
            
            # サブディレクトリを含まない検索
            criteria_no_sub = SearchCriteria(
                target_folder=temp_path,
                include_subdirectories=False
            )
            result_no_sub = self.service.search(criteria_no_sub)
            assert result_no_sub.match_count == 1
            assert result_no_sub.matches[0].filename == "root.txt"
    
    def test_search_cancellation(self):
        """検索キャンセル"""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # 多数のファイルを作成
            for i in range(10):
                (temp_path / f"file{i}.txt").write_text("content")
            
            criteria = SearchCriteria(target_folder=temp_path)
            
            # 検索を開始してすぐキャンセル
            self.service.cancel()
            result = self.service.search(criteria)
            
            # キャンセルにより、すべてのファイルがスキャンされない
            assert result.total_files_scanned < 10
    
    def test_invalid_regex(self):
        """無効な正規表現の処理"""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # テストファイル作成
            (temp_path / "test.txt").write_text("content")
            
            # 無効な正規表現でも動作することを確認（フォールバック）
            criteria = SearchCriteria(
                target_folder=temp_path,
                filename_pattern="[invalid",  # 不正な正規表現
                use_regex=True
            )
            
            # エラーにならず、通常の文字列検索にフォールバック
            result = self.service.search(criteria)
            assert result.total_files_scanned == 1