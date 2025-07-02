"""
Finder Scope Phase 2 デモ実行スクリプト
Phase 2で追加された機能の動作確認
"""
import sys
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from datetime import datetime, timedelta

# パッケージパスを追加
sys.path.insert(0, str(Path(__file__).parent))
os.environ['PYTHONPATH'] = str(Path(__file__).parent)

from src.models import SearchCriteria, ReplaceOperation
from src.services import FileSearchService, ExportService, FileReplaceService


def create_demo_files_phase2(demo_dir: Path) -> None:
    """Phase 2 デモ用ファイル作成"""
    print(f"📁 Phase 2 デモファイルを作成中: {demo_dir}")
    
    # 現在日時と過去の日時
    now = datetime.now()
    old_time = now - timedelta(days=30)
    
    # 各種ファイルを作成
    files_data = [
        ("recent_file.txt", "This is a recent test file.", now),
        ("old_file.txt", "This is an old test document.", old_time),
        ("config.json", '{"test": "value", "debug": true}', now),
        ("log_2025.log", "2025-06-27 INFO: Application started\n2025-06-27 DEBUG: test message", now),
        ("readme.md", "# Test Project\nThis contains test information.", now),
        ("script.py", "# Python test script\nprint('test output')\ntest_variable = 42", now),
    ]
    
    # サブディレクトリ作成
    sub_dir = demo_dir / "subdir"
    sub_dir.mkdir()
    
    sub_files_data = [
        ("nested_test.txt", "Nested file with test content", old_time),
        ("backup.bak", "Backup file content", old_time),
    ]
    
    # メインディレクトリのファイル作成
    for filename, content, mod_time in files_data:
        file_path = demo_dir / filename
        file_path.write_text(content, encoding="utf-8")
        # 更新日時を設定
        timestamp = mod_time.timestamp()
        os.utime(file_path, (timestamp, timestamp))
        print(f"  ✓ {filename} (更新日: {mod_time.strftime('%Y-%m-%d')})")
    
    # サブディレクトリのファイル作成
    for filename, content, mod_time in sub_files_data:
        file_path = sub_dir / filename
        file_path.write_text(content, encoding="utf-8")
        timestamp = mod_time.timestamp()
        os.utime(file_path, (timestamp, timestamp))
        print(f"  ✓ subdir/{filename} (更新日: {mod_time.strftime('%Y-%m-%d')})")


def demo_date_filter(demo_dir: Path, service: FileSearchService) -> None:
    """更新日フィルタのデモ"""
    print("\n📅 更新日フィルタデモ: 最近1週間のファイル")
    
    one_week_ago = datetime.now() - timedelta(days=7)
    
    criteria = SearchCriteria(
        target_folder=demo_dir,
        date_from=one_week_ago,
        include_subdirectories=True
    )
    
    result = service.search(criteria)
    print(f"結果: {result.get_summary()}")
    
    for file_match in result.matches:
        print(f"  📄 {file_match.filename} - 更新日: {file_match.modified_date.strftime('%Y-%m-%d %H:%M')}")


def demo_csv_export(demo_dir: Path, service: FileSearchService, export_service: ExportService) -> None:
    """CSV出力のデモ"""
    print("\n📤 CSV出力デモ")
    
    criteria = SearchCriteria(
        target_folder=demo_dir,
        content_pattern="test",
        include_subdirectories=True
    )
    
    result = service.search(criteria)
    print(f"検索結果: {result.get_summary()}")
    
    # CSV出力
    output_path = demo_dir / "demo_export.csv"
    success = export_service.export_to_csv(result, output_path)
    
    if success:
        print(f"  ✅ CSV出力完了: {output_path}")
        print(f"  📊 ファイルサイズ: {output_path.stat().st_size} bytes")
    else:
        print("  ❌ CSV出力に失敗")


def demo_json_export(demo_dir: Path, service: FileSearchService, export_service: ExportService) -> None:
    """JSON出力のデモ"""
    print("\n📋 JSON出力デモ")
    
    criteria = SearchCriteria(
        target_folder=demo_dir,
        filename_pattern="test",
        file_extensions=[".txt", ".py"],
        include_subdirectories=True
    )
    
    result = service.search(criteria)
    
    # JSON出力
    output_path = demo_dir / "demo_export.json"
    success = export_service.export_to_json(result, output_path)
    
    if success:
        print(f"  ✅ JSON出力完了: {output_path}")
        # JSON内容の一部表示
        import json
        with output_path.open('r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"  📊 エクスポート情報: {data['export_info']['timestamp']}")
    else:
        print("  ❌ JSON出力に失敗")


def demo_html_export(demo_dir: Path, service: FileSearchService, export_service: ExportService) -> None:
    """HTML出力のデモ"""
    print("\n🌐 HTML出力デモ")
    
    criteria = SearchCriteria(
        target_folder=demo_dir,
        content_pattern="test",
        use_regex=False,
        case_sensitive=False,
        include_subdirectories=True
    )
    
    result = service.search(criteria)
    
    # HTML出力
    output_path = demo_dir / "demo_report.html"
    success = export_service.export_to_html(result, output_path)
    
    if success:
        print(f"  ✅ HTML出力完了: {output_path}")
        print(f"  🌐 ブラウザで開けるレポートが作成されました")
    else:
        print("  ❌ HTML出力に失敗")


def demo_file_replacement(demo_dir: Path, replace_service: FileReplaceService) -> None:
    """ファイル置換のデモ"""
    print("\n🔄 ファイル置換デモ")
    
    # 置換用のテストファイル作成
    test_file = demo_dir / "replace_test.txt"
    test_file.write_text("Hello world! This is a test world.\nAnother test line.", encoding="utf-8")
    print(f"  📝 テストファイル作成: {test_file.name}")
    
    # FileMatchオブジェクト作成
    from src.models import FileMatch
    file_match = FileMatch(
        file_path=test_file,
        filename=test_file.name,
        folder_path=test_file.parent,
        modified_date=datetime.now(),
        file_size=test_file.stat().st_size
    )
    
    # 置換操作設定
    operation = ReplaceOperation(
        search_pattern="world",
        replace_text="universe",
        use_regex=False,
        case_sensitive=True,
        create_backup=True
    )
    operation.add_target_file(file_match)
    
    # 置換プレビュー
    print("\n  👁 置換プレビュー:")
    preview_results = replace_service.preview_replace(operation)
    for file_preview in preview_results:
        for change in file_preview["changes"]:
            print(f"    行{change['line_number']}: '{change['original']}' → '{change['replaced']}'")
    
    # 置換実行
    print("\n  🔄 置換実行:")
    result = replace_service.replace(operation)
    print(f"  結果: {result.get_summary()}")
    
    if result.success_count > 0:
        # 置換後の内容確認
        new_content = test_file.read_text(encoding="utf-8")
        print(f"  📄 置換後の内容:")
        for i, line in enumerate(new_content.split('\n'), 1):
            print(f"    {i}: {line}")
        
        # バックアップファイル確認
        if result.backup_files:
            backup_file = result.backup_files[0]
            print(f"  💾 バックアップファイル: {backup_file.name}")


def main() -> None:
    """Phase 2 デモメイン関数"""
    print("🚀 Finder Scope Phase 2 デモ実行開始")
    print("新機能: 更新日フィルタ、置換機能、エクスポート機能、プレビュー機能")
    print("=" * 70)
    
    with TemporaryDirectory() as temp_dir:
        demo_dir = Path(temp_dir)
        
        # デモファイル作成
        create_demo_files_phase2(demo_dir)
        
        # サービス初期化
        search_service = FileSearchService()
        export_service = ExportService()
        replace_service = FileReplaceService()
        
        # 各種機能デモ実行
        demo_date_filter(demo_dir, search_service)
        demo_csv_export(demo_dir, search_service, export_service)
        demo_json_export(demo_dir, search_service, export_service)
        demo_html_export(demo_dir, search_service, export_service)
        demo_file_replacement(demo_dir, replace_service)
        
        print("\n" + "=" * 70)
        print("✅ Phase 2 デモ実行完了！")
        print("💡 追加された機能:")
        print("   📅 更新日によるファイルフィルタ")
        print("   📤 CSV/JSON/HTMLエクスポート")
        print("   🔄 ファイル内容の置換（バックアップ付き）")
        print("   👁 置換プレビュー機能")
        print("   🗂 フォルダを開く機能")
        print("   📄 ファイルプレビュー機能")
        print("\n💻 GUI版を起動するには: python run_app.py")


if __name__ == "__main__":
    main()