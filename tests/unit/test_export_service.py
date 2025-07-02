"""
エクスポートサービスのユニットテスト
"""
import pytest
import json
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from src.models import SearchCriteria, SearchResult, FileMatch, ContentMatch
from src.services import ExportService


class TestExportService:
    """ExportServiceのテスト"""
    
    def setup_method(self):
        """テストメソッド前の準備"""
        self.service = ExportService()
        
        # テスト用データの作成
        with TemporaryDirectory() as temp_dir:
            self.criteria = SearchCriteria(target_folder=Path(temp_dir))
        
        self.result = SearchResult(criteria=self.criteria)
        
        # サンプルファイルマッチを追加
        file_match1 = FileMatch(
            file_path=Path("/test/file1.txt"),
            filename="file1.txt",
            folder_path=Path("/test"),
            modified_date=datetime(2025, 6, 27, 10, 30, 0),
            file_size=1024
        )
        file_match1.matches.append(ContentMatch(
            line_number=1,
            matched_text="test",
            context_before="This is a ",
            context_after=" string"
        ))
        
        file_match2 = FileMatch(
            file_path=Path("/test/file2.py"),
            filename="file2.py", 
            folder_path=Path("/test"),
            modified_date=datetime(2025, 6, 27, 11, 0, 0),
            file_size=2048
        )
        
        self.result.add_match(file_match1)
        self.result.add_match(file_match2)
        self.result.search_duration = 1.5
        self.result.total_files_scanned = 10
    
    def test_export_to_csv(self):
        """CSV出力のテスト"""
        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_export.csv"
            
            success = self.service.export_to_csv(self.result, output_path)
            
            assert success
            assert output_path.exists()
            
            # CSVファイルの内容確認
            content = output_path.read_text(encoding='utf-8')
            assert "ファイル名" in content
            assert "file1.txt" in content
            assert "file2.py" in content
            assert "検索サマリー" in content
    
    def test_export_to_json(self):
        """JSON出力のテスト"""
        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_export.json"
            
            success = self.service.export_to_json(self.result, output_path)
            
            assert success
            assert output_path.exists()
            
            # JSONファイルの内容確認
            with output_path.open('r', encoding='utf-8') as f:
                data = json.load(f)
            
            assert "search_criteria" in data
            assert "results" in data
            assert "matches" in data
            assert len(data["matches"]) == 2
            assert data["results"]["match_count"] == 2
            assert data["results"]["search_duration"] == 1.5
    
    def test_export_to_html(self):
        """HTML出力のテスト"""
        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_export.html"
            
            success = self.service.export_to_html(self.result, output_path)
            
            assert success
            assert output_path.exists()
            
            # HTMLファイルの内容確認
            content = output_path.read_text(encoding='utf-8')
            assert "<!DOCTYPE html>" in content
            assert "Finder Scope" in content
            assert "file1.txt" in content
            assert "file2.py" in content
            assert "検索条件" in content
    
    def test_empty_result_export(self):
        """空の検索結果の出力テスト"""
        with TemporaryDirectory() as temp_dir:
            empty_result = SearchResult(criteria=self.criteria)
            
            csv_path = Path(temp_dir) / "empty.csv"
            json_path = Path(temp_dir) / "empty.json"
            html_path = Path(temp_dir) / "empty.html"
            
            # すべての形式で出力成功
            assert self.service.export_to_csv(empty_result, csv_path)
            assert self.service.export_to_json(empty_result, json_path)
            assert self.service.export_to_html(empty_result, html_path)
            
            # ファイルが作成されている
            assert csv_path.exists()
            assert json_path.exists()
            assert html_path.exists()
    
    def test_file_match_to_dict(self):
        """FileMatchの辞書変換テスト"""
        file_match = FileMatch(
            file_path=Path("/test/sample.txt"),
            filename="sample.txt",
            folder_path=Path("/test"),
            modified_date=datetime(2025, 6, 27, 12, 0, 0),
            file_size=512
        )
        
        content_match = ContentMatch(
            line_number=5,
            matched_text="example",
            context_before="This is an ",
            context_after=" text",
            start_position=10,
            end_position=17
        )
        file_match.matches.append(content_match)
        
        result_dict = self.service._file_match_to_dict(file_match)
        
        assert result_dict["filename"] == "sample.txt"
        assert result_dict["file_path"] == "/test/sample.txt"
        assert result_dict["file_size"] == 512
        assert result_dict["match_count"] == 1
        assert len(result_dict["content_matches"]) == 1
        assert result_dict["content_matches"][0]["line_number"] == 5
        assert result_dict["content_matches"][0]["matched_text"] == "example"
    
    def test_export_error_handling(self):
        """エクスポートエラーハンドリングのテスト"""
        # 無効なパス
        invalid_path = Path("/invalid/directory/file.csv")
        
        success = self.service.export_to_csv(self.result, invalid_path)
        assert not success
        
        success = self.service.export_to_json(self.result, invalid_path)
        assert not success
        
        success = self.service.export_to_html(self.result, invalid_path)
        assert not success