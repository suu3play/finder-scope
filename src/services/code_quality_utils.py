"""
コード品質向上ユーティリティ
"""
import ast
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class CodeIssue:
    """コード品質の問題を表すクラス"""
    file_path: Path
    line_number: int
    issue_type: str
    message: str
    severity: str  # "error", "warning", "info"


class CodeQualityAnalyzer:
    """コード品質分析クラス"""
    
    def __init__(self):
        self.issues: List[CodeIssue] = []
    
    def analyze_python_file(self, file_path: Path) -> List[CodeIssue]:
        """Pythonファイルの品質分析"""
        self.issues.clear()
        
        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.splitlines()
            
            # AST解析
            try:
                tree = ast.parse(content)
                self._analyze_ast(tree, file_path, lines)
            except SyntaxError as e:
                self.issues.append(CodeIssue(
                    file_path=file_path,
                    line_number=e.lineno or 1,
                    issue_type="syntax_error",
                    message=f"構文エラー: {e.msg}",
                    severity="error"
                ))
            
            # 行レベルの分析
            self._analyze_lines(file_path, lines)
            
        except Exception as e:
            self.issues.append(CodeIssue(
                file_path=file_path,
                line_number=1,
                issue_type="file_error",
                message=f"ファイル読み込みエラー: {e}",
                severity="error"
            ))
        
        return self.issues.copy()
    
    def _analyze_ast(self, tree: ast.AST, file_path: Path, lines: List[str]) -> None:
        """AST分析"""
        for node in ast.walk(tree):
            # 長い関数の検出
            if isinstance(node, ast.FunctionDef):
                self._check_function_length(node, file_path, lines)
                self._check_function_complexity(node, file_path)
            
            # 長いクラスの検出
            elif isinstance(node, ast.ClassDef):
                self._check_class_length(node, file_path, lines)
            
            # 深いネストの検出
            elif isinstance(node, (ast.If, ast.For, ast.While, ast.With)):
                depth = self._calculate_nesting_depth(node)
                if depth > 4:
                    self.issues.append(CodeIssue(
                        file_path=file_path,
                        line_number=node.lineno,
                        issue_type="deep_nesting",
                        message=f"ネストが深すぎます (深度: {depth})",
                        severity="warning"
                    ))
    
    def _check_function_length(self, node: ast.FunctionDef, file_path: Path, lines: List[str]) -> None:
        """関数の長さをチェック"""
        start_line = node.lineno - 1
        end_line = node.end_lineno - 1 if node.end_lineno else len(lines)
        
        # 実際のコード行数を計算（空行とコメントを除く）
        code_lines = 0
        for i in range(start_line, min(end_line, len(lines))):
            line = lines[i].strip()
            if line and not line.startswith('#'):
                code_lines += 1
        
        if code_lines > 50:
            self.issues.append(CodeIssue(
                file_path=file_path,
                line_number=node.lineno,
                issue_type="long_function",
                message=f"関数 '{node.name}' が長すぎます ({code_lines}行)",
                severity="warning"
            ))
    
    def _check_function_complexity(self, node: ast.FunctionDef, file_path: Path) -> None:
        """関数の複雑度をチェック（循環的複雑度の簡易版）"""
        complexity = 1  # 基本複雑度
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
        
        if complexity > 10:
            self.issues.append(CodeIssue(
                file_path=file_path,
                line_number=node.lineno,
                issue_type="complex_function",
                message=f"関数 '{node.name}' の複雑度が高すぎます (複雑度: {complexity})",
                severity="warning"
            ))
    
    def _check_class_length(self, node: ast.ClassDef, file_path: Path, lines: List[str]) -> None:
        """クラスの長さをチェック"""
        start_line = node.lineno - 1
        end_line = node.end_lineno - 1 if node.end_lineno else len(lines)
        
        # メソッド数をカウント
        method_count = sum(1 for child in node.body if isinstance(child, ast.FunctionDef))
        
        if method_count > 20:
            self.issues.append(CodeIssue(
                file_path=file_path,
                line_number=node.lineno,
                issue_type="large_class",
                message=f"クラス '{node.name}' のメソッド数が多すぎます ({method_count}個)",
                severity="warning"
            ))
    
    def _calculate_nesting_depth(self, node: ast.AST, current_depth: int = 0) -> int:
        """ネストの深さを計算"""
        max_depth = current_depth
        
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                child_depth = self._calculate_nesting_depth(child, current_depth + 1)
                max_depth = max(max_depth, child_depth)
        
        return max_depth
    
    def _analyze_lines(self, file_path: Path, lines: List[str]) -> None:
        """行レベルの分析"""
        for i, line in enumerate(lines, 1):
            # 長い行の検出
            if len(line) > 88:
                self.issues.append(CodeIssue(
                    file_path=file_path,
                    line_number=i,
                    issue_type="long_line",
                    message=f"行が長すぎます ({len(line)}文字)",
                    severity="info"
                ))
            
            # タブとスペースの混在検出
            if '\t' in line and '    ' in line:
                self.issues.append(CodeIssue(
                    file_path=file_path,
                    line_number=i,
                    issue_type="mixed_indentation",
                    message="タブとスペースが混在しています",
                    severity="warning"
                ))
            
            # 行末の空白検出
            if line.endswith(' ') or line.endswith('\t'):
                self.issues.append(CodeIssue(
                    file_path=file_path,
                    line_number=i,
                    issue_type="trailing_whitespace",
                    message="行末に不要な空白があります",
                    severity="info"
                ))


class CodeRefactoringSuggester:
    """コードリファクタリング提案クラス"""
    
    def __init__(self):
        self.suggestions: List[str] = []
    
    def analyze_project(self, project_path: Path) -> List[str]:
        """プロジェクト全体の分析と提案"""
        self.suggestions.clear()
        
        # Pythonファイルを収集
        python_files = list(project_path.rglob("*.py"))
        
        # 重複コードの検出
        self._detect_duplicate_code(python_files)
        
        # 命名規則の検証
        self._check_naming_conventions(python_files)
        
        # アーキテクチャの提案
        self._suggest_architecture_improvements(project_path)
        
        return self.suggestions.copy()
    
    def _detect_duplicate_code(self, python_files: List[Path]) -> None:
        """重複コードの検出"""
        code_blocks = {}
        
        for file_path in python_files:
            try:
                content = file_path.read_text(encoding="utf-8")
                lines = content.splitlines()
                
                # 5行以上の連続するブロックをチェック
                for i in range(len(lines) - 4):
                    block = '\n'.join(lines[i:i+5])
                    normalized_block = re.sub(r'\s+', ' ', block.strip())
                    
                    if len(normalized_block) > 50:  # 短すぎるブロックは除外
                        if normalized_block in code_blocks:
                            code_blocks[normalized_block].append((file_path, i + 1))
                        else:
                            code_blocks[normalized_block] = [(file_path, i + 1)]
            
            except Exception:
                continue
        
        # 重複が見つかった場合
        for block, locations in code_blocks.items():
            if len(locations) > 1:
                files_info = ", ".join([f"{path.name}:{line}" for path, line in locations])
                self.suggestions.append(
                    f"重複コードが検出されました: {files_info}\n"
                    f"  共通関数として抽出を検討してください"
                )
    
    def _check_naming_conventions(self, python_files: List[Path]) -> None:
        """命名規則の検証"""
        for file_path in python_files:
            try:
                content = file_path.read_text(encoding="utf-8")
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # 関数名の検証（snake_case）
                        if not re.match(r'^[a-z_][a-z0-9_]*$', node.name):
                            self.suggestions.append(
                                f"{file_path.name}:{node.lineno} - "
                                f"関数名 '{node.name}' はsnake_caseにすべきです"
                            )
                    
                    elif isinstance(node, ast.ClassDef):
                        # クラス名の検証（PascalCase）
                        if not re.match(r'^[A-Z][a-zA-Z0-9]*$', node.name):
                            self.suggestions.append(
                                f"{file_path.name}:{node.lineno} - "
                                f"クラス名 '{node.name}' はPascalCaseにすべきです"
                            )
            
            except Exception:
                continue
    
    def _suggest_architecture_improvements(self, project_path: Path) -> None:
        """アーキテクチャ改善提案"""
        # ディレクトリ構造の分析
        subdirs = [d for d in project_path.iterdir() if d.is_dir() and not d.name.startswith('.')]
        
        # テストディレクトリの確認
        test_dirs = [d for d in subdirs if 'test' in d.name.lower()]
        if not test_dirs:
            self.suggestions.append(
                "テストディレクトリが見つかりません。testsディレクトリの作成を推奨します"
            )
        
        # ドキュメントディレクトリの確認
        doc_dirs = [d for d in subdirs if d.name.lower() in ['docs', 'doc', 'documentation']]
        if not doc_dirs:
            self.suggestions.append(
                "ドキュメントディレクトリが見つかりません。docsディレクトリの作成を推奨します"
            )
        
        # 設定ファイルの確認
        config_files = list(project_path.glob("*.cfg")) + list(project_path.glob("*.ini")) + list(project_path.glob("*.toml"))
        if not config_files:
            self.suggestions.append(
                "設定ファイルが見つかりません。pyproject.tomlまたはsetup.cfgの作成を推奨します"
            )


class CodeFormatterChecker:
    """コードフォーマットチェッカー"""
    
    def check_python_formatting(self, file_path: Path) -> List[CodeIssue]:
        """Pythonファイルのフォーマットチェック"""
        issues = []
        
        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.splitlines()
            
            for i, line in enumerate(lines, 1):
                # インデントチェック（4スペース）
                if line.startswith(' ') and not line.startswith('    '):
                    leading_spaces = len(line) - len(line.lstrip(' '))
                    if leading_spaces % 4 != 0:
                        issues.append(CodeIssue(
                            file_path=file_path,
                            line_number=i,
                            issue_type="indentation",
                            message=f"インデントが4の倍数ではありません ({leading_spaces}スペース)",
                            severity="warning"
                        ))
                
                # import文の順序チェック
                if line.strip().startswith('from ') and i > 1:
                    prev_line = lines[i-2].strip()
                    if prev_line.startswith('import ') and not prev_line.startswith('from '):
                        issues.append(CodeIssue(
                            file_path=file_path,
                            line_number=i,
                            issue_type="import_order",
                            message="import文の順序が正しくありません（import -> from import）",
                            severity="info"
                        ))
        
        except Exception as e:
            issues.append(CodeIssue(
                file_path=file_path,
                line_number=1,
                issue_type="format_check_error",
                message=f"フォーマットチェックエラー: {e}",
                severity="error"
            ))
        
        return issues


def run_code_quality_analysis(project_path: Path) -> Dict[str, List]:
    """プロジェクト全体のコード品質分析実行"""
    analyzer = CodeQualityAnalyzer()
    refactoring_suggester = CodeRefactoringSuggester()
    formatter_checker = CodeFormatterChecker()
    
    results = {
        "issues": [],
        "suggestions": [],
        "format_issues": []
    }
    
    # Pythonファイルを収集
    python_files = list(project_path.rglob("*.py"))
    
    print(f"分析対象ファイル: {len(python_files)}個")
    
    # 各ファイルの分析
    for file_path in python_files:
        print(f"分析中: {file_path.relative_to(project_path)}")
        
        # コード品質分析
        file_issues = analyzer.analyze_python_file(file_path)
        results["issues"].extend(file_issues)
        
        # フォーマットチェック
        format_issues = formatter_checker.check_python_formatting(file_path)
        results["format_issues"].extend(format_issues)
    
    # プロジェクト全体の分析
    suggestions = refactoring_suggester.analyze_project(project_path)
    results["suggestions"] = suggestions
    
    return results


if __name__ == "__main__":
    # 現在のプロジェクトを分析
    project_path = Path(__file__).parent.parent
    results = run_code_quality_analysis(project_path)
    
    print("\n=== コード品質分析結果 ===")
    print(f"品質問題: {len(results['issues'])}件")
    print(f"リファクタリング提案: {len(results['suggestions'])}件")
    print(f"フォーマット問題: {len(results['format_issues'])}件")
    
    # 重要度別集計
    severity_counts = {}
    for issue in results["issues"] + results["format_issues"]:
        severity_counts[issue.severity] = severity_counts.get(issue.severity, 0) + 1
    
    print("\n重要度別:")
    for severity, count in severity_counts.items():
        print(f"  {severity}: {count}件")