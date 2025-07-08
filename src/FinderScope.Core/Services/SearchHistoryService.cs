using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;
using FinderScope.Core.Models;

namespace FinderScope.Core.Services
{
    /// <summary>
    /// 検索履歴管理サービスの実装
    /// </summary>
    public class SearchHistoryService : ISearchHistoryService
    {
        private readonly string _historyDirectory;
        private readonly string _historyFilePath;
        private readonly JsonSerializerOptions _jsonOptions;
        
        private readonly SearchHistory _targetFolderHistory;
        private readonly SearchHistory _filenamePatternHistory;
        private readonly SearchHistory _contentPatternHistory;

        public SearchHistoryService()
        {
            // 履歴データの保存場所
            var appDataPath = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);
            _historyDirectory = Path.Combine(appDataPath, "FinderScope", "History");
            _historyFilePath = Path.Combine(_historyDirectory, "search_history.json");

            _jsonOptions = new JsonSerializerOptions
            {
                WriteIndented = true,
                PropertyNamingPolicy = JsonNamingPolicy.CamelCase
            };

            _targetFolderHistory = new SearchHistory(10);
            _filenamePatternHistory = new SearchHistory(10);
            _contentPatternHistory = new SearchHistory(10);

            // 初期化時に履歴を読み込み
            _ = Task.Run(LoadHistoryAsync);
        }

        public async Task AddTargetFolderAsync(string folder)
        {
            _targetFolderHistory.Add(folder);
            await SaveHistoryAsync();
        }

        public async Task AddFilenamePatternAsync(string pattern)
        {
            _filenamePatternHistory.Add(pattern);
            await SaveHistoryAsync();
        }

        public async Task AddContentPatternAsync(string pattern)
        {
            _contentPatternHistory.Add(pattern);
            await SaveHistoryAsync();
        }

        public async Task<IEnumerable<string>> GetTargetFolderHistoryAsync()
        {
            await EnsureHistoryLoadedAsync();
            return _targetFolderHistory.GetHistory();
        }

        public async Task<IEnumerable<string>> GetFilenamePatternHistoryAsync()
        {
            await EnsureHistoryLoadedAsync();
            return _filenamePatternHistory.GetHistory();
        }

        public async Task<IEnumerable<string>> GetContentPatternHistoryAsync()
        {
            await EnsureHistoryLoadedAsync();
            return _contentPatternHistory.GetHistory();
        }

        public async Task ClearAllHistoryAsync()
        {
            _targetFolderHistory.Clear();
            _filenamePatternHistory.Clear();
            _contentPatternHistory.Clear();
            await SaveHistoryAsync();
        }

        public async Task ClearTargetFolderHistoryAsync()
        {
            _targetFolderHistory.Clear();
            await SaveHistoryAsync();
        }

        public async Task ClearFilenamePatternHistoryAsync()
        {
            _filenamePatternHistory.Clear();
            await SaveHistoryAsync();
        }

        public async Task ClearContentPatternHistoryAsync()
        {
            _contentPatternHistory.Clear();
            await SaveHistoryAsync();
        }

        public async Task RemoveFromTargetFolderHistoryAsync(string folder)
        {
            _targetFolderHistory.Remove(folder);
            await SaveHistoryAsync();
        }

        public async Task RemoveFromFilenamePatternHistoryAsync(string pattern)
        {
            _filenamePatternHistory.Remove(pattern);
            await SaveHistoryAsync();
        }

        public async Task RemoveFromContentPatternHistoryAsync(string pattern)
        {
            _contentPatternHistory.Remove(pattern);
            await SaveHistoryAsync();
        }

        private async Task EnsureHistoryLoadedAsync()
        {
            if (!File.Exists(_historyFilePath)) return;
            
            // 履歴が空の場合のみロード
            if (!_targetFolderHistory.GetHistory().Any() && 
                !_filenamePatternHistory.GetHistory().Any() && 
                !_contentPatternHistory.GetHistory().Any())
            {
                await LoadHistoryAsync();
            }
        }

        private async Task LoadHistoryAsync()
        {
            try
            {
                if (File.Exists(_historyFilePath))
                {
                    var json = await File.ReadAllTextAsync(_historyFilePath);
                    var data = JsonSerializer.Deserialize<SearchHistoryData>(json, _jsonOptions);
                    
                    if (data != null)
                    {
                        _targetFolderHistory.LoadEntries(data.TargetFolderHistory ?? new List<SearchHistoryEntry>());
                        _filenamePatternHistory.LoadEntries(data.FilenamePatternHistory ?? new List<SearchHistoryEntry>());
                        _contentPatternHistory.LoadEntries(data.ContentPatternHistory ?? new List<SearchHistoryEntry>());
                    }
                }
            }
            catch
            {
                // 履歴ファイルが破損している場合は空で開始
            }
        }

        private async Task SaveHistoryAsync()
        {
            try
            {
                if (!Directory.Exists(_historyDirectory))
                {
                    Directory.CreateDirectory(_historyDirectory);
                }

                var data = new SearchHistoryData
                {
                    TargetFolderHistory = _targetFolderHistory.GetEntries().ToList(),
                    FilenamePatternHistory = _filenamePatternHistory.GetEntries().ToList(),
                    ContentPatternHistory = _contentPatternHistory.GetEntries().ToList()
                };

                var json = JsonSerializer.Serialize(data, _jsonOptions);
                await File.WriteAllTextAsync(_historyFilePath, json);
            }
            catch
            {
                // 保存エラーは無視（次回保存時に再試行）
            }
        }

        /// <summary>
        /// 履歴データ永続化用クラス
        /// </summary>
        private class SearchHistoryData
        {
            public List<SearchHistoryEntry> TargetFolderHistory { get; set; } = new();
            public List<SearchHistoryEntry> FilenamePatternHistory { get; set; } = new();
            public List<SearchHistoryEntry> ContentPatternHistory { get; set; } = new();
        }
    }
}