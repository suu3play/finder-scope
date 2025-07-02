# Finder Scope トラブルシューティング

## 🚨 設定画面無限ループ問題

### 問題の症状
- アプリケーション起動時に設定画面が自動的に表示される
- OKや適用ボタンを押しても設定画面が再度表示される
- 検索ボタンを押すと「対象フォルダを選択してください」エラーが表示される

### 原因
1. **Qtイベントループの異常**: ダイアログの`exec()`メソッドが適切に終了していない
2. **シグナル接続の問題**: ボタンクリックイベントが意図しない動作を引き起こしている
3. **設定ファイルの問題**: 破損した設定ファイルまたは権限エラー
4. **キーボードショートカットの誤作動**: `Ctrl+,`が意図せず実行されている

### 対策

#### 1. 安全モードでの起動
```bash
python run_app_safe.py
```
このランチャーは設定ダイアログの自動表示を無効化し、遅延初期化でUIを安定化します。

#### 2. デバッグモードでの確認
```bash
python debug_startup.py
```
起動時の詳細なログを出力し、問題箇所を特定できます。

#### 3. 設定ファイルのリセット
```bash
# Linux/macOS
rm -rf ~/.finder_scope/

# Windows
del /s %USERPROFILE%\.finder_scope\
```

#### 4. 手動での設定ファイル作成
最小限の設定ファイルを手動作成：
```json
{
  "search": {
    "default_use_regex": false,
    "default_case_sensitive": false,
    "default_include_subdirectories": true,
    "max_file_size_mb": 10,
    "max_results": 10000,
    "excluded_extensions": [".exe", ".dll", ".bin"],
    "excluded_folders": [".git", "__pycache__", "node_modules"]
  },
  "ui": {
    "window_width": 1000,
    "window_height": 700,
    "window_maximized": false,
    "font_family": "Segoe UI",
    "font_size": 9,
    "theme": "default",
    "show_tooltips": true,
    "auto_save_settings": true
  },
  "recent_folders": [],
  "recent_patterns": []
}
```

### 実装済み修正内容

#### MainWindow.py
- 設定ダイアログ表示フラグ追加 (`settings_dialog_shown`)
- 重複表示防止機構
- キーボードショートカットを`Ctrl+Shift+,`に変更
- デバッグログ追加

#### SettingsDialog.py
- `done()`メソッドによる明示的ダイアログ終了
- エラーハンドリング強化
- デバッグログ追加

#### SettingsManager.py
- 例外安全な初期化処理
- フォールバック設定ファイルパス
- エラー時のデフォルト設定使用

### 緊急回避方法

#### 方法1: 最小構成での起動
```python
# minimal_app.py
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget

app = QApplication(sys.argv)
window = QMainWindow()
window.setWindowTitle("Finder Scope - Minimal Mode")
window.setGeometry(100, 100, 800, 600)

central_widget = QWidget()
layout = QVBoxLayout(central_widget)
layout.addWidget(QLabel("Finder Scope - 最小構成モード\n設定画面の問題を回避しています"))

window.setCentralWidget(central_widget)
window.show()

sys.exit(app.exec())
```

#### 方法2: 設定機能を無効化
`src/ui/main_window.py`の`create_menu_bar()`メソッドで設定メニューをコメントアウト：
```python
# settings_action = file_menu.addAction("設定(&S)...")
# settings_action.setShortcut("Ctrl+Shift+,")
# settings_action.triggered.connect(self.show_settings_dialog)
```

### 予防策

1. **定期的な設定ファイルバックアップ**
   ```bash
   cp ~/.finder_scope/settings.json ~/.finder_scope/settings.json.backup
   ```

2. **ログファイルによる問題追跡**
   起動時の詳細ログをファイルに保存

3. **段階的な機能有効化**
   - 基本機能のみで起動
   - 安定性確認後に高度な機能を有効化

### 技術的詳細

#### Qt イベントループの問題
- `QDialog.exec()`が適切にイベントループを終了しない場合がある
- `done(DialogCode)`による明示的終了が必要
- モーダルダイアログの親子関係が重要

#### シグナル・スロット接続
- 重複した信号接続による予期しない動作
- ラムダ式使用時のオブジェクト寿命管理
- QTimer.singleShot()による遅延実行の活用

#### ファイルシステム権限
- ~/.finder_scope/ ディレクトリの作成権限
- 設定ファイルの読み書き権限
- OneDrive同期による競合状態

このトラブルシューティングガイドにより、設定画面の無限ループ問題を解決できます。