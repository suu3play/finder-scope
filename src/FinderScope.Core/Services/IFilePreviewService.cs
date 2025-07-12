using System.Threading;
using System.Threading.Tasks;
using FinderScope.Core.Models;

namespace FinderScope.Core.Services
{
    /// <summary>
    /// ファイルプレビュー機能を提供するサービスのインターフェース
    /// </summary>
    public interface IFilePreviewService
    {
        /// <summary>
        /// ファイルのプレビューを生成する
        /// </summary>
        /// <param name="fileMatch">プレビュー対象のファイル</param>
        /// <param name="settings">プレビュー設定</param>
        /// <param name="cancellationToken">キャンセレーショントークン</param>
        /// <returns>ファイルプレビュー</returns>
        Task<FilePreview> GeneratePreviewAsync(FileMatch fileMatch, PreviewSettings settings, CancellationToken cancellationToken = default);

        /// <summary>
        /// ファイルがプレビュー可能かどうかを判定する
        /// </summary>
        /// <param name="filePath">ファイルパス</param>
        /// <returns>プレビュー可能な場合はtrue</returns>
        bool IsPreviewable(string filePath);

        /// <summary>
        /// ファイルがバイナリファイルかどうかを判定する
        /// </summary>
        /// <param name="filePath">ファイルパス</param>
        /// <returns>バイナリファイルの場合はtrue</returns>
        Task<bool> IsBinaryFileAsync(string filePath);
    }
}