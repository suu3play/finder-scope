"""
エクスポート機能サービス
"""
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from src.models import SearchResult, FileMatch, ContentMatch


class ExportService:
    """検索結果のエクスポート機能を提供するサービスクラス"""
    
    def export_to_csv(self, search_result: SearchResult, output_path: Path) -> bool:
        """検索結果をCSVファイルにエクスポート"""
        try:
            with output_path.open('w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # ヘッダー行
                headers = [
                    'ファイル名',
                    'フォルダパス', 
                    '更新日時',
                    'ファイルサイズ',
                    'ファイルサイズ(バイト)',
                    'マッチ数',
                    'マッチ行番号',
                    'マッチ内容',
                    'ファイル拡張子'
                ]
                writer.writerow(headers)
                
                # データ行
                for file_match in search_result.matches:
                    if file_match.matches:
                        # 内容マッチがある場合、各マッチごとに行を作成
                        for content_match in file_match.matches:
                            row = [
                                file_match.filename,
                                str(file_match.folder_path),
                                file_match.modified_date.strftime('%Y/%m/%d %H:%M:%S'),
                                file_match.size_formatted,
                                file_match.file_size,
                                file_match.match_count,
                                content_match.line_number,
                                content_match.context_preview,
                                file_match.file_extension
                            ]
                            writer.writerow(row)
                    else:
                        # ファイル名のみマッチの場合
                        row = [
                            file_match.filename,
                            str(file_match.folder_path),
                            file_match.modified_date.strftime('%Y/%m/%d %H:%M:%S'),
                            file_match.size_formatted,
                            file_match.file_size,
                            0,  # マッチ数
                            '',  # マッチ行番号
                            '',  # マッチ内容
                            file_match.file_extension
                        ]
                        writer.writerow(row)
                
                # サマリー行を追加
                writer.writerow([])  # 空行
                writer.writerow(['=== 検索サマリー ==='])
                writer.writerow(['検索条件', '値'])
                writer.writerow(['対象フォルダ', str(search_result.criteria.target_folder)])
                writer.writerow(['ファイル名パターン', search_result.criteria.filename_pattern or ''])
                writer.writerow(['拡張子フィルタ', ','.join(search_result.criteria.file_extensions)])
                writer.writerow(['内容検索パターン', search_result.criteria.content_pattern or ''])
                writer.writerow(['正規表現使用', 'はい' if search_result.criteria.use_regex else 'いいえ'])
                writer.writerow(['大文字小文字区別', 'はい' if search_result.criteria.case_sensitive else 'いいえ'])
                writer.writerow(['サブディレクトリ含む', 'はい' if search_result.criteria.include_subdirectories else 'いいえ'])
                writer.writerow(['マッチファイル数', search_result.match_count])
                writer.writerow(['スキャンファイル数', search_result.total_files_scanned])
                writer.writerow(['実行時間(秒)', f'{search_result.search_duration:.2f}'])
                writer.writerow(['エクスポート日時', datetime.now().strftime('%Y/%m/%d %H:%M:%S')])
            
            return True
            
        except Exception as e:
            print(f"CSV出力エラー: {e}")
            return False
    
    def export_to_json(self, search_result: SearchResult, output_path: Path) -> bool:
        """検索結果をJSONファイルにエクスポート"""
        try:
            export_data = {
                'search_criteria': {
                    'target_folder': str(search_result.criteria.target_folder),
                    'filename_pattern': search_result.criteria.filename_pattern,
                    'file_extensions': search_result.criteria.file_extensions,
                    'date_from': search_result.criteria.date_from.isoformat() if search_result.criteria.date_from else None,
                    'date_to': search_result.criteria.date_to.isoformat() if search_result.criteria.date_to else None,
                    'content_pattern': search_result.criteria.content_pattern,
                    'use_regex': search_result.criteria.use_regex,
                    'case_sensitive': search_result.criteria.case_sensitive,
                    'include_subdirectories': search_result.criteria.include_subdirectories
                },
                'results': {
                    'match_count': search_result.match_count,
                    'total_files_scanned': search_result.total_files_scanned,
                    'search_duration': search_result.search_duration,
                    'total_content_matches': search_result.total_content_matches
                },
                'matches': [
                    self._file_match_to_dict(file_match) 
                    for file_match in search_result.matches
                ],
                'export_info': {
                    'timestamp': datetime.now().isoformat(),
                    'version': '1.0'
                }
            }
            
            with output_path.open('w', encoding='utf-8') as jsonfile:
                json.dump(export_data, jsonfile, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"JSON出力エラー: {e}")
            return False
    
    def export_to_html(self, search_result: SearchResult, output_path: Path) -> bool:
        """検索結果をHTMLファイルにエクスポート"""
        try:
            html_content = self._generate_html_report(search_result)
            
            with output_path.open('w', encoding='utf-8') as htmlfile:
                htmlfile.write(html_content)
            
            return True
            
        except Exception as e:
            print(f"HTML出力エラー: {e}")
            return False
    
    def _file_match_to_dict(self, file_match: FileMatch) -> Dict[str, Any]:
        """FileMatchオブジェクトを辞書に変換"""
        return {
            'file_path': str(file_match.file_path),
            'filename': file_match.filename,
            'folder_path': str(file_match.folder_path),
            'modified_date': file_match.modified_date.isoformat(),
            'file_size': file_match.file_size,
            'file_extension': file_match.file_extension,
            'match_count': file_match.match_count,
            'content_matches': [
                {
                    'line_number': match.line_number,
                    'matched_text': match.matched_text,
                    'context_before': match.context_before,
                    'context_after': match.context_after,
                    'start_position': match.start_position,
                    'end_position': match.end_position
                }
                for match in file_match.matches
            ]
        }
    
    def _generate_html_report(self, search_result: SearchResult) -> str:
        """HTML形式のレポートを生成"""
        html_template = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Finder Scope 検索結果レポート</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f5f5f5; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .criteria {{ background-color: #e8f4fd; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        .summary {{ background-color: #fff3cd; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; font-weight: bold; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        .file-path {{ font-family: monospace; font-size: 0.9em; }}
        .match-content {{ background-color: #ffffcc; padding: 2px 4px; border-radius: 3px; }}
        .no-results {{ text-align: center; color: #666; font-style: italic; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📁 Finder Scope 検索結果レポート</h1>
        <p>生成日時: {export_time}</p>
    </div>
    
    <div class="criteria">
        <h2>🔍 検索条件</h2>
        <ul>
            <li><strong>対象フォルダ:</strong> {target_folder}</li>
            <li><strong>ファイル名パターン:</strong> {filename_pattern}</li>
            <li><strong>拡張子フィルタ:</strong> {extensions}</li>
            <li><strong>内容検索:</strong> {content_pattern}</li>
            <li><strong>正規表現使用:</strong> {use_regex}</li>
            <li><strong>大文字小文字区別:</strong> {case_sensitive}</li>
            <li><strong>サブディレクトリ含む:</strong> {include_subdirs}</li>
        </ul>
    </div>
    
    <div class="summary">
        <h2>📊 検索結果サマリー</h2>
        <ul>
            <li><strong>マッチしたファイル数:</strong> {match_count} 件</li>
            <li><strong>スキャンしたファイル数:</strong> {total_scanned} 件</li>
            <li><strong>総コンテンツマッチ数:</strong> {total_content_matches} 箇所</li>
            <li><strong>実行時間:</strong> {duration:.2f} 秒</li>
        </ul>
    </div>
    
    {results_table}
</body>
</html>
        """
        
        # 検索条件の文字列化
        criteria = search_result.criteria
        target_folder = str(criteria.target_folder)
        filename_pattern = criteria.filename_pattern or "指定なし"
        extensions = ', '.join(criteria.file_extensions) if criteria.file_extensions else "指定なし"
        content_pattern = criteria.content_pattern or "指定なし"
        use_regex = "はい" if criteria.use_regex else "いいえ"
        case_sensitive = "はい" if criteria.case_sensitive else "いいえ"
        include_subdirs = "はい" if criteria.include_subdirectories else "いいえ"
        
        # 結果テーブルの生成
        if search_result.matches:
            results_table = "<h2>📄 検索結果詳細</h2>\n<table>\n"
            results_table += "<tr><th>ファイル名</th><th>フォルダパス</th><th>更新日時</th><th>サイズ</th><th>マッチ数</th></tr>\n"
            
            for file_match in search_result.matches:
                results_table += f"""
                <tr>
                    <td>{file_match.filename}</td>
                    <td class="file-path">{file_match.folder_path}</td>
                    <td>{file_match.modified_date.strftime('%Y/%m/%d %H:%M:%S')}</td>
                    <td>{file_match.size_formatted}</td>
                    <td>{file_match.match_count}</td>
                </tr>
                """
            
            results_table += "</table>"
        else:
            results_table = '<div class="no-results"><h2>検索結果</h2><p>マッチするファイルが見つかりませんでした。</p></div>'
        
        return html_template.format(
            export_time=datetime.now().strftime('%Y年%m月%d日 %H:%M:%S'),
            target_folder=target_folder,
            filename_pattern=filename_pattern,
            extensions=extensions,
            content_pattern=content_pattern,
            use_regex=use_regex,
            case_sensitive=case_sensitive,
            include_subdirs=include_subdirs,
            match_count=search_result.match_count,
            total_scanned=search_result.total_files_scanned,
            total_content_matches=search_result.total_content_matches,
            duration=search_result.search_duration,
            results_table=results_table
        )