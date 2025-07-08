using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;

namespace FinderScope.Core.Models
{
    /// <summary>
    /// 検索条件を表すクラス
    /// </summary>
    public class SearchCriteria
    {
        public string TargetFolder { get; set; } = string.Empty;
        public string? FilenamePattern { get; set; }
        public List<string> FileExtensions { get; set; } = new();
        public DateTime? DateFrom { get; set; }
        public DateTime? DateTo { get; set; }
        public string? ContentPattern { get; set; }
        public bool UseRegex { get; set; } = false;
        public bool CaseSensitive { get; set; } = false;
        public bool IncludeSubdirectories { get; set; } = true;
        public bool CaseInsensitive { get; set; } = true;
        public bool WholeWordOnly { get; set; } = false;

        /// <summary>
        /// 検索条件の検証
        /// </summary>
        public void Validate()
        {
            if (string.IsNullOrWhiteSpace(TargetFolder))
                throw new ArgumentException("対象フォルダが指定されていません。");

            if (!Directory.Exists(TargetFolder))
                throw new DirectoryNotFoundException($"対象フォルダが存在しません: {TargetFolder}");

            // 拡張子の正規化（先頭にドットを追加）
            FileExtensions = FileExtensions
                .Where(ext => !string.IsNullOrWhiteSpace(ext))
                .Select(ext => ext.StartsWith('.') ? ext : $".{ext}")
                .Distinct()
                .ToList();

            // 日付範囲の検証
            if (DateFrom.HasValue && DateTo.HasValue && DateFrom > DateTo)
                throw new ArgumentException("開始日が終了日より後になっています。");
        }

        /// <summary>
        /// 検索条件が有効かどうかをチェック
        /// </summary>
        public bool IsValid()
        {
            try
            {
                if (string.IsNullOrWhiteSpace(TargetFolder))
                    return false;

                if (!Directory.Exists(TargetFolder))
                    return false;

                // 日付範囲の検証
                if (DateFrom.HasValue && DateTo.HasValue && DateFrom > DateTo)
                    return false;

                return true;
            }
            catch
            {
                return false;
            }
        }

        /// <summary>
        /// 検索条件の概要説明を取得
        /// </summary>
        public string GetSummary()
        {
            var parts = new List<string>();
            
            if (!string.IsNullOrWhiteSpace(FilenamePattern))
                parts.Add($"ファイル名: {FilenamePattern}");
            
            if (FileExtensions.Any())
                parts.Add($"拡張子: {string.Join(", ", FileExtensions)}");
            
            if (!string.IsNullOrWhiteSpace(ContentPattern))
                parts.Add($"内容: {ContentPattern}");
            
            if (DateFrom.HasValue || DateTo.HasValue)
            {
                var dateRange = DateFrom?.ToString("yyyy/MM/dd") ?? "～";
                dateRange += " ～ ";
                dateRange += DateTo?.ToString("yyyy/MM/dd") ?? "～";
                parts.Add($"更新日: {dateRange}");
            }

            return parts.Any() ? string.Join(" | ", parts) : "すべてのファイル";
        }
    }
}