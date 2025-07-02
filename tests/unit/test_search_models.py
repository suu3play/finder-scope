"""
検索モデルのユニットテスト
"""
import pytest
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from src.models import SearchCriteria, FileMatch, ContentMatch, SearchResult


class TestSearchCriteria:
    """SearchCriteriaのテスト"""
    
    def test_valid_criteria(self):
        """有効な検索条件の作成"""
        with TemporaryDirectory() as temp_dir:
            criteria = SearchCriteria(
                target_folder=Path(temp_dir),
                filename_pattern="test",
                file_extensions=[".txt", ".py"],
                use_regex=False
            )
            
            assert criteria.target_folder == Path(temp_dir)
            assert criteria.filename_pattern == "test"
            assert criteria.file_extensions == [".txt", ".py"]
            assert not criteria.use_regex
    
    def test_extension_normalization(self):
        """拡張子の正規化テスト"""
        with TemporaryDirectory() as temp_dir:
            criteria = SearchCriteria(
                target_folder=Path(temp_dir),
                file_extensions=["txt", ".py", "log"]
            )
            
            # 先頭にドットが追加されることを確認
            assert criteria.file_extensions == [".txt", ".py", ".log"]
    
    def test_invalid_folder(self):
        """存在しないフォルダでエラー"""
        with pytest.raises(ValueError, match="対象フォルダが存在しません"):
            SearchCriteria(target_folder=Path("/nonexistent/folder"))
    
    def test_file_as_folder(self):
        """ファイルをフォルダとして指定した場合のエラー"""
        with TemporaryDirectory() as temp_dir:
            # テストファイル作成
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("test")
            
            with pytest.raises(ValueError, match="対象パスがフォルダではありません"):
                SearchCriteria(target_folder=test_file)


class TestContentMatch:
    """ContentMatchのテスト"""
    
    def test_content_match_creation(self):
        """ContentMatchの作成"""
        match = ContentMatch(
            line_number=5,
            matched_text="test",
            context_before="before ",
            context_after=" after",
            start_position=10,
            end_position=14
        )
        
        assert match.line_number == 5
        assert match.matched_text == "test"
        assert match.context_before == "before "
        assert match.context_after == " after"
        assert match.start_position == 10
        assert match.end_position == 14
    
    def test_context_preview(self):
        """コンテキストプレビューの生成"""
        match = ContentMatch(
            line_number=1,
            matched_text="test",
            context_before="This is a ",
            context_after=" string"
        )
        
        assert match.context_preview == "This is a test string"


class TestFileMatch:
    """FileMatchのテスト"""
    
    def test_file_match_creation(self):
        """FileMatchの作成"""
        test_path = Path("/test/folder/file.txt")
        modified_date = datetime(2025, 6, 27, 10, 30, 0)
        
        file_match = FileMatch(
            file_path=test_path,
            filename="file.txt",
            folder_path=Path("/test/folder"),
            modified_date=modified_date,
            file_size=1024
        )
        
        assert file_match.file_path == test_path
        assert file_match.filename == "file.txt"
        assert file_match.folder_path == Path("/test/folder")
        assert file_match.modified_date == modified_date
        assert file_match.file_size == 1024
    
    def test_auto_extraction(self):
        """ファイル名・フォルダパスの自動抽出"""
        test_path = Path("/test/folder/example.py")
        
        file_match = FileMatch(
            file_path=test_path,
            filename="dummy",  # この値は無視される
            folder_path=Path("dummy"),  # この値は無視される
            modified_date=datetime.now(),
            file_size=100
        )
        
        # __post_init__で自動的に設定される
        assert file_match.filename == "example.py"
        assert file_match.folder_path == Path("/test/folder")
    
    def test_properties(self):
        """プロパティのテスト"""
        test_path = Path("/test/file.txt")
        file_match = FileMatch(
            file_path=test_path,
            filename="file.txt",
            folder_path=Path("/test"),
            modified_date=datetime.now(),
            file_size=1024
        )
        
        # マッチを追加
        file_match.matches.append(ContentMatch(1, "test"))
        file_match.matches.append(ContentMatch(2, "another"))
        
        assert file_match.match_count == 2
        assert file_match.file_extension == ".txt"
        assert file_match.size_formatted == "1.0 KB"
    
    def test_size_formatting(self):
        """ファイルサイズフォーマットのテスト"""
        test_cases = [
            (500, "500 B"),
            (1024, "1.0 KB"),
            (1024 * 1024, "1.0 MB"),
            (1024 * 1024 * 1024, "1.0 GB"),
            (1536, "1.5 KB"),  # 1.5KB
            (2560000, "2.4 MB")  # 約2.4MB
        ]
        
        for size, expected in test_cases:
            file_match = FileMatch(
                file_path=Path("/test.txt"),
                filename="test.txt",
                folder_path=Path("/"),
                modified_date=datetime.now(),
                file_size=size
            )
            assert file_match.size_formatted == expected


class TestSearchResult:
    """SearchResultのテスト"""
    
    def test_empty_result(self):
        """空の検索結果"""
        with TemporaryDirectory() as temp_dir:
            criteria = SearchCriteria(target_folder=Path(temp_dir))
            result = SearchResult(criteria=criteria)
            
            assert result.criteria == criteria
            assert result.match_count == 0
            assert result.total_content_matches == 0
            assert len(result.matches) == 0
    
    def test_add_matches(self):
        """マッチ追加のテスト"""
        with TemporaryDirectory() as temp_dir:
            criteria = SearchCriteria(target_folder=Path(temp_dir))
            result = SearchResult(criteria=criteria)
            
            # ファイルマッチを追加
            file_match1 = FileMatch(
                file_path=Path("/test1.txt"),
                filename="test1.txt",
                folder_path=Path("/"),
                modified_date=datetime.now(),
                file_size=100
            )
            file_match1.matches.append(ContentMatch(1, "test"))
            
            file_match2 = FileMatch(
                file_path=Path("/test2.txt"),
                filename="test2.txt",
                folder_path=Path("/"),
                modified_date=datetime.now(),
                file_size=200
            )
            file_match2.matches.extend([
                ContentMatch(1, "test"),
                ContentMatch(2, "another")
            ])
            
            result.add_match(file_match1)
            result.add_match(file_match2)
            
            assert result.match_count == 2
            assert result.total_content_matches == 3
    
    def test_clear_matches(self):
        """マッチクリアのテスト"""
        with TemporaryDirectory() as temp_dir:
            criteria = SearchCriteria(target_folder=Path(temp_dir))
            result = SearchResult(criteria=criteria)
            
            # マッチを追加
            file_match = FileMatch(
                file_path=Path("/test.txt"),
                filename="test.txt",
                folder_path=Path("/"),
                modified_date=datetime.now(),
                file_size=100
            )
            result.add_match(file_match)
            
            assert result.match_count == 1
            
            # クリア
            result.clear_matches()
            assert result.match_count == 0
            assert len(result.matches) == 0
    
    def test_summary(self):
        """サマリー文字列のテスト"""
        with TemporaryDirectory() as temp_dir:
            criteria = SearchCriteria(target_folder=Path(temp_dir))
            result = SearchResult(
                criteria=criteria,
                search_duration=1.5,
                total_files_scanned=100
            )
            
            # マッチを追加
            file_match = FileMatch(
                file_path=Path("/test.txt"),
                filename="test.txt",
                folder_path=Path("/"),
                modified_date=datetime.now(),
                file_size=100
            )
            result.add_match(file_match)
            
            summary = result.get_summary()
            assert "1件のファイルがマッチ" in summary
            assert "100件中" in summary
            assert "1.50秒" in summary