using System.Collections.Generic;
using System.Threading.Tasks;

namespace FinderScope.Core.Services
{
    /// <summary>
    /// 検索履歴管理サービスのインターフェース
    /// </summary>
    public interface ISearchHistoryService
    {
        /// <summary>
        /// 対象フォルダ履歴を追加
        /// </summary>
        Task AddTargetFolderAsync(string folder);

        /// <summary>
        /// ファイル名パターン履歴を追加
        /// </summary>
        Task AddFilenamePatternAsync(string pattern);

        /// <summary>
        /// ファイル内容パターン履歴を追加
        /// </summary>
        Task AddContentPatternAsync(string pattern);

        /// <summary>
        /// 対象フォルダ履歴を取得
        /// </summary>
        Task<IEnumerable<string>> GetTargetFolderHistoryAsync();

        /// <summary>
        /// ファイル名パターン履歴を取得
        /// </summary>
        Task<IEnumerable<string>> GetFilenamePatternHistoryAsync();

        /// <summary>
        /// ファイル内容パターン履歴を取得
        /// </summary>
        Task<IEnumerable<string>> GetContentPatternHistoryAsync();

        /// <summary>
        /// 全履歴をクリア
        /// </summary>
        Task ClearAllHistoryAsync();

        /// <summary>
        /// 特定の履歴をクリア
        /// </summary>
        Task ClearTargetFolderHistoryAsync();
        Task ClearFilenamePatternHistoryAsync();
        Task ClearContentPatternHistoryAsync();

        /// <summary>
        /// 履歴から項目を削除
        /// </summary>
        Task RemoveFromTargetFolderHistoryAsync(string folder);
        Task RemoveFromFilenamePatternHistoryAsync(string pattern);
        Task RemoveFromContentPatternHistoryAsync(string pattern);
    }
}