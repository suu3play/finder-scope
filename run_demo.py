"""
デモ実行用ランチャー（インポート問題回避版）
"""
import sys
import os
from pathlib import Path

def main():
    """デモ実行"""
    # プロジェクトルートを設定
    project_root = Path(__file__).parent
    
    # Pythonパスに追加
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # 環境変数も設定
    os.environ['PYTHONPATH'] = str(project_root)
    
    try:
        # デモモジュールをインポートして実行
        import demo
        demo.main()
    except ImportError as e:
        print(f"インポートエラー: {e}")
        print("依存関係の確認:")
        
        # 基本的なファイル存在確認
        required_files = [
            "src/__init__.py",
            "src/models/__init__.py", 
            "src/services/__init__.py",
            "src/ui/__init__.py"
        ]
        
        for file_path in required_files:
            full_path = project_root / file_path
            status = "✓" if full_path.exists() else "✗"
            print(f"  {status} {file_path}")
        
        return False
    except Exception as e:
        print(f"実行エラー: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)