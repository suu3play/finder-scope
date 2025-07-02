"""
非同期検索サービスのユニットテスト
"""
import pytest
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication

from src.models import SearchCriteria
from src.services import AsyncSearchService


class TestAsyncSearchService:
    """AsyncSearchServiceのテスト"""
    
    @classmethod
    def setup_class(cls):
        """テストクラス前の準備"""
        # QApplicationが必要
        import sys
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication(sys.argv)
    
    def setup_method(self):
        """テストメソッド前の準備"""
        self.service = AsyncSearchService()
    
    def teardown_method(self):
        """テストメソッド後のクリーンアップ"""
        self.service.cleanup()
    
    def test_start_search(self):
        """非同期検索開始のテスト"""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # テストファイル作成
            (temp_path / "test.txt").write_text("test content")
            
            criteria = SearchCriteria(target_folder=temp_path)
            
            # 検索開始
            worker = self.service.start_search(criteria)
            
            assert worker is not None
            assert self.service.is_searching()
            
            # ワーカー完了まで待機
            worker.wait(5000)  # 最大5秒
            
            assert not self.service.is_searching()
    
    def test_cancel_search(self):
        """検索キャンセルのテスト"""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # 多数のファイルを作成（キャンセルしやすくするため）
            for i in range(100):
                (temp_path / f"file_{i}.txt").write_text(f"content {i}")
            
            criteria = SearchCriteria(target_folder=temp_path)
            
            # 検索開始
            worker = self.service.start_search(criteria)
            
            # すぐにキャンセル
            self.service.cancel_search()
            
            # ワーカー完了まで待機
            worker.wait(3000)
            
            assert not self.service.is_searching()
            assert worker.is_cancelled()
    
    def test_multiple_searches(self):
        """複数検索のテスト（前の検索はキャンセルされる）"""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "test.txt").write_text("test content")
            
            criteria = SearchCriteria(target_folder=temp_path)
            
            # 最初の検索開始
            worker1 = self.service.start_search(criteria)
            assert self.service.current_worker == worker1
            
            # 2番目の検索開始（1番目はキャンセルされる）
            worker2 = self.service.start_search(criteria)
            assert self.service.current_worker == worker2
            assert worker1 != worker2
            
            # 両方のワーカーの完了を待機
            worker1.wait(1000)
            worker2.wait(5000)
    
    def test_search_with_signals(self):
        """シグナル付き検索のテスト"""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # テストファイル作成
            (temp_path / "test.txt").write_text("test content")
            
            criteria = SearchCriteria(
                target_folder=temp_path,
                content_pattern="test"
            )
            
            # シグナル受信用のモック
            started_mock = Mock()
            finished_mock = Mock()
            progress_mock = Mock()
            
            # 検索開始
            worker = self.service.start_search(criteria)
            
            # シグナル接続
            worker.search_started.connect(started_mock)
            worker.search_finished.connect(finished_mock)
            worker.progress_updated.connect(progress_mock)
            
            # ワーカー開始
            worker.start()
            
            # 完了まで待機
            worker.wait(5000)
            
            # シグナルが呼ばれたことを確認
            started_mock.assert_called_once()
            finished_mock.assert_called_once()
            
            # 進捗シグナルは複数回呼ばれる
            assert progress_mock.call_count > 0
    
    def test_cleanup(self):
        """クリーンアップのテスト"""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "test.txt").write_text("test")
            
            criteria = SearchCriteria(target_folder=temp_path)
            
            # 検索開始
            worker = self.service.start_search(criteria)
            assert self.service.is_searching()
            
            # クリーンアップ実行
            self.service.cleanup()
            
            # 検索が停止していることを確認
            assert not self.service.is_searching()
            assert self.service.current_worker is None