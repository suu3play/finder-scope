"""
設定機能に関するデータモデル
"""
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional, Dict, Any


@dataclass
class SearchSettings:
    """検索設定"""
    default_use_regex: bool = False
    default_case_sensitive: bool = False
    default_include_subdirectories: bool = True
    max_file_size_mb: int = 100  # MB
    max_results: int = 10000
    excluded_extensions: List[str] = None
    excluded_folders: List[str] = None
    
    def __post_init__(self):
        if self.excluded_extensions is None:
            self.excluded_extensions = ['.exe', '.dll', '.bin', '.zip', '.rar']
        if self.excluded_folders is None:
            self.excluded_folders = ['.git', '__pycache__', 'node_modules', '.vscode']


@dataclass
class UISettings:
    """UI設定"""
    window_width: int = 1200
    window_height: int = 800
    window_maximized: bool = False
    splitter_ratio: float = 0.3  # 検索条件:結果の比率
    font_family: str = "Segoe UI"
    font_size: int = 9
    theme: str = "default"  # default, dark
    show_tooltips: bool = True
    auto_save_settings: bool = True


@dataclass
class ExportSettings:
    """エクスポート設定"""
    default_format: str = "csv"  # csv, json, html
    default_output_folder: Optional[str] = None
    include_summary: bool = True
    csv_delimiter: str = ","
    csv_encoding: str = "utf-8"
    html_theme: str = "default"


@dataclass
class ReplaceSettings:
    """置換設定"""
    create_backup_by_default: bool = True
    backup_suffix: str = ".bak"
    confirm_before_replace: bool = True
    max_backup_files: int = 10
    auto_cleanup_backups: bool = False


@dataclass
class AppSettings:
    """アプリケーション全体の設定"""
    search: SearchSettings = None
    ui: UISettings = None
    export: ExportSettings = None
    replace: ReplaceSettings = None
    recent_folders: List[str] = None
    recent_patterns: List[str] = None
    
    def __post_init__(self):
        if self.search is None:
            self.search = SearchSettings()
        if self.ui is None:
            self.ui = UISettings()
        if self.export is None:
            self.export = ExportSettings()
        if self.replace is None:
            self.replace = ReplaceSettings()
        if self.recent_folders is None:
            self.recent_folders = []
        if self.recent_patterns is None:
            self.recent_patterns = []


class SettingsManager:
    """設定管理クラス"""
    
    def __init__(self, settings_file: Optional[Path] = None):
        print("SettingsManager初期化開始")  # デバッグ用
        
        if settings_file is None:
            # デフォルトの設定ファイルパス
            from pathlib import Path
            try:
                app_data = Path.home() / ".finder_scope"
                app_data.mkdir(exist_ok=True)
                settings_file = app_data / "settings.json"
                print(f"設定ファイルパス: {settings_file}")  # デバッグ用
            except Exception as e:
                print(f"設定ディレクトリ作成エラー: {e}")
                # フォールバック: 現在のディレクトリに設定ファイルを作成
                settings_file = Path("finder_scope_settings.json")
        
        self.settings_file = settings_file
        self._settings = AppSettings()
        
        try:
            self.load_settings()
            print("設定読み込み完了")  # デバッグ用
        except Exception as e:
            print(f"設定読み込みで重大エラー: {e}")
            # 最小限のデフォルト設定で続行
            self._settings = AppSettings()
        
        print("SettingsManager初期化完了")  # デバッグ用
    
    @property
    def settings(self) -> AppSettings:
        """設定オブジェクトを取得"""
        return self._settings
    
    def load_settings(self) -> bool:
        """設定ファイルから読み込み"""
        try:
            if not self.settings_file.exists():
                # デフォルト設定で新規作成
                self.save_settings()
                return True
            
            with self.settings_file.open('r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 設定を復元
            self._settings = self._dict_to_settings(data)
            return True
            
        except Exception as e:
            print(f"設定読み込みエラー: {e}")
            # デフォルト設定を使用
            self._settings = AppSettings()
            return False
    
    def save_settings(self) -> bool:
        """設定ファイルに保存"""
        try:
            # 親ディレクトリを作成
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 設定を辞書に変換
            data = self._settings_to_dict(self._settings)
            
            with self.settings_file.open('w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"設定保存エラー: {e}")
            return False
    
    def reset_to_defaults(self) -> None:
        """設定をデフォルトにリセット"""
        self._settings = AppSettings()
        self.save_settings()
    
    def add_recent_folder(self, folder_path: str) -> None:
        """最近使用したフォルダを追加"""
        if folder_path in self._settings.recent_folders:
            self._settings.recent_folders.remove(folder_path)
        
        self._settings.recent_folders.insert(0, folder_path)
        
        # 最大10件まで保持
        if len(self._settings.recent_folders) > 10:
            self._settings.recent_folders = self._settings.recent_folders[:10]
    
    def add_recent_pattern(self, pattern: str) -> None:
        """最近使用した検索パターンを追加"""
        if not pattern.strip():
            return
            
        if pattern in self._settings.recent_patterns:
            self._settings.recent_patterns.remove(pattern)
        
        self._settings.recent_patterns.insert(0, pattern)
        
        # 最大20件まで保持
        if len(self._settings.recent_patterns) > 20:
            self._settings.recent_patterns = self._settings.recent_patterns[:20]
    
    def get_recent_folders(self) -> List[str]:
        """最近使用したフォルダを取得"""
        return self._settings.recent_folders[:]
    
    def get_recent_patterns(self) -> List[str]:
        """最近使用した検索パターンを取得"""
        return self._settings.recent_patterns[:]
    
    def _settings_to_dict(self, settings: AppSettings) -> Dict[str, Any]:
        """設定オブジェクトを辞書に変換"""
        return {
            'search': asdict(settings.search),
            'ui': asdict(settings.ui),
            'export': asdict(settings.export),
            'replace': asdict(settings.replace),
            'recent_folders': settings.recent_folders,
            'recent_patterns': settings.recent_patterns
        }
    
    def _dict_to_settings(self, data: Dict[str, Any]) -> AppSettings:
        """辞書から設定オブジェクトを復元"""
        try:
            search = SearchSettings(**data.get('search', {}))
            ui = UISettings(**data.get('ui', {}))
            export = ExportSettings(**data.get('export', {}))
            replace = ReplaceSettings(**data.get('replace', {}))
            
            return AppSettings(
                search=search,
                ui=ui,
                export=export,
                replace=replace,
                recent_folders=data.get('recent_folders', []),
                recent_patterns=data.get('recent_patterns', [])
            )
        except Exception:
            # 設定の一部が不正な場合はデフォルトを使用
            return AppSettings()
    
    def export_settings(self, export_path: Path) -> bool:
        """設定をファイルにエクスポート"""
        try:
            data = self._settings_to_dict(self._settings)
            
            with export_path.open('w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception:
            return False
    
    def import_settings(self, import_path: Path) -> bool:
        """設定をファイルからインポート"""
        try:
            with import_path.open('r', encoding='utf-8') as f:
                data = json.load(f)
            
            self._settings = self._dict_to_settings(data)
            self.save_settings()
            
            return True
        except Exception:
            return False