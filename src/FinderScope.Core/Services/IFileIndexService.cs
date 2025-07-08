using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using FinderScope.Core.Models;

namespace FinderScope.Core.Services
{
    /// <summary>
    /// ファイルインデックスサービスのインターフェース
    /// </summary>
    public interface IFileIndexService
    {
        /// <summary>
        /// インデックス進行状況が変更された時のイベント
        /// </summary>
        event EventHandler<IndexProgressEventArgs>? IndexProgressChanged;

        /// <summary>
        /// 全ドライブのインデックスを開始
        /// </summary>
        Task StartFullIndexAsync(CancellationToken cancellationToken = default);

        /// <summary>
        /// 特定のドライブのインデックスを開始
        /// </summary>
        Task StartDriveIndexAsync(string driveLetter, CancellationToken cancellationToken = default);

        /// <summary>
        /// インデックス更新（変更された部分のみ）
        /// </summary>
        Task UpdateIndexAsync(CancellationToken cancellationToken = default);

        /// <summary>
        /// ファイル名でクイック検索
        /// </summary>
        Task<IEnumerable<FileIndexEntry>> QuickSearchAsync(string fileName, int maxResults = 1000);

        /// <summary>
        /// 拡張子でフィルタリング
        /// </summary>
        Task<IEnumerable<FileIndexEntry>> SearchByExtensionAsync(IEnumerable<string> extensions, int maxResults = 1000);

        /// <summary>
        /// パターンマッチング検索
        /// </summary>
        Task<IEnumerable<FileIndexEntry>> SearchByPatternAsync(string pattern, bool useRegex = false, bool caseSensitive = false, int maxResults = 1000);

        /// <summary>
        /// インデックス統計情報を取得
        /// </summary>
        Task<IndexStatistics> GetStatisticsAsync();

        /// <summary>
        /// インデックスをクリア
        /// </summary>
        Task ClearIndexAsync();

        /// <summary>
        /// インデックスが利用可能か確認
        /// </summary>
        Task<bool> IsIndexAvailableAsync();

        /// <summary>
        /// バックグラウンドでインデックス更新を開始
        /// </summary>
        void StartBackgroundIndexing();

        /// <summary>
        /// バックグラウンドインデックス更新を停止
        /// </summary>
        void StopBackgroundIndexing();

        /// <summary>
        /// 現在インデックス中かどうか
        /// </summary>
        bool IsIndexing { get; }
    }

    /// <summary>
    /// インデックス進行状況イベント引数
    /// </summary>
    public class IndexProgressEventArgs : EventArgs
    {
        public string CurrentDrive { get; set; } = string.Empty;
        public string CurrentFile { get; set; } = string.Empty;
        public int FilesProcessed { get; set; }
        public int TotalFiles { get; set; }
        public double ProgressPercentage { get; set; }
        public TimeSpan ElapsedTime { get; set; }
        public bool IsCompleted { get; set; }
        public string? ErrorMessage { get; set; }
    }
}