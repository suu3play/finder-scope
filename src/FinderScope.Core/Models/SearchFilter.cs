using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.Linq;

namespace FinderScope.Core.Models
{
    /// <summary>
    /// 保存された検索フィルタ
    /// </summary>
    public class SearchFilter
    {
        /// <summary>
        /// フィルタの一意識別子
        /// </summary>
        public string Id { get; set; } = Guid.NewGuid().ToString();

        /// <summary>
        /// フィルタ名
        /// </summary>
        [Required]
        [StringLength(100, MinimumLength = 1)]
        public string Name { get; set; } = string.Empty;

        /// <summary>
        /// 検索条件
        /// </summary>
        public SearchCriteria Criteria { get; set; } = new();

        /// <summary>
        /// 作成日時
        /// </summary>
        public DateTime CreatedAt { get; set; } = DateTime.Now;

        /// <summary>
        /// 最終使用日時
        /// </summary>
        public DateTime LastUsed { get; set; } = DateTime.Now;

        /// <summary>
        /// デフォルトフィルタかどうか
        /// </summary>
        public bool IsDefault { get; set; } = false;

        /// <summary>
        /// フィルタの説明
        /// </summary>
        [StringLength(500)]
        public string? Description { get; set; }

        /// <summary>
        /// 使用回数
        /// </summary>
        public int UsageCount { get; set; } = 0;
        public object? TargetFolder { get; set; }
        public object? FilenamePattern { get; set; }
        public object? FileExtensions { get; set; }
        public object? DateFrom { get; set; }
        public object? ContentPattern { get; set; }
        public object? DateTo { get; set; }
        public object? UseRegex { get; set; }
        public object? CaseSensitive { get; set; }
        public object? IncludeSubdirectories { get; set; }
        public object? EnableAutoSearch { get; set; }
        public object? WholeWordOnly { get; set; }

        /// <summary>
        /// フィルタが有効かどうか
        /// </summary>
        /// <returns>検索条件が有効な場合はtrue</returns>
        public bool IsValid()
        {
            return !string.IsNullOrWhiteSpace(Name) && Criteria.IsValid();
        }

        /// <summary>
        /// フィルタの使用を記録
        /// </summary>
        public void RecordUsage()
        {
            LastUsed = DateTime.Now;
            UsageCount++;
        }

        /// <summary>
        /// フィルタのクローンを作成
        /// </summary>
        public SearchFilter Clone()
        {
            return new SearchFilter
            {
                Id = Guid.NewGuid().ToString(), // 新しいIDを生成
                Name = $"{Name} - コピー",
                Criteria = new SearchCriteria
                {
                    TargetFolder = Criteria.TargetFolder,
                    FilenamePattern = Criteria.FilenamePattern,
                    FileExtensions = new List<string>(Criteria.FileExtensions),
                    DateFrom = Criteria.DateFrom,
                    DateTo = Criteria.DateTo,
                    ContentPattern = Criteria.ContentPattern,
                    UseRegex = Criteria.UseRegex,
                    CaseSensitive = Criteria.CaseSensitive,
                    IncludeSubdirectories = Criteria.IncludeSubdirectories
                },
                Description = Description,
                IsDefault = false // コピーはデフォルトにしない
            };
        }

        /// <summary>
        /// フィルタの概要を取得
        /// </summary>
        public string GetSummary()
        {
            var summary = $"フィルタ: {Name}";
            
            if (!string.IsNullOrWhiteSpace(Criteria.TargetFolder))
                summary += $" | フォルダ: {Criteria.TargetFolder}";
            
            if (!string.IsNullOrWhiteSpace(Criteria.FilenamePattern))
                summary += $" | ファイル名: {Criteria.FilenamePattern}";
            
            if (Criteria.FileExtensions.Any())
                summary += $" | 拡張子: {string.Join(", ", Criteria.FileExtensions)}";
            
            if (!string.IsNullOrWhiteSpace(Criteria.ContentPattern))
                summary += $" | 内容: {Criteria.ContentPattern}";
            
            summary += $" | 使用回数: {UsageCount}回";
            
            if (IsDefault)
                summary += " | デフォルト";
                
            return summary;
        }

        public override string ToString()
        {
            return Name;
        }

        public override bool Equals(object? obj)
        {
            return obj is SearchFilter filter && Id == filter.Id;
        }

        public override int GetHashCode()
        {
            return Id.GetHashCode();
        }
    }
}