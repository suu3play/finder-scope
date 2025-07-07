using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using FinderScope.Core.Models;

namespace FinderScope.Core.Services
{
    /// <summary>
    /// ファイル検索機能を提供するサービスクラス
    /// </summary>
    public class FileSearchService : IFileSearchService
    {
        public event EventHandler<SearchProgressEventArgs>? ProgressChanged;

        private const int ProgressReportInterval = 100; // 100ファイルごとに進行状況を報告

        /// <summary>
        /// 非同期でファイル検索を実行
        /// </summary>
        public async Task<SearchResult> SearchAsync(SearchCriteria criteria, CancellationToken cancellationToken = default)
        {
            return await Task.Run(() => Search(criteria, cancellationToken), cancellationToken);
        }

        /// <summary>
        /// 同期でファイル検索を実行
        /// </summary>
        public SearchResult Search(SearchCriteria criteria)
        {
            return Search(criteria, CancellationToken.None);
        }

        /// <summary>
        /// 内部検索実装
        /// </summary>
        private SearchResult Search(SearchCriteria criteria, CancellationToken cancellationToken)
        {
            var stopwatch = Stopwatch.StartNew();
            var performanceMonitor = new PerformanceMonitor();
            performanceMonitor.Start();
            
            var result = new SearchResult
            {
                Criteria = criteria,
                SearchStartTime = DateTime.Now
            };

            try
            {
                // 検索条件の検証
                criteria.Validate();

                // ファイル一覧を取得
                var files = GetFileList(criteria, cancellationToken);
                var totalFiles = files.Count();

                int scannedCount = 0;
                int matchedCount = 0;

                foreach (var filePath in files)
                {
                    cancellationToken.ThrowIfCancellationRequested();

                    try
                    {
                        var fileInfo = new FileInfo(filePath);
                        scannedCount++;

                        // ファイル条件チェック
                        if (MatchesFileCriteria(fileInfo, criteria))
                        {
                            var fileMatch = FileMatch.FromFileInfo(fileInfo);

                            // コンテンツ検索
                            if (!string.IsNullOrWhiteSpace(criteria.ContentPattern))
                            {
                                var contentMatches = SearchFileContent(filePath, criteria);
                                if (contentMatches.Any())
                                {
                                    fileMatch.Matches.AddRange(contentMatches);
                                    result.AddMatch(fileMatch);
                                    matchedCount++;
                                }
                            }
                            else
                            {
                                // ファイル名のみの検索
                                result.AddMatch(fileMatch);
                                matchedCount++;
                            }
                        }

                        // 進行状況の報告
                        if (scannedCount % ProgressReportInterval == 0 || scannedCount == totalFiles)
                        {
                            ReportProgress(scannedCount, matchedCount, filePath, totalFiles, stopwatch.Elapsed);
                        }
                    }
                    catch (Exception ex) when (!(ex is OperationCanceledException))
                    {
                        // 個別ファイルのエラーは無視して継続
                        continue;
                    }
                }

                result.TotalFilesScanned = scannedCount;
            }
            catch (OperationCanceledException)
            {
                result.WasCancelled = true;
            }
            catch (Exception ex)
            {
                result.ErrorMessage = ex.Message;
            }
            finally
            {
                stopwatch.Stop();
                result.SearchDurationSeconds = stopwatch.Elapsed.TotalSeconds;
                
                // パフォーマンス情報を収集
                var perfResult = performanceMonitor.Stop();
                
                // メモリ最適化（大量ファイル処理後）
                if (result.TotalFilesScanned > 10000)
                {
                    PerformanceMonitor.OptimizeMemory();
                }
            }

            return result;
        }

        /// <summary>
        /// 検索対象ファイル一覧を取得
        /// </summary>
        private IEnumerable<string> GetFileList(SearchCriteria criteria, CancellationToken cancellationToken)
        {
            var searchOption = criteria.IncludeSubdirectories 
                ? SearchOption.AllDirectories 
                : SearchOption.TopDirectoryOnly;

            var allFiles = Directory.EnumerateFiles(criteria.TargetFolder, "*", searchOption);

            // 拡張子フィルタを適用
            if (criteria.FileExtensions.Any())
            {
                allFiles = allFiles.Where(file => 
                    criteria.FileExtensions.Contains(Path.GetExtension(file), StringComparer.OrdinalIgnoreCase));
            }

            return allFiles;
        }

        /// <summary>
        /// ファイルが検索条件に一致するかチェック
        /// </summary>
        private bool MatchesFileCriteria(FileInfo fileInfo, SearchCriteria criteria)
        {
            // ファイル名パターンチェック
            if (!string.IsNullOrWhiteSpace(criteria.FilenamePattern))
            {
                if (!MatchesPattern(fileInfo.Name, criteria.FilenamePattern, criteria.UseRegex, criteria.CaseSensitive))
                {
                    return false;
                }
            }

            // 更新日チェック
            if (criteria.DateFrom.HasValue && fileInfo.LastWriteTime.Date < criteria.DateFrom.Value.Date)
            {
                return false;
            }

            if (criteria.DateTo.HasValue && fileInfo.LastWriteTime.Date > criteria.DateTo.Value.Date)
            {
                return false;
            }

            return true;
        }

        /// <summary>
        /// ファイル内容を検索
        /// </summary>
        private List<ContentMatch> SearchFileContent(string filePath, SearchCriteria criteria)
        {
            var matches = new List<ContentMatch>();

            if (string.IsNullOrWhiteSpace(criteria.ContentPattern))
                return matches;

            try
            {
                var lines = File.ReadAllLines(filePath);
                
                for (int lineIndex = 0; lineIndex < lines.Length; lineIndex++)
                {
                    var line = lines[lineIndex];
                    var lineMatches = FindMatchesInLine(line, criteria.ContentPattern, criteria.UseRegex, criteria.CaseSensitive);

                    foreach (var match in lineMatches)
                    {
                        var contentMatch = new ContentMatch
                        {
                            LineNumber = lineIndex + 1,
                            MatchedText = match.Value,
                            StartPosition = match.Index,
                            EndPosition = match.Index + match.Length,
                            ContextBefore = GetContextBefore(line, match.Index, 20),
                            ContextAfter = GetContextAfter(line, match.Index + match.Length, 20)
                        };

                        matches.Add(contentMatch);
                    }
                }
            }
            catch
            {
                // ファイル読み取りエラーは無視
            }

            return matches;
        }

        /// <summary>
        /// 行内でパターンにマッチする箇所を検索
        /// </summary>
        private IEnumerable<Match> FindMatchesInLine(string line, string pattern, bool useRegex, bool caseSensitive)
        {
            if (useRegex)
            {
                var options = caseSensitive ? RegexOptions.None : RegexOptions.IgnoreCase;
                var regex = new Regex(pattern, options);
                return regex.Matches(line).Cast<Match>();
            }
            else
            {
                var comparison = caseSensitive ? StringComparison.Ordinal : StringComparison.OrdinalIgnoreCase;
                var matches = new List<Match>();
                int startIndex = 0;

                while (true)
                {
                    int index = line.IndexOf(pattern, startIndex, comparison);
                    if (index == -1) break;

                    matches.Add(Match.Synchronized(new Regex(Regex.Escape(pattern)).Match(line, index)));
                    startIndex = index + 1;
                }

                return matches;
            }
        }

        /// <summary>
        /// パターンマッチング
        /// </summary>
        private bool MatchesPattern(string text, string pattern, bool useRegex, bool caseSensitive)
        {
            if (useRegex)
            {
                var options = caseSensitive ? RegexOptions.None : RegexOptions.IgnoreCase;
                return Regex.IsMatch(text, pattern, options);
            }
            else
            {
                var comparison = caseSensitive ? StringComparison.Ordinal : StringComparison.OrdinalIgnoreCase;
                return text.Contains(pattern, comparison);
            }
        }

        /// <summary>
        /// 前方コンテキストを取得
        /// </summary>
        private string GetContextBefore(string line, int position, int maxLength)
        {
            int start = Math.Max(0, position - maxLength);
            int length = position - start;
            return length > 0 ? line.Substring(start, length) : string.Empty;
        }

        /// <summary>
        /// 後方コンテキストを取得
        /// </summary>
        private string GetContextAfter(string line, int position, int maxLength)
        {
            if (position >= line.Length) return string.Empty;
            
            int length = Math.Min(maxLength, line.Length - position);
            return length > 0 ? line.Substring(position, length) : string.Empty;
        }

        /// <summary>
        /// 進行状況を報告
        /// </summary>
        private void ReportProgress(int scanned, int matched, string currentFile, int total, TimeSpan elapsed)
        {
            var progress = new SearchProgressEventArgs
            {
                FilesScanned = scanned,
                FilesMatched = matched,
                CurrentFile = currentFile,
                ProgressPercentage = total > 0 ? (double)scanned / total * 100 : 0,
                ElapsedTime = elapsed
            };

            ProgressChanged?.Invoke(this, progress);
        }
    }
}