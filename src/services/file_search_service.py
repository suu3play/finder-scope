"""
ファイル検索サービス
"""
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Iterator, List, Optional

from src.models import SearchCriteria, FileMatch, ContentMatch, SearchResult


class FileSearchService:
    """ファイル検索機能を提供するサービスクラス"""
    
    def __init__(self):
        self.is_cancelled = False
    
    def search(self, criteria: SearchCriteria) -> SearchResult:
        """検索実行"""
        start_time = time.time()
        result = SearchResult(criteria=criteria)
        
        try:
            self.is_cancelled = False
            
            # ファイル一覧を取得
            files = self._get_file_list(criteria)
            
            for file_path in files:
                if self.is_cancelled:
                    break
                
                result.total_files_scanned += 1
                
                # ファイル情報を取得
                file_info = self._get_file_info(file_path)
                if not file_info:
                    continue
                
                # 検索条件に一致するかチェック
                if self._matches_criteria(file_path, file_info, criteria):
                    file_match = self._create_file_match(file_path, file_info, criteria)
                    result.add_match(file_match)
            
        finally:
            result.search_duration = time.time() - start_time
        
        return result
    
    def cancel(self) -> None:
        """検索キャンセル"""
        self.is_cancelled = True
    
    def _get_file_list(self, criteria: SearchCriteria) -> Iterator[Path]:
        """検索対象ファイル一覧を取得"""
        if criteria.include_subdirectories:
            # 再帰的に検索
            return criteria.target_folder.rglob("*")
        else:
            # 指定フォルダのみ
            return criteria.target_folder.iterdir()
    
    def _get_file_info(self, file_path: Path) -> Optional[dict]:
        """ファイル情報を取得"""
        try:
            if not file_path.is_file():
                return None
            
            stat = file_path.stat()
            return {
                "modified_date": datetime.fromtimestamp(stat.st_mtime),
                "file_size": stat.st_size
            }
        except (OSError, PermissionError):
            return None
    
    def _matches_criteria(self, file_path: Path, file_info: dict, criteria: SearchCriteria) -> bool:
        """ファイルが検索条件に一致するかチェック"""
        # ファイル名チェック
        if criteria.filename_pattern:
            if not self._matches_filename(file_path.name, criteria.filename_pattern, criteria.use_regex, criteria.case_sensitive):
                return False
        
        # 拡張子チェック
        if criteria.file_extensions:
            if file_path.suffix.lower() not in [ext.lower() for ext in criteria.file_extensions]:
                return False
        
        # 更新日チェック
        if criteria.date_from and file_info["modified_date"] < criteria.date_from:
            return False
        if criteria.date_to and file_info["modified_date"] > criteria.date_to:
            return False
        
        return True
    
    def _matches_filename(self, filename: str, pattern: str, use_regex: bool, case_sensitive: bool) -> bool:
        """ファイル名パターンマッチング"""
        if use_regex:
            flags = 0 if case_sensitive else re.IGNORECASE
            try:
                return bool(re.search(pattern, filename, flags))
            except re.error:
                # 正規表現エラーの場合は通常の文字列検索にフォールバック
                return self._simple_match(filename, pattern, case_sensitive)
        else:
            return self._simple_match(filename, pattern, case_sensitive)
    
    def _simple_match(self, text: str, pattern: str, case_sensitive: bool) -> bool:
        """シンプルな文字列マッチング"""
        if not case_sensitive:
            text = text.lower()
            pattern = pattern.lower()
        return pattern in text
    
    def _create_file_match(self, file_path: Path, file_info: dict, criteria: SearchCriteria) -> FileMatch:
        """FileMatchオブジェクトを作成"""
        file_match = FileMatch(
            file_path=file_path,
            filename=file_path.name,
            folder_path=file_path.parent,
            modified_date=file_info["modified_date"],
            file_size=file_info["file_size"]
        )
        
        # コンテンツ検索がある場合
        if criteria.content_pattern:
            content_matches = self._search_file_content(file_path, criteria)
            file_match.matches.extend(content_matches)
        
        return file_match
    
    def _search_file_content(self, file_path: Path, criteria: SearchCriteria) -> List[ContentMatch]:
        """ファイル内容検索"""
        content_matches = []
        
        try:
            # テキストファイルとして読み込み試行
            with file_path.open('r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    if self.is_cancelled:
                        break
                    
                    matches = self._find_line_matches(line, criteria.content_pattern, criteria.use_regex, criteria.case_sensitive)
                    for match in matches:
                        content_match = ContentMatch(
                            line_number=line_num,
                            matched_text=match["text"],
                            context_before=match["before"],
                            context_after=match["after"],
                            start_position=match["start"],
                            end_position=match["end"]
                        )
                        content_matches.append(content_match)
        
        except (UnicodeDecodeError, PermissionError, OSError):
            # バイナリファイルや読み込み不可ファイルはスキップ
            pass
        
        return content_matches
    
    def _find_line_matches(self, line: str, pattern: str, use_regex: bool, case_sensitive: bool) -> List[dict]:
        """行内のマッチを検索"""
        matches = []
        
        if use_regex:
            flags = 0 if case_sensitive else re.IGNORECASE
            try:
                for match in re.finditer(pattern, line, flags):
                    matches.append({
                        "text": match.group(),
                        "start": match.start(),
                        "end": match.end(),
                        "before": line[:match.start()][-20:],  # 前後20文字のコンテキスト
                        "after": line[match.end():][:20]
                    })
            except re.error:
                # 正規表現エラー時は通常検索
                return self._simple_line_search(line, pattern, case_sensitive)
        else:
            return self._simple_line_search(line, pattern, case_sensitive)
        
        return matches
    
    def _simple_line_search(self, line: str, pattern: str, case_sensitive: bool) -> List[dict]:
        """シンプルな行内検索"""
        matches = []
        search_line = line if case_sensitive else line.lower()
        search_pattern = pattern if case_sensitive else pattern.lower()
        
        start = 0
        while True:
            pos = search_line.find(search_pattern, start)
            if pos == -1:
                break
            
            matches.append({
                "text": line[pos:pos + len(pattern)],
                "start": pos,
                "end": pos + len(pattern),
                "before": line[:pos][-20:],
                "after": line[pos + len(pattern):][:20]
            })
            start = pos + 1
        
        return matches