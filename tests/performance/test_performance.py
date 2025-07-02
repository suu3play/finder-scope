"""
パフォーマンステスト
"""
import pytest
import time
import tempfile
from pathlib import Path
from datetime import datetime
import random
import string
import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
os.environ['PYTHONPATH'] = str(Path(__file__).parent.parent.parent)

from src.models import SearchCriteria
from src.services import FileSearchService, AsyncSearchService


class TestSearchPerformance:
    """検索パフォーマンステスト"""
    
    def setup_method(self):
        """テストメソッド前の準備"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.service = FileSearchService()
        
    def teardown_method(self):
        """テストメソッド後のクリーンアップ"""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def create_large_dataset(self, num_files: int = 1000, num_subdirs: int = 10):
        """大量ファイルデータセット作成"""
        print(f"大量データセット作成中: {num_files}ファイル、{num_subdirs}サブディレクトリ")
        
        # メインディレクトリにファイル作成
        for i in range(num_files // 2):
            filename = f"file_{i:06d}.txt"
            content = self.generate_random_content(random.randint(100, 10000))
            (self.test_dir / filename).write_text(content, encoding="utf-8")
        
        # サブディレクトリ作成
        for subdir_idx in range(num_subdirs):
            subdir = self.test_dir / f"subdir_{subdir_idx:03d}"
            subdir.mkdir()
            
            # 各サブディレクトリにファイル作成
            files_per_subdir = num_files // 2 // num_subdirs
            for file_idx in range(files_per_subdir):
                filename = f"sub_file_{file_idx:06d}.txt"
                content = self.generate_random_content(random.randint(100, 5000))
                (subdir / filename).write_text(content, encoding="utf-8")
        
        print(f"データセット作成完了: {self.test_dir}")
    
    def generate_random_content(self, length: int) -> str:
        """ランダムなテキストコンテンツ生成"""
        words = ["test", "content", "data", "file", "search", "keyword", "text", 
                "document", "sample", "example", "performance", "benchmark"]
        
        content = []
        current_length = 0
        
        while current_length < length:
            if random.random() < 0.1:  # 10%の確率で特定キーワード
                word = "PERFORMANCE_TEST_KEYWORD"
            else:
                word = random.choice(words)
            
            content.append(word)
            current_length += len(word) + 1  # +1 はスペース分
        
        return " ".join(content)
    
    @pytest.mark.performance
    def test_filename_search_performance(self):
        """ファイル名検索パフォーマンステスト"""
        self.create_large_dataset(num_files=2000, num_subdirs=20)
        
        criteria = SearchCriteria(
            target_folder=self.test_dir,
            filename_pattern="file_*",
            include_subdirectories=True
        )
        
        start_time = time.time()
        result = self.service.search_files(criteria)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        print(f"ファイル名検索パフォーマンス:")
        print(f"  実行時間: {execution_time:.2f}秒")
        print(f"  検索結果: {result.match_count}件")
        print(f"  スループット: {result.match_count / execution_time:.1f}件/秒")
        
        # パフォーマンス基準: 2000ファイルを5秒以内で検索
        assert execution_time < 5.0, f"ファイル名検索が遅すぎます: {execution_time:.2f}秒"
        assert result.match_count > 0, "検索結果が見つかりませんでした"
    
    @pytest.mark.performance
    def test_content_search_performance(self):
        """内容検索パフォーマンステスト"""
        self.create_large_dataset(num_files=500, num_subdirs=5)
        
        criteria = SearchCriteria(
            target_folder=self.test_dir,
            content_pattern="PERFORMANCE_TEST_KEYWORD",
            include_subdirectories=True
        )
        
        start_time = time.time()
        result = self.service.search_files(criteria)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        print(f"内容検索パフォーマンス:")
        print(f"  実行時間: {execution_time:.2f}秒")
        print(f"  検索結果: {result.match_count}件")
        print(f"  スループット: {result.match_count / execution_time:.1f}件/秒")
        
        # パフォーマンス基準: 500ファイルの内容検索を10秒以内
        assert execution_time < 10.0, f"内容検索が遅すぎます: {execution_time:.2f}秒"
        assert result.match_count > 0, "検索結果が見つかりませんでした"
    
    @pytest.mark.performance
    def test_regex_search_performance(self):
        """正規表現検索パフォーマンステスト"""
        self.create_large_dataset(num_files=300, num_subdirs=3)
        
        criteria = SearchCriteria(
            target_folder=self.test_dir,
            content_pattern=r"test.*content",
            use_regex=True,
            include_subdirectories=True
        )
        
        start_time = time.time()
        result = self.service.search_files(criteria)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        print(f"正規表現検索パフォーマンス:")
        print(f"  実行時間: {execution_time:.2f}秒")
        print(f"  検索結果: {result.match_count}件")
        print(f"  スループット: {result.match_count / execution_time:.1f}件/秒")
        
        # パフォーマンス基準: 300ファイルの正規表現検索を15秒以内
        assert execution_time < 15.0, f"正規表現検索が遅すぎます: {execution_time:.2f}秒"
    
    @pytest.mark.performance
    def test_large_file_handling(self):
        """大きなファイルの処理パフォーマンステスト"""
        # 大きなファイル作成（10MB）
        large_content = "Large file content line.\n" * 500000
        large_file = self.test_dir / "large_file.txt"
        large_file.write_text(large_content, encoding="utf-8")
        
        # 通常サイズのファイルも作成
        for i in range(100):
            small_file = self.test_dir / f"small_{i:03d}.txt"
            small_file.write_text(f"Small file {i} with test content", encoding="utf-8")
        
        criteria = SearchCriteria(
            target_folder=self.test_dir,
            content_pattern="content",
            include_subdirectories=False
        )
        
        start_time = time.time()
        result = self.service.search_files(criteria)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        print(f"大きなファイル処理パフォーマンス:")
        print(f"  実行時間: {execution_time:.2f}秒")
        print(f"  検索結果: {result.match_count}件")
        print(f"  処理ファイル数: {len(result.matches)}件")
        
        # パフォーマンス基準: 大きなファイルを含む検索を20秒以内
        assert execution_time < 20.0, f"大きなファイル処理が遅すぎます: {execution_time:.2f}秒"


class TestAsyncSearchPerformance:
    """非同期検索パフォーマンステスト"""
    
    @classmethod
    def setup_class(cls):
        """テストクラス前の準備"""
        from PySide6.QtWidgets import QApplication
        import sys
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication(sys.argv)
    
    def setup_method(self):
        """テストメソッド前の準備"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.service = AsyncSearchService()
        
    def teardown_method(self):
        """テストメソッド後のクリーンアップ"""
        self.service.cleanup()
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def create_test_files(self, num_files: int = 1000):
        """テストファイル作成"""
        for i in range(num_files):
            filename = f"async_test_{i:06d}.txt"
            content = f"Async test file {i}\nContent with test keyword #{i}"
            (self.test_dir / filename).write_text(content, encoding="utf-8")
    
    @pytest.mark.performance
    def test_async_search_responsiveness(self):
        """非同期検索の応答性テスト"""
        self.create_test_files(num_files=2000)
        
        criteria = SearchCriteria(
            target_folder=self.test_dir,
            content_pattern="test",
            include_subdirectories=True
        )
        
        # 進捗更新の回数をカウント
        progress_updates = []
        
        def on_progress(progress, status):
            progress_updates.append((time.time(), progress, status))
        
        start_time = time.time()
        
        # 非同期検索開始
        worker = self.service.start_search(criteria)
        worker.progress_updated.connect(on_progress)
        worker.start()
        
        # 完了まで待機
        worker.wait(30000)  # 最大30秒
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"非同期検索応答性テスト:")
        print(f"  実行時間: {execution_time:.2f}秒")
        print(f"  進捗更新回数: {len(progress_updates)}回")
        
        if progress_updates:
            print(f"  最初の進捗更新: {progress_updates[0][2]}")
            print(f"  最後の進捗更新: {progress_updates[-1][2]}")
        
        # 応答性基準
        assert len(progress_updates) > 0, "進捗更新が発生していません"
        assert execution_time < 30.0, f"非同期検索が遅すぎます: {execution_time:.2f}秒"
    
    @pytest.mark.performance
    def test_cancellation_responsiveness(self):
        """キャンセル応答性テスト"""
        self.create_test_files(num_files=3000)
        
        criteria = SearchCriteria(
            target_folder=self.test_dir,
            content_pattern=".*",  # 全てにマッチする重い検索
            use_regex=True,
            include_subdirectories=True
        )
        
        # 検索開始
        worker = self.service.start_search(criteria)
        worker.start()
        
        # 少し待ってからキャンセル
        time.sleep(1.0)
        cancel_time = time.time()
        self.service.cancel_search()
        
        # キャンセル完了まで待機
        worker.wait(10000)  # 最大10秒
        completion_time = time.time()
        
        cancel_response_time = completion_time - cancel_time
        
        print(f"キャンセル応答性テスト:")
        print(f"  キャンセル応答時間: {cancel_response_time:.2f}秒")
        print(f"  キャンセル状態: {worker.is_cancelled()}")
        
        # キャンセル応答性基準
        assert worker.is_cancelled(), "検索がキャンセルされていません"
        assert cancel_response_time < 5.0, f"キャンセル応答が遅すぎます: {cancel_response_time:.2f}秒"


class TestMemoryUsage:
    """メモリ使用量テスト"""
    
    def setup_method(self):
        """テストメソッド前の準備"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.service = FileSearchService()
        
    def teardown_method(self):
        """テストメソッド後のクリーンアップ"""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def get_memory_usage(self):
        """現在のメモリ使用量を取得（MB）"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024  # MB
    
    @pytest.mark.performance
    def test_memory_usage_large_search(self):
        """大規模検索時のメモリ使用量テスト"""
        # 大量のファイル作成
        num_files = 1000
        for i in range(num_files):
            filename = f"memory_test_{i:06d}.txt"
            content = f"Memory test file {i}\n" + "Content line.\n" * 100
            (self.test_dir / filename).write_text(content, encoding="utf-8")
        
        # 検索前のメモリ使用量
        memory_before = self.get_memory_usage()
        
        criteria = SearchCriteria(
            target_folder=self.test_dir,
            content_pattern="test",
            include_subdirectories=True
        )
        
        result = self.service.search_files(criteria)
        
        # 検索後のメモリ使用量
        memory_after = self.get_memory_usage()
        memory_increase = memory_after - memory_before
        
        print(f"メモリ使用量テスト:")
        print(f"  検索前: {memory_before:.1f}MB")
        print(f"  検索後: {memory_after:.1f}MB")
        print(f"  増加量: {memory_increase:.1f}MB")
        print(f"  検索結果: {result.match_count}件")
        print(f"  ファイル当たり: {memory_increase / num_files * 1000:.1f}KB/ファイル")
        
        # メモリ使用量基準: 1000ファイルで100MB以下の増加
        assert memory_increase < 100.0, f"メモリ使用量が多すぎます: {memory_increase:.1f}MB"


if __name__ == "__main__":
    # パフォーマンステストのみ実行
    pytest.main([__file__, "-v", "-m", "performance"])