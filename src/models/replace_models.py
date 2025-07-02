"""
置換機能に関するデータモデル
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from .search_models import SearchCriteria, FileMatch


@dataclass
class ReplaceOperation:
    """置換操作を表すデータクラス"""
    search_pattern: str
    replace_text: str
    target_files: List[FileMatch] = field(default_factory=list)
    use_regex: bool = False
    case_sensitive: bool = False
    create_backup: bool = True
    backup_suffix: str = ".bak"
    
    @property
    def file_count(self) -> int:
        """対象ファイル数"""
        return len(self.target_files)
    
    def add_target_file(self, file_match: FileMatch) -> None:
        """対象ファイルを追加"""
        if file_match not in self.target_files:
            self.target_files.append(file_match)
    
    def clear_target_files(self) -> None:
        """対象ファイルをクリア"""
        self.target_files.clear()


@dataclass
class ReplaceResult:
    """置換結果を表すデータクラス"""
    operation: ReplaceOperation
    processed_files: List[Path] = field(default_factory=list)
    failed_files: List[tuple[Path, str]] = field(default_factory=list)  # (ファイルパス, エラーメッセージ)
    total_replacements: int = 0
    backup_files: List[Path] = field(default_factory=list)
    
    @property
    def success_count(self) -> int:
        """成功したファイル数"""
        return len(self.processed_files)
    
    @property
    def error_count(self) -> int:
        """失敗したファイル数"""
        return len(self.failed_files)
    
    @property
    def success_rate(self) -> float:
        """成功率（%）"""
        total = self.success_count + self.error_count
        if total == 0:
            return 0.0
        return (self.success_count / total) * 100
    
    def add_success(self, file_path: Path, replacement_count: int = 0, backup_path: Optional[Path] = None) -> None:
        """成功結果を追加"""
        self.processed_files.append(file_path)
        self.total_replacements += replacement_count
        if backup_path:
            self.backup_files.append(backup_path)
    
    def add_error(self, file_path: Path, error_message: str) -> None:
        """エラー結果を追加"""
        self.failed_files.append((file_path, error_message))
    
    def get_summary(self) -> str:
        """置換結果のサマリー文字列"""
        return (
            f"置換結果: {self.success_count}件成功, {self.error_count}件失敗 "
            f"(総置換数: {self.total_replacements}箇所, 成功率: {self.success_rate:.1f}%)"
        )