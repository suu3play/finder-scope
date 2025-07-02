"""
テストランナー - 全テストの実行とカバレッジ計測
"""
import sys
import subprocess
from pathlib import Path
import json


def run_tests_with_coverage():
    """テストを実行してカバレッジを計測"""
    print("🧪 Finder Scope テストスイート実行開始")
    print("=" * 60)
    
    # プロジェクトルートディレクトリ
    project_root = Path(__file__).parent
    
    # Pythonパスを設定
    sys.path.insert(0, str(project_root))
    
    try:
        # 1. ユニットテスト実行
        print("\n📋 ユニットテスト実行中...")
        unit_result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/unit/", 
            "-v", 
            "--tb=short",
            "--cov=src",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov",
            "--cov-report=json:coverage.json"
        ], cwd=project_root, capture_output=True, text=True)
        
        print(unit_result.stdout)
        if unit_result.stderr:
            print("Warnings/Errors:")
            print(unit_result.stderr)
        
        # 2. 統合テスト実行
        print("\n🔗 統合テスト実行中...")
        integration_result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/integration/", 
            "-v", 
            "--tb=short"
        ], cwd=project_root, capture_output=True, text=True)
        
        print(integration_result.stdout)
        if integration_result.stderr:
            print("Warnings/Errors:")
            print(integration_result.stderr)
        
        # 3. GUIテスト実行
        print("\n🖥 GUIテスト実行中...")
        gui_result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/gui/", 
            "-v", 
            "--tb=short"
        ], cwd=project_root, capture_output=True, text=True)
        
        print(gui_result.stdout)
        if gui_result.stderr:
            print("Warnings/Errors:")
            print(gui_result.stderr)
        
        # 4. パフォーマンステスト実行
        print("\n⚡ パフォーマンステスト実行中...")
        perf_result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/performance/", 
            "-v", 
            "-m", "performance",
            "--tb=short"
        ], cwd=project_root, capture_output=True, text=True)
        
        print(perf_result.stdout)
        if perf_result.stderr:
            print("Warnings/Errors:")
            print(perf_result.stderr)
        
        # 5. カバレッジ結果の表示
        print("\n📊 テストカバレッジ結果")
        print("-" * 40)
        
        coverage_file = project_root / "coverage.json"
        if coverage_file.exists():
            with open(coverage_file, 'r') as f:
                coverage_data = json.load(f)
            
            total_coverage = coverage_data.get('totals', {}).get('percent_covered', 0)
            print(f"総合カバレッジ: {total_coverage:.1f}%")
            
            # ファイル別カバレッジ
            files = coverage_data.get('files', {})
            print("\nファイル別カバレッジ:")
            for file_path, file_data in sorted(files.items()):
                if 'src/' in file_path:
                    coverage_pct = file_data.get('summary', {}).get('percent_covered', 0)
                    filename = Path(file_path).name
                    print(f"  {filename:30} {coverage_pct:6.1f}%")
        
        # 6. 結果サマリー
        print("\n" + "=" * 60)
        print("📈 テスト実行結果サマリー")
        print(f"ユニットテスト:   {'✅ PASS' if unit_result.returncode == 0 else '❌ FAIL'}")
        print(f"統合テスト:       {'✅ PASS' if integration_result.returncode == 0 else '❌ FAIL'}")
        print(f"GUIテスト:        {'✅ PASS' if gui_result.returncode == 0 else '❌ FAIL'}")
        print(f"パフォーマンス:   {'✅ PASS' if perf_result.returncode == 0 else '❌ FAIL'}")
        
        overall_success = all(result.returncode == 0 for result in [
            unit_result, integration_result, gui_result, perf_result
        ])
        
        print(f"\n🎯 総合結果: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
        
        if coverage_file.exists():
            print(f"\n📊 詳細カバレッジレポート: {project_root / 'htmlcov' / 'index.html'}")
        
        return overall_success
    
    except Exception as e:
        print(f"❌ テスト実行中にエラーが発生しました: {e}")
        return False


def run_specific_test_category(category: str):
    """特定カテゴリのテストのみ実行"""
    project_root = Path(__file__).parent
    
    test_dirs = {
        "unit": "tests/unit/",
        "integration": "tests/integration/",
        "gui": "tests/gui/",
        "performance": "tests/performance/"
    }
    
    if category not in test_dirs:
        print(f"❌ 無効なテストカテゴリ: {category}")
        print(f"利用可能: {', '.join(test_dirs.keys())}")
        return False
    
    print(f"🧪 {category}テスト実行中...")
    
    cmd = [sys.executable, "-m", "pytest", test_dirs[category], "-v", "--tb=short"]
    
    if category == "performance":
        cmd.extend(["-m", "performance"])
    
    result = subprocess.run(cmd, cwd=project_root)
    
    return result.returncode == 0


def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Finder Scope テストランナー")
    parser.add_argument("--category", "-c", 
                       choices=["unit", "integration", "gui", "performance"],
                       help="実行するテストカテゴリを指定")
    parser.add_argument("--all", "-a", action="store_true",
                       help="全テストを実行（デフォルト）")
    
    args = parser.parse_args()
    
    if args.category:
        success = run_specific_test_category(args.category)
    else:
        success = run_tests_with_coverage()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()