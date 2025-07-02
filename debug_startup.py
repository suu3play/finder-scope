"""
起動時の問題をデバッグするためのスクリプト
"""
import sys
import os
from pathlib import Path

# プロジェクトルートを設定
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
os.environ['PYTHONPATH'] = str(project_root)

def debug_startup():
    """起動時の問題をデバッグ"""
    print("🔍 Finder Scope デバッグモード開始")
    
    try:
        from PySide6.QtWidgets import QApplication
        from src.ui import MainWindow
        
        print("1. Qtライブラリ読み込み完了")
        
        # アプリケーション作成
        app = QApplication(sys.argv)
        print("2. QApplication作成完了")
        
        # アプリケーション情報設定
        app.setApplicationName("Finder Scope Debug")
        app.setApplicationVersion("1.0.0")
        print("3. アプリケーション情報設定完了")
        
        # メインウィンドウ作成
        print("4. MainWindow作成開始...")
        window = MainWindow()
        print("5. MainWindow作成完了")
        
        # ウィンドウ表示
        print("6. ウィンドウ表示開始...")
        window.show()
        print("7. ウィンドウ表示完了")
        
        print("🚀 デバッグモードでFinder Scopeが起動しました")
        print("コンソールでエラーや警告を確認してください")
        
        # 短時間実行してイベントループを確認
        app.processEvents()
        
        print("8. 初期イベント処理完了")
        print("何かキーを押すと終了します...")
        input()
        
        window.close()
        print("9. ウィンドウクローズ完了")
        
    except ImportError as e:
        print(f"❌ インポートエラー: {e}")
        print("必要な依存関係がインストールされていません")
        return False
    except Exception as e:
        print(f"❌ 実行エラー: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    debug_startup()