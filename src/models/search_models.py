"""
検索機能に関するデータモデル
"""
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional


@dataclass
class SearchCriteria:
    """検索条件を表すデータクラス"""
    target_folder: Path
    filename_pattern: Optional[str] = None
    file_extensions: List[str] = field(default_factory=list)
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    content_pattern: Optional[str] = None
    use_regex: bool = False
    case_sensitive: bool = False
    include_subdirectories: bool = True
    
    def __post_init__(self) -> None:
        """初期化後の検証"""
        if not self.target_folder.exists():
            raise ValueError(f"対象フォルダが存在しません: {self.target_folder}")
        
        if not self.target_folder.is_dir():
            raise ValueError(f"対象パスがフォルダではありません: {self.target_folder}")
        
        # 拡張子の正規化（先頭にドットを追加）
        self.file_extensions = [
            ext if ext.startswith('.') else f'.{ext}' 
            for ext in self.file_extensions
        ]


@dataclass
class ContentMatch:
    """ファイル内容のマッチ情報"""
    line_number: int
    matched_text: str
    context_before: str = ""
    context_after: str = ""
    start_position: int = 0
    end_position: int = 0
    
    @property
    def context_preview(self) -> str:
        """マッチ部分のプレビューテキスト"""
        return f"{self.context_before}{self.matched_text}{self.context_after}"


@dataclass
class FileMatch:
    """検索にマッチしたファイル情報"""
    file_path: Path
    filename: str
    folder_path: Path
    modified_date: datetime
    file_size: int
    matches: List[ContentMatch] = field(default_factory=list)
    
    def __post_init__(self) -> None:
        """初期化後の処理"""
        self.filename = self.file_path.name
        self.folder_path = self.file_path.parent
    
    @property
    def match_count(self) -> int:
        """マッチ数"""
        return len(self.matches)
    
    @property
    def file_extension(self) -> str:
        """ファイル拡張子"""
        return self.file_path.suffix
    
    @property
    def relative_path(self) -> str:
        """相対パス表示用"""
        return str(self.file_path)
    
    @property
    def size_formatted(self) -> str:
        """ファイルサイズの整形表示"""
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        elif self.file_size < 1024 * 1024 * 1024:
            return f"{self.file_size / (1024 * 1024):.1f} MB"
        else:
            return f"{self.file_size / (1024 * 1024 * 1024):.1f} GB"


@dataclass
class SearchResult:
    """検索結果の統合データ"""
    criteria: SearchCriteria
    matches: List[FileMatch] = field(default_factory=list)
    search_duration: float = 0.0
    total_files_scanned: int = 0
    
    @property
    def match_count(self) -> int:
        """マッチしたファイル数"""
        return len(self.matches)
    
    @property
    def total_content_matches(self) -> int:
        """コンテンツマッチの総数"""
        return sum(file_match.match_count for file_match in self.matches)
    
    def add_match(self, file_match: FileMatch) -> None:
        """マッチ結果を追加"""
        self.matches.append(file_match)
    
    def clear_matches(self) -> None:
        """マッチ結果をクリア"""
        self.matches.clear()
    
    def get_summary(self) -> str:
        """検索結果のサマリー文字列"""
        return (
            f"検索結果: {self.match_count}件のファイルがマッチ "
            f"({self.total_files_scanned}件中) "
            f"実行時間: {self.search_duration:.2f}秒"
        )