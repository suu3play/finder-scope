"""
アプリケーション実行用ランチャー（インポート問題回避版）
"""
import sys
import os
from pathlib import Path

def main():
    """アプリケーション実行"""
    # プロジェクトルートを設定
    project_root = Path(__file__).parent
    
    # Pythonパスに追加
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # 環境変数も設定
    os.environ['PYTHONPATH'] = str(project_root)
    
    try:
        from PySide6.QtWidgets import QApplication
        from src.ui import MainWindow
        
        # アプリケーション作成
        app = QApplication(sys.argv)
        
        # アプリケーション情報設定
        app.setApplicationName("Finder Scope")
        app.setApplicationVersion("1.0.0")
        app.setOrganizationName("Claude Code")
        
        # メインウィンドウ作成・表示
        window = MainWindow()
        window.show()
        
        print("🚀 Finder Scope が起動しました")
        print("📁 フォルダを選択して検索を開始してください")
        
        # イベントループ開始
        sys.exit(app.exec())
        
    except ImportError as e:
        print(f"インポートエラー: {e}")
        print("必要な依存関係:")
        print("  pip install PySide6")
        return False
    except Exception as e:
        print(f"実行エラー: {e}")
        return False

if __name__ == "__main__":
    main()