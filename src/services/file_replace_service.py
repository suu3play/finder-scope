"""
ファイル置換サービス
"""
import re
import shutil
from pathlib import Path
from typing import List, Optional

from src.models import ReplaceOperation, ReplaceResult, FileMatch


class FileReplaceService:
    """ファイル置換機能を提供するサービスクラス"""
    
    def __init__(self):
        self.is_cancelled = False
    
    def replace(self, operation: ReplaceOperation) -> ReplaceResult:
        """置換実行"""
        result = ReplaceResult(operation=operation)
        
        try:
            self.is_cancelled = False
            
            for file_match in operation.target_files:
                if self.is_cancelled:
                    break
                
                try:
                    replacement_count = self._replace_in_file(
                        file_match.file_path, 
                        operation
                    )
                    
                    backup_path = None
                    if operation.create_backup and replacement_count > 0:
                        backup_path = self._create_backup(file_match.file_path, operation.backup_suffix)
                    
                    result.add_success(file_match.file_path, replacement_count, backup_path)
                    
                except Exception as e:
                    result.add_error(file_match.file_path, str(e))
        
        except Exception as e:
            # 全体的なエラー
            for file_match in operation.target_files:
                if file_match.file_path not in [p for p, _ in result.failed_files]:
                    result.add_error(file_match.file_path, f"処理エラー: {e}")
        
        return result
    
    def cancel(self) -> None:
        """置換キャンセル"""
        self.is_cancelled = True
    
    def preview_replace(self, operation: ReplaceOperation) -> List[dict]:
        """置換のプレビュー（実際の置換は行わない）"""
        preview_results = []
        
        for file_match in operation.target_files:
            if self.is_cancelled:
                break
            
            try:
                file_preview = self._preview_file_replace(file_match.file_path, operation)
                if file_preview["changes"]:
                    preview_results.append(file_preview)
            except Exception as e:
                preview_results.append({
                    "file_path": file_match.file_path,
                    "error": str(e),
                    "changes": []
                })
        
        return preview_results
    
    def _replace_in_file(self, file_path: Path, operation: ReplaceOperation) -> int:
        """単一ファイル内の置換処理"""
        try:
            # ファイル読み込み
            with file_path.open('r', encoding='utf-8') as f:
                content = f.read()
            
            # 置換実行
            new_content, replacement_count = self._perform_replacement(
                content, 
                operation.search_pattern, 
                operation.replace_text,
                operation.use_regex,
                operation.case_sensitive
            )
            
            # 変更があった場合のみファイル書き込み
            if replacement_count > 0:
                with file_path.open('w', encoding='utf-8') as f:
                    f.write(new_content)
            
            return replacement_count
            
        except UnicodeDecodeError:
            raise Exception("テキストファイルではありません")
        except PermissionError:
            raise Exception("ファイルへの書き込み権限がありません")
        except OSError as e:
            raise Exception(f"ファイルアクセスエラー: {e}")
    
    def _preview_file_replace(self, file_path: Path, operation: ReplaceOperation) -> dict:
        """単一ファイルの置換プレビュー"""
        try:
            with file_path.open('r', encoding='utf-8') as f:
                lines = f.readlines()
            
            changes = []
            for line_num, line in enumerate(lines, 1):
                new_line, count = self._perform_replacement(
                    line.rstrip('\n\r'),
                    operation.search_pattern,
                    operation.replace_text,
                    operation.use_regex,
                    operation.case_sensitive
                )
                
                if count > 0:
                    changes.append({
                        "line_number": line_num,
                        "original": line.rstrip('\n\r'),
                        "replaced": new_line,
                        "replacement_count": count
                    })
            
            return {
                "file_path": file_path,
                "changes": changes,
                "total_replacements": sum(change["replacement_count"] for change in changes)
            }
            
        except Exception as e:
            return {
                "file_path": file_path,
                "error": str(e),
                "changes": []
            }
    
    def _perform_replacement(self, text: str, pattern: str, replacement: str, 
                           use_regex: bool, case_sensitive: bool) -> tuple[str, int]:
        """文字列置換の実行"""
        if use_regex:
            flags = 0 if case_sensitive else re.IGNORECASE
            try:
                new_text, count = re.subn(pattern, replacement, text, flags=flags)
                return new_text, count
            except re.error:
                # 正規表現エラーの場合は通常の文字列置換にフォールバック
                return self._simple_replacement(text, pattern, replacement, case_sensitive)
        else:
            return self._simple_replacement(text, pattern, replacement, case_sensitive)
    
    def _simple_replacement(self, text: str, pattern: str, replacement: str, 
                          case_sensitive: bool) -> tuple[str, int]:
        """シンプルな文字列置換"""
        if not case_sensitive:
            # 大文字小文字を区別しない場合
            count = text.lower().count(pattern.lower())
            if count == 0:
                return text, 0
            
            # より正確な置換のため、正規表現を使用
            flags = re.IGNORECASE
            pattern_escaped = re.escape(pattern)
            new_text = re.sub(pattern_escaped, replacement, text, flags=flags)
            return new_text, count
        else:
            # 大文字小文字を区別する場合
            count = text.count(pattern)
            new_text = text.replace(pattern, replacement)
            return new_text, count
    
    def _create_backup(self, file_path: Path, backup_suffix: str) -> Path:
        """バックアップファイル作成"""
        backup_path = file_path.with_suffix(file_path.suffix + backup_suffix)
        
        # 既存のバックアップファイルがある場合は連番を付ける
        counter = 1
        original_backup_path = backup_path
        while backup_path.exists():
            backup_path = original_backup_path.with_suffix(
                original_backup_path.suffix + f".{counter}"
            )
            counter += 1
        
        # バックアップファイルをコピー
        shutil.copy2(file_path, backup_path)
        return backup_path
    
    def restore_from_backup(self, backup_path: Path) -> bool:
        """バックアップから復元"""
        try:
            original_path = self._get_original_path_from_backup(backup_path)
            if original_path and original_path.exists():
                shutil.copy2(backup_path, original_path)
                return True
            return False
        except Exception:
            return False
    
    def _get_original_path_from_backup(self, backup_path: Path) -> Optional[Path]:
        """バックアップファイルパスから元のファイルパスを取得"""
        path_str = str(backup_path)
        
        # .bak を削除
        if path_str.endswith('.bak'):
            return Path(path_str[:-4])
        
        # .bak.1, .bak.2 などを削除
        if '.bak.' in path_str:
            return Path(path_str.split('.bak.')[0])
        
        return None
    
    def cleanup_backups(self, backup_files: List[Path]) -> int:
        """バックアップファイルの削除"""
        deleted_count = 0
        for backup_path in backup_files:
            try:
                if backup_path.exists():
                    backup_path.unlink()
                    deleted_count += 1
            except Exception:
                continue
        return deleted_count