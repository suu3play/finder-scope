"""
安全なアプリケーション実行用ランチャー（設定ダイアログ問題対策版）
"""
import sys
import os
from pathlib import Path

def main():
    """安全なアプリケーション実行"""
    # プロジェクトルートを設定
    project_root = Path(__file__).parent
    
    # Pythonパスに追加
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # 環境変数も設定
    os.environ['PYTHONPATH'] = str(project_root)
    
    print("🔒 Finder Scope 安全モード起動")
    print("設定ダイアログの無限ループ問題を回避します")
    
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import Qt, QTimer
        
        # アプリケーション作成
        app = QApplication(sys.argv)
        
        # アプリケーション情報設定
        app.setApplicationName("Finder Scope Safe")
        app.setApplicationVersion("1.0.0")
        app.setOrganizationName("Claude Code")
        
        print("✅ Qtアプリケーション初期化完了")
        
        # メインウィンドウを遅延作成（問題回避）
        def create_main_window():
            try:
                print("📱 メインウィンドウ作成開始...")
                from src.ui import MainWindow
                
                # ウィンドウ作成
                window = MainWindow()
                
                # ウィンドウ設定
                window.setWindowTitle("📁 Finder Scope - ファイル検索・置換ツール (安全モード)")
                
                # 設定ダイアログの自動表示を無効化
                if hasattr(window, 'settings_dialog_shown'):
                    window.settings_dialog_shown = False
                
                # ウィンドウ表示
                window.show()
                
                print("✅ メインウィンドウ表示完了")
                print("🚀 Finder Scope (安全モード) が起動しました")
                print("📁 フォルダを選択して検索を開始してください")
                
                return window
                
            except Exception as e:
                print(f"❌ メインウィンドウ作成エラー: {e}")
                import traceback
                traceback.print_exc()
                return None
        
        # 100ms後にメインウィンドウを作成（イベントループ安定化）
        window = None
        QTimer.singleShot(100, lambda: create_main_window())
        
        # イベントループ開始
        sys.exit(app.exec())
        
    except ImportError as e:
        print(f"❌ インポートエラー: {e}")
        print("必要な依存関係:")
        print("  pip install PySide6")
        return False
    except Exception as e:
        print(f"❌ 実行エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()