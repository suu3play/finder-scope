namespace FinderScope.Core.Models
{
    /// <summary>
    /// ファイルカテゴリの列挙型
    /// </summary>
    public enum FileCategory
    {
        /// <summary>
        /// ドキュメント系ファイル
        /// </summary>
        Document,

        /// <summary>
        /// プログラムコード系ファイル
        /// </summary>
        Code,

        /// <summary>
        /// ログ・設定ファイル系
        /// </summary>
        Config,

        /// <summary>
        /// Web系ファイル
        /// </summary>
        Web,

        /// <summary>
        /// データ系ファイル
        /// </summary>
        Data,

        /// <summary>
        /// すべてのファイル
        /// </summary>
        All
    }

    /// <summary>
    /// ファイルカテゴリとその表示名・拡張子の情報
    /// </summary>
    public class FileCategoryInfo
    {
        public FileCategory Category { get; set; }
        public string DisplayName { get; set; } = string.Empty;
        public List<string> Extensions { get; set; } = new();
        public string Description { get; set; } = string.Empty;

        public FileCategoryInfo()
        {
        }

        public FileCategoryInfo(FileCategory category, string displayName, List<string> extensions, string description = "")
        {
            Category = category;
            DisplayName = displayName;
            Extensions = extensions;
            Description = description;
        }
    }
}