using System;
using System.Collections.Generic;

namespace FinderScope.Core.Models
{
    /// <summary>
    /// ファイルプレビューの設定
    /// </summary>
    public class PreviewSettings
    {
        public int MaxPreviewSize { get; set; } = 1024 * 1024; // 1MB
        public int MaxDisplayLines { get; set; } = 100;
        public int ContextLines { get; set; } = 3;
        public int TimeoutMs { get; set; } = 5000;
        public bool EnableEncodingDetection { get; set; } = true;
        public bool EnableBinaryDetection { get; set; } = true;
    }

    /// <summary>
    /// プレビュー内のマッチ情報
    /// </summary>
    public class PreviewMatch
    {
        public int LineNumber { get; set; }
        public int StartIndex { get; set; }
        public int Length { get; set; }
        public string MatchedText { get; set; } = string.Empty;
        public string Context { get; set; } = string.Empty;
    }

    /// <summary>
    /// ファイルプレビュー情報
    /// </summary>
    public class FilePreview
    {
        public string FilePath { get; set; } = string.Empty;
        public bool IsPreviewable { get; set; }
        public string Content { get; set; } = string.Empty;
        public List<PreviewMatch> Matches { get; set; } = new();
        public int StartLineNumber { get; set; } = 1;
        public int DisplayLines { get; set; } = 50;
        public int TotalLines { get; set; } = 0;
        public string Encoding { get; set; } = "UTF-8";
        public string? PreviewErrorMessage { get; set; }
        public long FileSize { get; set; }
        public bool IsBinaryFile { get; set; }
        public TimeSpan LoadTime { get; set; }

        /// <summary>
        /// プレビューが成功したかどうか
        /// </summary>
        public bool IsSuccess => IsPreviewable && string.IsNullOrEmpty(PreviewErrorMessage);

        /// <summary>
        /// ファイルサイズの人間が読みやすい形式
        /// </summary>
        public string FormattedFileSize
        {
            get
            {
                const long KB = 1024;
                const long MB = KB * 1024;
                const long GB = MB * 1024;

                return FileSize switch
                {
                    < KB => $"{FileSize} B",
                    < MB => $"{FileSize / (double)KB:F1} KB",
                    < GB => $"{FileSize / (double)MB:F1} MB",
                    _ => $"{FileSize / (double)GB:F1} GB"
                };
            }
        }

        /// <summary>
        /// プレビューの統計情報
        /// </summary>
        public string GetStatistics()
        {
            if (!IsPreviewable)
                return PreviewErrorMessage ?? "プレビューできません";

            var stats = $"表示行数: {DisplayLines}";
            if (TotalLines > DisplayLines)
                stats += $"/{TotalLines}";
            
            stats += $", サイズ: {FormattedFileSize}";
            stats += $", エンコーディング: {Encoding}";
            
            if (Matches.Count > 0)
                stats += $", マッチ数: {Matches.Count}";

            return stats;
        }
    }
}