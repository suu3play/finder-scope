using System;
using System.Threading;
using System.Threading.Tasks;
using FinderScope.Core.Models;

namespace FinderScope.Core.Services
{
    /// <summary>
    /// ファイル検索サービスのインターフェース
    /// </summary>
    public interface IFileSearchService
    {
        /// <summary>
        /// 検索進行状況の通知イベント
        /// </summary>
        event EventHandler<SearchProgressEventArgs>? ProgressChanged;

        /// <summary>
        /// 非同期でファイル検索を実行
        /// </summary>
        /// <param name="criteria">検索条件</param>
        /// <param name="cancellationToken">キャンセルトークン</param>
        /// <returns>検索結果</returns>
        Task<SearchResult> SearchAsync(SearchCriteria criteria, CancellationToken cancellationToken = default);

        /// <summary>
        /// 同期でファイル検索を実行
        /// </summary>
        /// <param name="criteria">検索条件</param>
        /// <returns>検索結果</returns>
        SearchResult Search(SearchCriteria criteria);
    }

    /// <summary>
    /// 検索進行状況のイベント引数
    /// </summary>
    public class SearchProgressEventArgs : EventArgs
    {
        public int FilesScanned { get; set; }
        public int FilesMatched { get; set; }
        public string CurrentFile { get; set; } = string.Empty;
        public double ProgressPercentage { get; set; }
        public TimeSpan ElapsedTime { get; set; }
    }
}