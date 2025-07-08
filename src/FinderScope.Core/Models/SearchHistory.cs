using System;
using System.Collections.Generic;
using System.Linq;

namespace FinderScope.Core.Models
{
    /// <summary>
    /// 検索履歴エントリ
    /// </summary>
    public class SearchHistoryEntry
    {
        public string Value { get; set; } = string.Empty;
        public DateTime LastUsed { get; set; } = DateTime.Now;
        public int UsageCount { get; set; } = 1;

        public void RecordUsage()
        {
            LastUsed = DateTime.Now;
            UsageCount++;
        }
    }

    /// <summary>
    /// 検索履歴管理
    /// </summary>
    public class SearchHistory
    {
        private readonly List<SearchHistoryEntry> _entries = new();
        private readonly int _maxEntries;

        public SearchHistory(int maxEntries = 10)
        {
            _maxEntries = maxEntries;
        }

        /// <summary>
        /// 履歴に追加
        /// </summary>
        public void Add(string value)
        {
            if (string.IsNullOrWhiteSpace(value)) return;

            var existing = _entries.FirstOrDefault(e => e.Value.Equals(value, StringComparison.OrdinalIgnoreCase));
            if (existing != null)
            {
                existing.RecordUsage();
            }
            else
            {
                _entries.Add(new SearchHistoryEntry { Value = value });
                
                // 最大件数を超えた場合は古いものを削除
                if (_entries.Count > _maxEntries)
                {
                    var toRemove = _entries
                        .OrderBy(e => e.LastUsed)
                        .ThenBy(e => e.UsageCount)
                        .Take(_entries.Count - _maxEntries)
                        .ToList();
                    
                    foreach (var entry in toRemove)
                    {
                        _entries.Remove(entry);
                    }
                }
            }
        }

        /// <summary>
        /// 履歴を取得（使用頻度順）
        /// </summary>
        public IEnumerable<string> GetHistory()
        {
            return _entries
                .OrderByDescending(e => e.LastUsed)
                .ThenByDescending(e => e.UsageCount)
                .Select(e => e.Value)
                .ToList();
        }

        /// <summary>
        /// 履歴をクリア
        /// </summary>
        public void Clear()
        {
            _entries.Clear();
        }

        /// <summary>
        /// 特定の項目を削除
        /// </summary>
        public void Remove(string value)
        {
            var entry = _entries.FirstOrDefault(e => e.Value.Equals(value, StringComparison.OrdinalIgnoreCase));
            if (entry != null)
            {
                _entries.Remove(entry);
            }
        }

        /// <summary>
        /// エントリ一覧を取得（内部データ構造用）
        /// </summary>
        public IEnumerable<SearchHistoryEntry> GetEntries()
        {
            return _entries.ToList();
        }

        /// <summary>
        /// エントリ一覧から復元（永続化用）
        /// </summary>
        public void LoadEntries(IEnumerable<SearchHistoryEntry> entries)
        {
            _entries.Clear();
            _entries.AddRange(entries.Take(_maxEntries));
        }
    }
}