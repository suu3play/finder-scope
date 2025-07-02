"""
Finder Scope Phase 3 デモ実行スクリプト
Phase 3で追加された機能の動作確認
"""
import sys
import os
import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory
from datetime import datetime

# パッケージパスを追加
sys.path.insert(0, str(Path(__file__).parent))
os.environ['PYTHONPATH'] = str(Path(__file__).parent)

from src.models import SearchCriteria, SettingsManager
from src.services import AsyncSearchService


def create_demo_files_phase3(demo_dir: Path) -> None:
    """Phase 3 デモ用ファイル作成"""
    print(f"📁 Phase 3 デモファイルを作成中: {demo_dir}")
    
    # 大量のファイルを作成（非同期処理のテスト用）
    files_data = []
    
    # メインディレクトリに100個のファイル
    for i in range(100):
        content = f"This is test file #{i}\nContent with test keyword #{i}\nMore content here."
        files_data.append((f"file_{i:03d}.txt", content))
    
    # 各種形式のファイル
    files_data.extend([
        ("large_log.log", "ERROR: Test error message\n" * 1000),
        ("config.json", '{"test": true, "value": 42}'),
        ("script.py", "# Python test script\nprint('test')\ntest_var = 'value'"),
        ("readme.md", "# Test Project\nThis is a test document with test content."),
        ("data.csv", "name,value,test\ntest1,100,yes\ntest2,200,no\ntest3,300,yes"),
    ])
    
    # サブディレクトリも作成
    for subdir in ["subdir1", "subdir2", "subdir3"]:
        sub_path = demo_dir / subdir
        sub_path.mkdir()
        
        for i in range(20):
            file_path = sub_path / f"sub_{subdir}_{i:02d}.txt"
            content = f"Subdirectory file in {subdir}\nTest content #{i}"
            file_path.write_text(content, encoding="utf-8")
    
    # メインファイル作成
    for filename, content in files_data:
        file_path = demo_dir / filename
        file_path.write_text(content, encoding="utf-8")
        
        if len(filename) <= 15:  # 短いファイル名のみ表示
            print(f"  ✓ {filename}")
    
    print(f"  ✓ 合計 {len(files_data) + 60} 個のファイルを作成")


def demo_settings_manager() -> None:
    """設定マネージャーのデモ"""
    print("\n⚙️ 設定管理機能デモ")
    
    # 一時的な設定ファイルを使用
    with TemporaryDirectory() as temp_dir:
        settings_file = Path(temp_dir) / "test_settings.json"
        settings_manager = SettingsManager(settings_file)
        
        print("  📝 初期設定:")
        print(f"    デフォルト正規表現: {settings_manager.settings.search.default_use_regex}")
        print(f"    デフォルト大文字小文字区別: {settings_manager.settings.search.default_case_sensitive}")
        print(f"    最大ファイルサイズ: {settings_manager.settings.search.max_file_size_mb}MB")
        
        # 設定を変更
        print("\n  🔧 設定を変更:")
        settings_manager.settings.search.default_use_regex = True
        settings_manager.settings.search.max_file_size_mb = 50
        settings_manager.settings.ui.window_width = 1400
        settings_manager.settings.ui.theme = "dark"
        
        # 最近使用した項目を追加
        settings_manager.add_recent_folder("/test/folder1")
        settings_manager.add_recent_folder("/test/folder2")
        settings_manager.add_recent_pattern("test.*pattern")
        settings_manager.add_recent_pattern("another.+search")
        
        # 設定を保存
        if settings_manager.save_settings():
            print("    ✅ 設定を保存しました")
        
        print(f"    正規表現: {settings_manager.settings.search.default_use_regex}")
        print(f"    最大ファイルサイズ: {settings_manager.settings.search.max_file_size_mb}MB")
        print(f"    ウィンドウ幅: {settings_manager.settings.ui.window_width}")
        print(f"    テーマ: {settings_manager.settings.ui.theme}")
        print(f"    最近使用したフォルダ: {settings_manager.get_recent_folders()}")
        print(f"    最近使用したパターン: {settings_manager.get_recent_patterns()}")
        
        # 設定をエクスポート
        export_path = Path(temp_dir) / "exported_settings.json"
        if settings_manager.export_settings(export_path):
            print(f"    📤 設定をエクスポート: {export_path}")
            print(f"    ファイルサイズ: {export_path.stat().st_size} bytes")


def demo_async_search(demo_dir: Path) -> None:
    """非同期検索のデモ"""
    print("\n🚀 非同期検索機能デモ")
    
    # 検索条件設定
    criteria = SearchCriteria(
        target_folder=demo_dir,
        content_pattern="test",
        include_subdirectories=True
    )
    
    # 非同期検索サービス
    async_service = AsyncSearchService()
    
    # 進捗を表示するコールバック
    def on_progress(progress: int, status: str):
        print(f"    進捗: {progress:3d}% - {status}")
    
    def on_search_started():
        print("  🔍 検索開始")
    
    def on_search_finished(result):
        print(f"  ✅ 検索完了: {result.get_summary()}")
        print(f"    マッチファイル例:")
        for i, file_match in enumerate(result.matches[:5]):  # 最初の5件
            print(f"      {i+1}. {file_match.filename} ({file_match.match_count}箇所)")
        if len(result.matches) > 5:
            print(f"      ... 他 {len(result.matches)-5} 件")
    
    def on_search_error(error):
        print(f"  ❌ 検索エラー: {error}")
    
    # 検索実行
    worker = async_service.start_search(criteria)
    
    # シグナル接続（簡易版）
    worker.search_started.connect(on_search_started)
    worker.search_finished.connect(on_search_finished)
    worker.search_error.connect(on_search_error)
    worker.progress_updated.connect(on_progress)
    
    # ワーカー開始
    worker.start()
    
    # 完了まで待機（デモ用）
    worker.wait()
    
    # クリーンアップ
    async_service.cleanup()


def demo_search_cancellation(demo_dir: Path) -> None:
    """検索キャンセル機能のデモ"""
    print("\n⏹ 検索キャンセル機能デモ")
    
    # より重い検索条件
    criteria = SearchCriteria(
        target_folder=demo_dir,
        content_pattern=".*",  # 全てにマッチする正規表現
        use_regex=True,
        include_subdirectories=True
    )
    
    async_service = AsyncSearchService()
    
    def on_progress(progress: int, status: str):
        # 30%で強制キャンセル
        if progress >= 30:
            print(f"    進捗: {progress:3d}% - キャンセル実行!")
            async_service.cancel_search()
        else:
            print(f"    進捗: {progress:3d}% - {status}")
    
    def on_search_started():
        print("  🔍 検索開始（30%でキャンセル予定）")
    
    def on_search_finished(result):
        print(f"  ✅ 検索完了: {result.get_summary()}")
    
    def on_search_error(error):
        print(f"  ❌ 検索エラー: {error}")
    
    # 検索実行
    worker = async_service.start_search(criteria)
    
    # シグナル接続
    worker.search_started.connect(on_search_started)
    worker.search_finished.connect(on_search_finished)
    worker.search_error.connect(on_search_error)
    worker.progress_updated.connect(on_progress)
    
    # ワーカー開始
    worker.start()
    
    # 完了まで待機
    worker.wait()
    
    if worker.is_cancelled():
        print("  🛑 検索がキャンセルされました")
    
    # クリーンアップ
    async_service.cleanup()


def demo_error_handling() -> None:
    """エラーハンドリングのデモ"""
    print("\n🚨 エラーハンドリング機能デモ")
    
    # 存在しないフォルダで検索
    try:
        criteria = SearchCriteria(
            target_folder=Path("/nonexistent/folder"),
            filename_pattern="test"
        )
        print("  ❌ 想定外: エラーが発生しませんでした")
    except ValueError as e:
        print(f"  ✅ 適切にエラーをキャッチ: {e}")
    
    # 無効な正規表現のテスト
    from src.services import FileSearchService
    service = FileSearchService()
    
    try:
        result = service._simple_match("test string", "[invalid", False)
        print(f"  ✅ 無効な正規表現でもフォールバック: '{result}'")
    except Exception as e:
        print(f"  ❌ 想定外のエラー: {e}")


def main() -> None:
    """Phase 3 デモメイン関数"""
    print("🚀 Finder Scope Phase 3 デモ実行開始")
    print("新機能: 非同期検索、設定管理、キャンセル機能、UX改善")
    print("=" * 70)
    
    with TemporaryDirectory() as temp_dir:
        demo_dir = Path(temp_dir)
        
        # デモファイル作成
        create_demo_files_phase3(demo_dir)
        
        # 各種機能デモ実行
        demo_settings_manager()
        demo_async_search(demo_dir)
        demo_search_cancellation(demo_dir)
        demo_error_handling()
        
        print("\n" + "=" * 70)
        print("✅ Phase 3 デモ実行完了！")
        print("💡 追加された機能:")
        print("   🚀 非同期検索処理（応答性向上）")
        print("   ⚙️ 包括的な設定管理機能")
        print("   ⏹ 検索キャンセル機能")
        print("   📊 詳細な進捗表示")
        print("   🚨 エラーダイアログ・ハンドリング")
        print("   🎨 メニューバー・設定ダイアログ")
        print("   📱 ユーザーエクスペリエンス向上")
        print("\n💻 GUI版を起動するには: python run_app.py")
        print("🧪 全機能テスト: python demo.py && python demo_phase2.py && python demo_phase3.py")


if __name__ == "__main__":
    main()