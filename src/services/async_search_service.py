"""
非同期検索サービス
UIの応答性を保つため、バックグラウンドで検索処理を実行
"""
from PySide6.QtCore import QThread, Signal, QMutex, QMutexLocker
from typing import Optional

from src.models import SearchCriteria, SearchResult
from src.services import FileSearchService


class SearchWorker(QThread):
    """検索処理を行うワーカースレッド"""
    
    # シグナル定義
    search_started = Signal()
    search_finished = Signal(SearchResult)
    search_error = Signal(str)
    progress_updated = Signal(int, str)  # (progress_value, status_message)
    file_processed = Signal(str)  # processed_file_path
    
    def __init__(self, criteria: SearchCriteria, parent=None):
        super().__init__(parent)
        self.criteria = criteria
        self.search_service = FileSearchService()
        self._is_cancelled = False
        self._mutex = QMutex()
    
    def run(self) -> None:
        """スレッド実行処理"""
        try:
            self.search_started.emit()
            
            # カスタムコールバック付きで検索実行
            result = self._search_with_progress()
            
            if not self._is_cancelled:
                self.search_finished.emit(result)
            
        except Exception as e:
            if not self._is_cancelled:
                self.search_error.emit(str(e))
    
    def cancel(self) -> None:
        """検索キャンセル"""
        with QMutexLocker(self._mutex):
            self._is_cancelled = True
            self.search_service.cancel()
    
    def is_cancelled(self) -> bool:
        """キャンセル状態確認"""
        with QMutexLocker(self._mutex):
            return self._is_cancelled
    
    def _search_with_progress(self) -> SearchResult:
        """進捗通知付きの検索実行"""
        import time
        from pathlib import Path
        
        start_time = time.time()
        result = SearchResult(criteria=self.criteria)
        
        try:
            self.progress_updated.emit(0, "検索対象ファイルを収集中...")
            
            # ファイル一覧を取得
            files = list(self.search_service._get_file_list(self.criteria))
            total_files = len(files)
            
            if total_files == 0:
                self.progress_updated.emit(100, "検索完了")
                result.search_duration = time.time() - start_time
                return result
            
            self.progress_updated.emit(10, f"{total_files}件のファイルをスキャン中...")
            
            processed_count = 0
            
            for file_path in files:
                if self.is_cancelled():
                    break
                
                result.total_files_scanned += 1
                
                # ファイル情報を取得
                file_info = self.search_service._get_file_info(file_path)
                if not file_info:
                    continue
                
                # 検索条件に一致するかチェック
                if self.search_service._matches_criteria(file_path, file_info, self.criteria):
                    file_match = self.search_service._create_file_match(file_path, file_info, self.criteria)
                    result.add_match(file_match)
                    
                    # マッチファイルを通知
                    self.file_processed.emit(str(file_path))
                
                processed_count += 1
                
                # 進捗更新（10%〜90%の範囲）
                progress = 10 + int((processed_count / total_files) * 80)
                status = f"スキャン中... {processed_count}/{total_files} ({result.match_count}件マッチ)"
                self.progress_updated.emit(progress, status)
                
                # UI応答性のため少し待機
                if processed_count % 50 == 0:
                    self.msleep(1)
            
            if not self.is_cancelled():
                self.progress_updated.emit(100, f"検索完了 - {result.match_count}件のファイルがマッチ")
            
        finally:
            result.search_duration = time.time() - start_time
        
        return result


class AsyncSearchService:
    """非同期検索サービス"""
    
    def __init__(self):
        self.current_worker: Optional[SearchWorker] = None
    
    def start_search(self, criteria: SearchCriteria) -> SearchWorker:
        """非同期検索開始"""
        # 既存の検索があればキャンセル
        self.cancel_search()
        
        # 新しいワーカーを作成・開始
        self.current_worker = SearchWorker(criteria)
        return self.current_worker
    
    def cancel_search(self) -> None:
        """現在の検索をキャンセル"""
        if self.current_worker and self.current_worker.isRunning():
            self.current_worker.cancel()
            self.current_worker.wait(3000)  # 最大3秒待機
            
            if self.current_worker.isRunning():
                # 強制終了
                self.current_worker.terminate()
                self.current_worker.wait(1000)
        
        self.current_worker = None
    
    def is_searching(self) -> bool:
        """検索中かどうか"""
        return self.current_worker is not None and self.current_worker.isRunning()
    
    def cleanup(self) -> None:
        """リソースのクリーンアップ"""
        self.cancel_search()