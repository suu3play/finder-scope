"""
テスト実行スクリプト
"""
import sys
import subprocess
from pathlib import Path

def run_tests():
    """テスト実行"""
    project_root = Path(__file__).parent
    
    # Pythonパスを設定
    sys.path.insert(0, str(project_root))
    
    try:
        # pytestを実行
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            "-v", "--tb=short"
        ], cwd=project_root, capture_output=True, text=True)
        
        print("=== テスト実行結果 ===")
        print(result.stdout)
        if result.stderr:
            print("=== エラー ===")
            print(result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"テスト実行エラー: {e}")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)