using System;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using CsvHelper;
using FinderScope.Core.Models;

namespace FinderScope.Core.Services
{
    /// <summary>
    /// エクスポート機能の実装
    /// </summary>
    public class ExportService : IExportService
    {
        /// <summary>
        /// CSV形式でエクスポート
        /// </summary>
        public async Task ExportToCsvAsync(SearchResult searchResult, string filePath)
        {
            using var writer = new StreamWriter(filePath, false, Encoding.UTF8);
            using var csv = new CsvWriter(writer, CultureInfo.InvariantCulture);

            // ヘッダー行を書き込み
            csv.WriteField("ファイル名");
            csv.WriteField("ディレクトリ");
            csv.WriteField("ファイルサイズ");
            csv.WriteField("更新日時");
            csv.WriteField("マッチ数");
            csv.WriteField("マッチ内容");
            await csv.NextRecordAsync();

            // データ行を書き込み
            foreach (var fileMatch in searchResult.FileMatches)
            {
                csv.WriteField(fileMatch.FileName);
                csv.WriteField(fileMatch.Directory);
                csv.WriteField(fileMatch.FormattedSize);
                csv.WriteField(fileMatch.LastModified.ToString("yyyy/MM/dd HH:mm:ss"));
                csv.WriteField(fileMatch.MatchCount);
                csv.WriteField(string.Join("; ", fileMatch.GetAllMatchedTexts()));
                await csv.NextRecordAsync();
            }

            await writer.FlushAsync();
        }

        /// <summary>
        /// JSON形式でエクスポート
        /// </summary>
        public async Task ExportToJsonAsync(SearchResult searchResult, string filePath)
        {
            var exportData = new
            {
                SearchCriteria = new
                {
                    searchResult.Criteria.TargetFolder,
                    searchResult.Criteria.FilenamePattern,
                    searchResult.Criteria.FileExtensions,
                    searchResult.Criteria.DateFrom,
                    searchResult.Criteria.DateTo,
                    searchResult.Criteria.ContentPattern,
                    searchResult.Criteria.UseRegex,
                    searchResult.Criteria.CaseSensitive,
                    searchResult.Criteria.IncludeSubdirectories
                },
                SearchInfo = new
                {
                    searchResult.SearchStartTime,
                    searchResult.SearchDurationSeconds,
                    searchResult.TotalFilesScanned,
                    MatchedFilesCount = searchResult.MatchCount,
                    searchResult.TotalContentMatches
                },
                Results = searchResult.FileMatches.Select(fm => new
                {
                    fm.FileName,
                    fm.Directory,
                    fm.FilePath,
                    fm.FileSize,
                    FormattedSize = fm.FormattedSize,
                    fm.LastModified,
                    MatchCount = fm.MatchCount,
                    ContentMatches = fm.Matches.Select(cm => new
                    {
                        cm.LineNumber,
                        cm.MatchedText,
                        cm.StartPosition,
                        cm.EndPosition,
                        cm.ContextBefore,
                        cm.ContextAfter
                    })
                })
            };

            var options = new JsonSerializerOptions
            {
                WriteIndented = true,
                Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping
            };

            var json = JsonSerializer.Serialize(exportData, options);
            await File.WriteAllTextAsync(filePath, json, Encoding.UTF8);
        }

        /// <summary>
        /// HTML形式でエクスポート
        /// </summary>
        public async Task ExportToHtmlAsync(SearchResult searchResult, string filePath)
        {
            var html = new StringBuilder();
            
            // HTML構造の開始
            html.AppendLine("<!DOCTYPE html>");
            html.AppendLine("<html lang=\"ja\">");
            html.AppendLine("<head>");
            html.AppendLine("    <meta charset=\"UTF-8\">");
            html.AppendLine("    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">");
            html.AppendLine("    <title>Finder Scope - 検索結果</title>");
            html.AppendLine("    <style>");
            html.AppendLine(GetHtmlStyles());
            html.AppendLine("    </style>");
            html.AppendLine("</head>");
            html.AppendLine("<body>");

            // ヘッダー
            html.AppendLine("    <header>");
            html.AppendLine("        <h1>🔍 Finder Scope - 検索結果</h1>");
            html.AppendLine($"        <p class=\"timestamp\">生成日時: {DateTime.Now:yyyy年MM月dd日 HH:mm:ss}</p>");
            html.AppendLine("    </header>");

            // 検索条件サマリー
            html.AppendLine("    <section class=\"search-summary\">");
            html.AppendLine("        <h2>検索条件</h2>");
            html.AppendLine("        <div class=\"summary-grid\">");
            html.AppendLine($"            <div class=\"summary-item\"><strong>対象フォルダ:</strong> {EscapeHtml(searchResult.Criteria.TargetFolder)}</div>");
            
            if (!string.IsNullOrWhiteSpace(searchResult.Criteria.FilenamePattern))
                html.AppendLine($"            <div class=\"summary-item\"><strong>ファイル名:</strong> {EscapeHtml(searchResult.Criteria.FilenamePattern)}</div>");
            
            if (searchResult.Criteria.FileExtensions.Any())
                html.AppendLine($"            <div class=\"summary-item\"><strong>拡張子:</strong> {EscapeHtml(string.Join(", ", searchResult.Criteria.FileExtensions))}</div>");
            
            if (!string.IsNullOrWhiteSpace(searchResult.Criteria.ContentPattern))
                html.AppendLine($"            <div class=\"summary-item\"><strong>内容検索:</strong> {EscapeHtml(searchResult.Criteria.ContentPattern)}</div>");
            
            html.AppendLine($"            <div class=\"summary-item\"><strong>正規表現:</strong> {(searchResult.Criteria.UseRegex ? "有効" : "無効")}</div>");
            html.AppendLine($"            <div class=\"summary-item\"><strong>大文字小文字区別:</strong> {(searchResult.Criteria.CaseSensitive ? "有効" : "無効")}</div>");
            html.AppendLine("        </div>");
            html.AppendLine("    </section>");

            // 検索結果統計
            html.AppendLine("    <section class=\"search-stats\">");
            html.AppendLine("        <h2>検索結果統計</h2>");
            html.AppendLine("        <div class=\"stats-grid\">");
            html.AppendLine($"            <div class=\"stat-item\"><span class=\"stat-number\">{searchResult.TotalFilesScanned:N0}</span><span class=\"stat-label\">スキャンファイル数</span></div>");
            html.AppendLine($"            <div class=\"stat-item\"><span class=\"stat-number\">{searchResult.MatchCount:N0}</span><span class=\"stat-label\">マッチファイル数</span></div>");
            html.AppendLine($"            <div class=\"stat-item\"><span class=\"stat-number\">{searchResult.TotalContentMatches:N0}</span><span class=\"stat-label\">コンテンツマッチ数</span></div>");
            html.AppendLine($"            <div class=\"stat-item\"><span class=\"stat-number\">{searchResult.SearchDurationSeconds:F2}秒</span><span class=\"stat-label\">実行時間</span></div>");
            html.AppendLine("        </div>");
            html.AppendLine("    </section>");

            // 検索結果テーブル
            if (searchResult.FileMatches.Any())
            {
                html.AppendLine("    <section class=\"search-results\">");
                html.AppendLine("        <h2>検索結果一覧</h2>");
                html.AppendLine("        <table>");
                html.AppendLine("            <thead>");
                html.AppendLine("                <tr>");
                html.AppendLine("                    <th>ファイル名</th>");
                html.AppendLine("                    <th>ディレクトリ</th>");
                html.AppendLine("                    <th>サイズ</th>");
                html.AppendLine("                    <th>更新日時</th>");
                html.AppendLine("                    <th>マッチ数</th>");
                html.AppendLine("                    <th>マッチ内容</th>");
                html.AppendLine("                </tr>");
                html.AppendLine("            </thead>");
                html.AppendLine("            <tbody>");

                foreach (var fileMatch in searchResult.FileMatches)
                {
                    html.AppendLine("                <tr>");
                    html.AppendLine($"                    <td class=\"filename\">{EscapeHtml(fileMatch.FileName)}</td>");
                    html.AppendLine($"                    <td class=\"directory\">{EscapeHtml(fileMatch.Directory)}</td>");
                    html.AppendLine($"                    <td class=\"filesize\">{EscapeHtml(fileMatch.FormattedSize)}</td>");
                    html.AppendLine($"                    <td class=\"date\">{fileMatch.LastModified:yyyy/MM/dd HH:mm}</td>");
                    html.AppendLine($"                    <td class=\"match-count\">{fileMatch.MatchCount}</td>");
                    html.AppendLine($"                    <td class=\"matches\">{EscapeHtml(string.Join("; ", fileMatch.GetAllMatchedTexts().Take(3)))}</td>");
                    html.AppendLine("                </tr>");
                }

                html.AppendLine("            </tbody>");
                html.AppendLine("        </table>");
                html.AppendLine("    </section>");
            }

            // フッター
            html.AppendLine("    <footer>");
            html.AppendLine("        <p>Generated by Finder Scope - 高性能ファイル検索ツール</p>");
            html.AppendLine("    </footer>");

            html.AppendLine("</body>");
            html.AppendLine("</html>");

            await File.WriteAllTextAsync(filePath, html.ToString(), Encoding.UTF8);
        }

        /// <summary>
        /// HTMLエスケープ処理
        /// </summary>
        private static string EscapeHtml(string text)
        {
            if (string.IsNullOrEmpty(text)) return text;
            
            return text.Replace("&", "&amp;")
                      .Replace("<", "&lt;")
                      .Replace(">", "&gt;")
                      .Replace("\"", "&quot;")
                      .Replace("'", "&#39;");
        }

        /// <summary>
        /// HTMLスタイルを取得
        /// </summary>
        private static string GetHtmlStyles()
        {
            return @"
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f8f9fa;
            color: #333;
            line-height: 1.6;
        }
        
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
        }
        
        header h1 {
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }
        
        .timestamp {
            margin: 10px 0 0 0;
            opacity: 0.9;
            font-size: 0.9em;
        }
        
        section {
            background: white;
            padding: 25px;
            margin-bottom: 25px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        h2 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-top: 0;
        }
        
        .summary-grid, .stats-grid {
            display: grid;
            gap: 15px;
            margin-top: 20px;
        }
        
        .summary-grid {
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        }
        
        .stats-grid {
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        }
        
        .summary-item {
            padding: 12px;
            background-color: #f8f9fa;
            border-left: 4px solid #3498db;
            border-radius: 4px;
        }
        
        .stat-item {
            text-align: center;
            padding: 20px;
            background: linear-gradient(45deg, #f39c12, #e74c3c);
            color: white;
            border-radius: 8px;
        }
        
        .stat-number {
            display: block;
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .stat-label {
            font-size: 0.9em;
            opacity: 0.9;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        
        th {
            background-color: #34495e;
            color: white;
            font-weight: 600;
            position: sticky;
            top: 0;
        }
        
        tr:nth-child(even) {
            background-color: #f8f9fa;
        }
        
        tr:hover {
            background-color: #e8f4f8;
        }
        
        .filename {
            font-weight: 600;
            color: #2980b9;
        }
        
        .directory {
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            color: #7f8c8d;
        }
        
        .filesize, .date {
            text-align: center;
        }
        
        .match-count {
            text-align: center;
            font-weight: bold;
            color: #e74c3c;
        }
        
        .matches {
            font-family: 'Courier New', monospace;
            font-size: 0.85em;
            background-color: #fff3cd;
            padding: 5px;
            border-radius: 3px;
        }
        
        footer {
            text-align: center;
            padding: 20px;
            color: #7f8c8d;
            border-top: 1px solid #ecf0f1;
            margin-top: 30px;
        }
        
        @media (max-width: 768px) {
            body { padding: 10px; }
            header h1 { font-size: 2em; }
            .summary-grid, .stats-grid { grid-template-columns: 1fr; }
            table { font-size: 0.8em; }
            th, td { padding: 8px; }
        }";
        }

        /// <summary>
        /// TXT形式でエクスポート
        /// </summary>
        public async Task ExportToTxtAsync(SearchResult searchResult, string filePath)
        {
            var txt = new StringBuilder();
            
            // ヘッダー情報
            txt.AppendLine("=== Finder Scope 検索結果 ===");
            txt.AppendLine();
            txt.AppendLine($"検索実行日時: {searchResult.SearchStartTime:yyyy年MM月dd日 HH:mm:ss}");
            txt.AppendLine($"検索対象: {searchResult.Criteria.TargetFolder}");
            
            if (!string.IsNullOrWhiteSpace(searchResult.Criteria.FilenamePattern))
                txt.AppendLine($"ファイル名パターン: {searchResult.Criteria.FilenamePattern}");
            
            if (searchResult.Criteria.FileExtensions.Any())
                txt.AppendLine($"拡張子フィルタ: {string.Join(", ", searchResult.Criteria.FileExtensions)}");
            
            if (searchResult.Criteria.DateFrom.HasValue || searchResult.Criteria.DateTo.HasValue)
            {
                var dateRange = "";
                if (searchResult.Criteria.DateFrom.HasValue)
                    dateRange += $"開始: {searchResult.Criteria.DateFrom:yyyy/MM/dd}";
                if (searchResult.Criteria.DateTo.HasValue)
                {
                    if (!string.IsNullOrEmpty(dateRange)) dateRange += " ";
                    dateRange += $"終了: {searchResult.Criteria.DateTo:yyyy/MM/dd}";
                }
                txt.AppendLine($"更新日フィルタ: {dateRange}");
            }
            
            if (!string.IsNullOrWhiteSpace(searchResult.Criteria.ContentPattern))
                txt.AppendLine($"内容検索: {searchResult.Criteria.ContentPattern}");
            
            txt.AppendLine($"正規表現使用: {(searchResult.Criteria.UseRegex ? "有効" : "無効")}");
            txt.AppendLine($"大文字小文字区別: {(searchResult.Criteria.CaseSensitive ? "有効" : "無効")}");
            txt.AppendLine($"サブディレクトリ検索: {(searchResult.Criteria.IncludeSubdirectories ? "有効" : "無効")}");
            
            txt.AppendLine();
            txt.AppendLine("=== 検索結果統計 ===");
            txt.AppendLine($"スキャンファイル数: {searchResult.TotalFilesScanned:N0}件");
            txt.AppendLine($"マッチファイル数: {searchResult.MatchCount:N0}件");
            txt.AppendLine($"コンテンツマッチ数: {searchResult.TotalContentMatches:N0}件");
            txt.AppendLine($"実行時間: {searchResult.SearchDurationSeconds:F2}秒");
            
            if (searchResult.FileMatches.Any())
            {
                txt.AppendLine();
                txt.AppendLine("=== 検索結果一覧 ===");
                
                for (int i = 0; i < searchResult.FileMatches.Count; i++)
                {
                    var fileMatch = searchResult.FileMatches[i];
                    txt.AppendLine();
                    txt.AppendLine($"[{i + 1:D3}] {fileMatch.FileName}");
                    txt.AppendLine($"     パス: {fileMatch.FilePath}");
                    txt.AppendLine($"     サイズ: {fileMatch.FormattedSize}");
                    txt.AppendLine($"     更新日時: {fileMatch.LastModified:yyyy/MM/dd HH:mm:ss}");
                    
                    if (fileMatch.MatchCount > 0)
                    {
                        txt.AppendLine($"     マッチ数: {fileMatch.MatchCount}件");
                        var matchedTexts = fileMatch.GetAllMatchedTexts().Take(5).ToList();
                        if (matchedTexts.Any())
                        {
                            txt.AppendLine("     マッチ内容:");
                            foreach (var matchedText in matchedTexts)
                            {
                                txt.AppendLine($"       - {matchedText}");
                            }
                            if (fileMatch.MatchCount > 5)
                            {
                                txt.AppendLine($"       ... 他{fileMatch.MatchCount - 5}件");
                            }
                        }
                    }
                }
            }
            else
            {
                txt.AppendLine();
                txt.AppendLine("=== 検索結果 ===");
                txt.AppendLine("マッチするファイルが見つかりませんでした。");
            }
            
            txt.AppendLine();
            txt.AppendLine("=== レポート作成情報 ===");
            txt.AppendLine($"作成日時: {DateTime.Now:yyyy年MM月dd日 HH:mm:ss}");
            txt.AppendLine("作成者: Finder Scope - 高性能ファイル検索ツール");

            await File.WriteAllTextAsync(filePath, txt.ToString(), Encoding.UTF8);
        }
    }
}