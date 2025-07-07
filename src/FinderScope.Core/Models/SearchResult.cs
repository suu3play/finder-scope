using System;
using System.Collections.Generic;
using System.Linq;

namespace FinderScope.Core.Models
{
    /// <summary>
    /// 検索結果の統合データ
    /// </summary>
    public class SearchResult
    {
        public SearchCriteria Criteria { get; set; } = new();
        public List<FileMatch> FileMatches { get; set; } = new();
        public List<FileMatch> Matches { get; set; } = new();
        public double SearchDurationSeconds { get; set; }
        public int TotalFilesScanned { get; set; }
        public DateTime SearchStartTime { get; set; }
        public bool WasCancelled { get; set; }
        public string? ErrorMessage { get; set; }

        /// <summary>
        /// マッチしたファイル数
        /// </summary>
        public int MatchCount => FileMatches.Count;

        /// <summary>
        /// コンテンツマッチの総数
        /// </summary>
        public int TotalContentMatches => FileMatches.Sum(fm => fm.MatchCount);

        /// <summary>
        /// 総ファイルサイズ
        /// </summary>
        public long TotalFileSize => FileMatches.Sum(fm => fm.FileSize);

        /// <summary>
        /// 検索が成功したかどうか
        /// </summary>
        public bool IsSuccess => string.IsNullOrEmpty(ErrorMessage) && !WasCancelled;

        /// <summary>
        /// マッチ結果を追加
        /// </summary>
        public void AddMatch(FileMatch fileMatch)
        {
            FileMatches.Add(fileMatch);
            Matches.Add(fileMatch);
        }

        /// <summary>
        /// マッチ結果をクリア
        /// </summary>
        public void ClearMatches()
        {
            FileMatches.Clear();
            Matches.Clear();
        }

        /// <summary>
        /// 検索結果のサマリー文字列
        /// </summary>
        public string GetSummary()
        {
            if (!IsSuccess)
            {
                return WasCancelled ? "検索がキャンセルされました" : $"エラー: {ErrorMessage}";
            }

            var summary = $"検索結果: {MatchCount}件のファイルがマッチ ({TotalFilesScanned}件中)";
            
            if (TotalContentMatches > 0)
            {
                summary += $" | コンテンツマッチ: {TotalContentMatches}件";
            }
            
            summary += $" | 実行時間: {SearchDurationSeconds:F2}秒";
            
            return summary;
        }

        /// <summary>
        /// 詳細な統計情報を取得
        /// </summary>
        public SearchStatistics GetStatistics()
        {
            return new SearchStatistics
            {
                TotalFiles = TotalFilesScanned,
                MatchedFiles = MatchCount,
                ContentMatches = TotalContentMatches,
                TotalSize = TotalFileSize,
                SearchDuration = TimeSpan.FromSeconds(SearchDurationSeconds),
                FileExtensions = FileMatches.GroupBy(m => m.FileExtension)
                    .ToDictionary(g => g.Key, g => g.Count())
            };
        }
    }

    /// <summary>
    /// 検索統計情報
    /// </summary>
    public class SearchStatistics
    {
        public int TotalFiles { get; set; }
        public int MatchedFiles { get; set; }
        public int ContentMatches { get; set; }
        public long TotalSize { get; set; }
        public TimeSpan SearchDuration { get; set; }
        public Dictionary<string, int> FileExtensions { get; set; } = new();

        public double MatchRate => TotalFiles > 0 ? (double)MatchedFiles / TotalFiles * 100 : 0;
        public string TotalSizeFormatted => FormatFileSize(TotalSize);

        private static string FormatFileSize(long bytes)
        {
            const long KB = 1024;
            const long MB = KB * 1024;
            const long GB = MB * 1024;

            return bytes switch
            {
                < KB => $"{bytes} B",
                < MB => $"{bytes / (double)KB:F1} KB",
                < GB => $"{bytes / (double)MB:F1} MB",
                _ => $"{bytes / (double)GB:F1} GB"
            };
        }
    }
}