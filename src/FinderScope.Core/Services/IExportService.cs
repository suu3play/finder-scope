using System.Threading.Tasks;
using FinderScope.Core.Models;

namespace FinderScope.Core.Services
{
    /// <summary>
    /// エクスポート機能のインターフェース
    /// </summary>
    public interface IExportService
    {
        /// <summary>
        /// CSV形式でエクスポート
        /// </summary>
        Task ExportToCsvAsync(SearchResult searchResult, string filePath);

        /// <summary>
        /// JSON形式でエクスポート
        /// </summary>
        Task ExportToJsonAsync(SearchResult searchResult, string filePath);

        /// <summary>
        /// HTML形式でエクスポート
        /// </summary>
        Task ExportToHtmlAsync(SearchResult searchResult, string filePath);
    }

    /// <summary>
    /// エクスポート形式の列挙型
    /// </summary>
    public enum ExportFormat
    {
        Csv,
        Json,
        Html
    }
}