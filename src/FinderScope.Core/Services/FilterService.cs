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
    /// 検索フィルタ管理サービスの実装
    /// </summary>
    public class FilterService : IFilterService
    {
        private readonly string _filtersDirectory;
        private readonly string _filtersFilePath;
        private readonly JsonSerializerOptions _jsonOptions;
        private List<SearchFilter> _filters;

        public FilterService()
        {
            // アプリケーションデータフォルダにフィルタを保存
            var appDataPath = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);
            _filtersDirectory = Path.Combine(appDataPath, "FinderScope", "Filters");
            _filtersFilePath = Path.Combine(_filtersDirectory, "filters.json");
            
            _jsonOptions = new JsonSerializerOptions
            {
                WriteIndented = true,
                PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
                Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping
            };

            _filters = new List<SearchFilter>();
            
            // 初期化時にフィルタを読み込み
            _ = Task.Run(LoadFiltersAsync);
        }

        /// <summary>
        /// 全ての保存済みフィルタを取得
        /// </summary>
        public async Task<IEnumerable<SearchFilter>> GetFiltersAsync()
        {
            await EnsureFiltersLoadedAsync();
            return _filters.OrderBy(f => f.Name).ToList();
        }

        /// <summary>
        /// フィルタを保存
        /// </summary>
        public async Task SaveFilterAsync(SearchFilter filter)
        {
            if (!filter.IsValid())
                throw new ArgumentException("フィルタが無効です。", nameof(filter));

            await EnsureFiltersLoadedAsync();

            // 名前の重複チェック
            if (await IsFilterNameExistsAsync(filter.Name))
                throw new InvalidOperationException($"フィルタ名 '{filter.Name}' は既に存在します。");

            _filters.Add(filter);
            await SaveFiltersAsync();
        }

        /// <summary>
        /// フィルタを更新
        /// </summary>
        public async Task UpdateFilterAsync(SearchFilter filter)
        {
            if (!filter.IsValid())
                throw new ArgumentException("フィルタが無効です。", nameof(filter));

            await EnsureFiltersLoadedAsync();

            var existingFilter = _filters.FirstOrDefault(f => f.Id == filter.Id);
            if (existingFilter == null)
                throw new InvalidOperationException($"ID '{filter.Id}' のフィルタが見つかりません。");

            // 名前の重複チェック（自分以外）
            if (await IsFilterNameExistsAsync(filter.Name, filter.Id))
                throw new InvalidOperationException($"フィルタ名 '{filter.Name}' は既に存在します。");

            var index = _filters.IndexOf(existingFilter);
            _filters[index] = filter;
            await SaveFiltersAsync();
        }

        /// <summary>
        /// フィルタを削除
        /// </summary>
        public async Task DeleteFilterAsync(string filterId)
        {
            await EnsureFiltersLoadedAsync();

            var filter = _filters.FirstOrDefault(f => f.Id == filterId);
            if (filter == null)
                throw new InvalidOperationException($"ID '{filterId}' のフィルタが見つかりません。");

            _filters.Remove(filter);
            await SaveFiltersAsync();
        }

        /// <summary>
        /// IDでフィルタを取得
        /// </summary>
        public async Task<SearchFilter?> GetFilterByIdAsync(string filterId)
        {
            await EnsureFiltersLoadedAsync();
            return _filters.FirstOrDefault(f => f.Id == filterId);
        }

        /// <summary>
        /// デフォルトフィルタを取得
        /// </summary>
        public async Task<SearchFilter?> GetDefaultFilterAsync()
        {
            await EnsureFiltersLoadedAsync();
            return _filters.FirstOrDefault(f => f.IsDefault);
        }

        /// <summary>
        /// デフォルトフィルタを設定
        /// </summary>
        public async Task SetDefaultFilterAsync(string filterId)
        {
            await EnsureFiltersLoadedAsync();

            var filter = _filters.FirstOrDefault(f => f.Id == filterId);
            if (filter == null)
                throw new InvalidOperationException($"ID '{filterId}' のフィルタが見つかりません。");

            // 既存のデフォルトを解除
            foreach (var f in _filters.Where(f => f.IsDefault))
            {
                f.IsDefault = false;
            }

            // 新しいデフォルトを設定
            filter.IsDefault = true;
            await SaveFiltersAsync();
        }

        /// <summary>
        /// デフォルトフィルタを解除
        /// </summary>
        public async Task ClearDefaultFilterAsync()
        {
            await EnsureFiltersLoadedAsync();

            var hasChanges = false;
            foreach (var filter in _filters.Where(f => f.IsDefault))
            {
                filter.IsDefault = false;
                hasChanges = true;
            }

            if (hasChanges)
            {
                await SaveFiltersAsync();
            }
        }

        /// <summary>
        /// フィルタ名の重複をチェック
        /// </summary>
        public async Task<bool> IsFilterNameExistsAsync(string name, string? excludeId = null)
        {
            await EnsureFiltersLoadedAsync();
            return _filters.Any(f => f.Name.Equals(name, StringComparison.OrdinalIgnoreCase) && 
                                   (excludeId == null || f.Id != excludeId));
        }

        /// <summary>
        /// フィルタの使用を記録
        /// </summary>
        public async Task RecordFilterUsageAsync(string filterId)
        {
            await EnsureFiltersLoadedAsync();

            var filter = _filters.FirstOrDefault(f => f.Id == filterId);
            if (filter != null)
            {
                filter.RecordUsage();
                await SaveFiltersAsync();
            }
        }

        /// <summary>
        /// フィルタをエクスポート
        /// </summary>
        public async Task ExportFiltersAsync(string filePath)
        {
            await EnsureFiltersLoadedAsync();

            var exportData = new
            {
                ExportDate = DateTime.Now,
                Version = "1.0",
                Filters = _filters
            };

            var json = JsonSerializer.Serialize(exportData, _jsonOptions);
            await File.WriteAllTextAsync(filePath, json);
        }

        /// <summary>
        /// フィルタをインポート
        /// </summary>
        public async Task<int> ImportFiltersAsync(string filePath)
        {
            if (!File.Exists(filePath))
                throw new FileNotFoundException($"ファイルが見つかりません: {filePath}");

            var json = await File.ReadAllTextAsync(filePath);
            var importData = JsonSerializer.Deserialize<JsonElement>(json);

            if (!importData.TryGetProperty("Filters", out var filtersElement))
                throw new InvalidOperationException("有効なフィルタファイルではありません。");

            var importedFilters = JsonSerializer.Deserialize<List<SearchFilter>>(filtersElement.GetRawText(), _jsonOptions);
            if (importedFilters == null)
                throw new InvalidOperationException("フィルタデータを読み込めませんでした。");

            await EnsureFiltersLoadedAsync();

            var importedCount = 0;
            foreach (var filter in importedFilters)
            {
                // 名前の重複を避けるため、必要に応じて名前を変更
                var originalName = filter.Name;
                var counter = 1;
                while (await IsFilterNameExistsAsync(filter.Name))
                {
                    filter.Name = $"{originalName} ({counter})";
                    counter++;
                }

                // 新しいIDを生成
                filter.Id = Guid.NewGuid().ToString();
                filter.IsDefault = false; // インポートフィルタはデフォルトにしない

                _filters.Add(filter);
                importedCount++;
            }

            if (importedCount > 0)
            {
                await SaveFiltersAsync();
            }

            return importedCount;
        }

        /// <summary>
        /// 全フィルタを削除（リセット）
        /// </summary>
        public async Task ClearAllFiltersAsync()
        {
            _filters.Clear();
            await SaveFiltersAsync();
        }

        /// <summary>
        /// フィルタがロードされていることを確認
        /// </summary>
        private async Task EnsureFiltersLoadedAsync()
        {
            if (!_filters.Any() && File.Exists(_filtersFilePath))
            {
                await LoadFiltersAsync();
            }
        }

        /// <summary>
        /// フィルタをファイルから読み込み
        /// </summary>
        private async Task LoadFiltersAsync()
        {
            try
            {
                if (File.Exists(_filtersFilePath))
                {
                    var json = await File.ReadAllTextAsync(_filtersFilePath);
                    var filters = JsonSerializer.Deserialize<List<SearchFilter>>(json, _jsonOptions);
                    _filters = filters ?? new List<SearchFilter>();
                }
                else
                {
                    _filters = new List<SearchFilter>();
                }
            }
            catch (Exception)
            {
                // ファイルが破損している場合は空のリストで開始
                _filters = new List<SearchFilter>();
            }
        }

        /// <summary>
        /// フィルタをファイルに保存
        /// </summary>
        private async Task SaveFiltersAsync()
        {
            try
            {
                // ディレクトリが存在しない場合は作成
                if (!Directory.Exists(_filtersDirectory))
                {
                    Directory.CreateDirectory(_filtersDirectory);
                }

                var json = JsonSerializer.Serialize(_filters, _jsonOptions);
                await File.WriteAllTextAsync(_filtersFilePath, json);
            }
            catch (Exception ex)
            {
                throw new InvalidOperationException("フィルタの保存に失敗しました。", ex);
            }
        }
    }
}