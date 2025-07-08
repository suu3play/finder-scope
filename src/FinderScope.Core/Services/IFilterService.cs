using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using FinderScope.Core.Models;

namespace FinderScope.Core.Services
{
    /// <summary>
    /// 検索フィルタ管理サービスのインターフェース
    /// </summary>
    public interface IFilterService
    {
        /// <summary>
        /// 全ての保存済みフィルタを取得
        /// </summary>
        Task<IEnumerable<SearchFilter>> GetFiltersAsync();

        /// <summary>
        /// フィルタを保存
        /// </summary>
        Task SaveFilterAsync(SearchFilter filter);

        /// <summary>
        /// フィルタを更新
        /// </summary>
        Task UpdateFilterAsync(SearchFilter filter);

        /// <summary>
        /// フィルタを削除
        /// </summary>
        Task DeleteFilterAsync(string filterId);

        /// <summary>
        /// IDでフィルタを取得
        /// </summary>
        Task<SearchFilter?> GetFilterByIdAsync(string filterId);

        /// <summary>
        /// デフォルトフィルタを取得
        /// </summary>
        Task<SearchFilter?> GetDefaultFilterAsync();

        /// <summary>
        /// デフォルトフィルタを設定
        /// </summary>
        Task SetDefaultFilterAsync(string filterId);

        /// <summary>
        /// デフォルトフィルタを解除
        /// </summary>
        Task ClearDefaultFilterAsync();

        /// <summary>
        /// フィルタ名の重複をチェック
        /// </summary>
        Task<bool> IsFilterNameExistsAsync(string name, string? excludeId = null);

        /// <summary>
        /// フィルタの使用を記録
        /// </summary>
        Task RecordFilterUsageAsync(string filterId);

        /// <summary>
        /// フィルタをエクスポート
        /// </summary>
        Task ExportFiltersAsync(string filePath);

        /// <summary>
        /// フィルタをインポート
        /// </summary>
        Task<int> ImportFiltersAsync(string filePath);

        /// <summary>
        /// 全フィルタを削除（リセット）
        /// </summary>
        Task ClearAllFiltersAsync();
    }

    /// <summary>
    /// フィルタ操作の結果
    /// </summary>
    public class FilterOperationResult
    {
        public bool Success { get; set; }
        public string? ErrorMessage { get; set; }
        public SearchFilter? Filter { get; set; }

        public static FilterOperationResult SuccessResult(SearchFilter? filter = null)
        {
            return new FilterOperationResult { Success = true, Filter = filter };
        }

        public static FilterOperationResult ErrorResult(string errorMessage)
        {
            return new FilterOperationResult { Success = false, ErrorMessage = errorMessage };
        }
    }
}