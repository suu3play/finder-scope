"""
Finder Scope デモ実行スクリプト
アプリケーションの基本動作を確認
"""
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

# パッケージパスを追加
sys.path.insert(0, str(Path(__file__).parent))

from src.models import SearchCriteria, SearchResult
from src.services import FileSearchService


def create_demo_files(demo_dir: Path) -> None:
    """デモ用ファイル作成"""
    print(f"📁 デモファイルを作成中: {demo_dir}")
    
    # 各種ファイルを作成
    files_to_create = [
        ("test_file.txt", "This is a test file with some content."),
        ("example.py", "# Python example\nprint('Hello, World!')"),
        ("data.csv", "name,age,city\nJohn,30,Tokyo\nJane,25,Osaka"),
        ("log_file.log", "2025-06-27 10:30:00 INFO Application started\n2025-06-27 10:30:01 DEBUG Loading config"),
        ("readme.md", "# Sample Project\nThis is a sample project for testing."),
        ("config.json", '{"setting": "value", "debug": true}'),
    ]
    
    # サブディレクトリも作成
    sub_dir = demo_dir / "subdirectory"
    sub_dir.mkdir()
    
    sub_files = [
        ("sub_test.txt", "File in subdirectory with test keyword"),
        ("nested.py", "# Nested Python file\ntest_function()"),
    ]
    
    # メインディレクトリのファイル作成
    for filename, content in files_to_create:
        file_path = demo_dir / filename
        file_path.write_text(content, encoding="utf-8")
        print(f"  ✓ {filename}")
    
    # サブディレクトリのファイル作成
    for filename, content in sub_files:
        file_path = sub_dir / filename
        file_path.write_text(content, encoding="utf-8")
        print(f"  ✓ subdirectory/{filename}")


def demo_filename_search(demo_dir: Path, service: FileSearchService) -> None:
    """ファイル名検索のデモ"""
    print("\n🔍 ファイル名検索デモ: 'test' を含むファイル")
    
    criteria = SearchCriteria(
        target_folder=demo_dir,
        filename_pattern="test",
        include_subdirectories=True
    )
    
    result = service.search(criteria)
    print(f"結果: {result.get_summary()}")
    
    for file_match in result.matches:
        print(f"  📄 {file_match.filename} ({file_match.size_formatted})")


def demo_extension_filter(demo_dir: Path, service: FileSearchService) -> None:
    """拡張子フィルタのデモ"""
    print("\n🔍 拡張子フィルタデモ: .py ファイルのみ")
    
    criteria = SearchCriteria(
        target_folder=demo_dir,
        file_extensions=[".py"],
        include_subdirectories=True
    )
    
    result = service.search(criteria)
    print(f"結果: {result.get_summary()}")
    
    for file_match in result.matches:
        print(f"  🐍 {file_match.filename} - {file_match.folder_path}")


def demo_content_search(demo_dir: Path, service: FileSearchService) -> None:
    """内容検索のデモ"""
    print("\n🔍 内容検索デモ: 'test' を含む内容")
    
    criteria = SearchCriteria(
        target_folder=demo_dir,
        content_pattern="test",
        include_subdirectories=True
    )
    
    result = service.search(criteria)
    print(f"結果: {result.get_summary()}")
    
    for file_match in result.matches:
        print(f"  📄 {file_match.filename} ({file_match.match_count}箇所)")
        for content_match in file_match.matches:
            print(f"    行{content_match.line_number}: {content_match.context_preview}")


def demo_regex_search(demo_dir: Path, service: FileSearchService) -> None:
    """正規表現検索のデモ"""
    print("\n🔍 正規表現検索デモ: '\\.(txt|py)$' パターン")
    
    criteria = SearchCriteria(
        target_folder=demo_dir,
        filename_pattern=r"\.(txt|py)$",
        use_regex=True,
        include_subdirectories=True
    )
    
    result = service.search(criteria)
    print(f"結果: {result.get_summary()}")
    
    for file_match in result.matches:
        print(f"  📄 {file_match.filename}")


def main() -> None:
    """デモメイン関数"""
    print("🚀 Finder Scope デモ実行開始")
    print("=" * 50)
    
    with TemporaryDirectory() as temp_dir:
        demo_dir = Path(temp_dir)
        
        # デモファイル作成
        create_demo_files(demo_dir)
        
        # 検索サービス初期化
        service = FileSearchService()
        
        # 各種検索デモ実行
        demo_filename_search(demo_dir, service)
        demo_extension_filter(demo_dir, service)
        demo_content_search(demo_dir, service)
        demo_regex_search(demo_dir, service)
        
        print("\n" + "=" * 50)
        print("✅ デモ実行完了！")
        print("💡 GUI版を起動するには: python src/main.py")


if __name__ == "__main__":
    main()