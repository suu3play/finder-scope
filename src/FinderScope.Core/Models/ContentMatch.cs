namespace FinderScope.Core.Models
{
    /// <summary>
    /// ファイル内容のマッチ情報
    /// </summary>
    public class ContentMatch
    {
        public int LineNumber { get; set; }
        public string MatchedText { get; set; } = string.Empty;
        public string ContextBefore { get; set; } = string.Empty;
        public string ContextAfter { get; set; } = string.Empty;
        public int StartPosition { get; set; }
        public int EndPosition { get; set; }

        /// <summary>
        /// マッチ部分のプレビューテキスト
        /// </summary>
        public string ContextPreview => $"{ContextBefore}{MatchedText}{ContextAfter}";

        /// <summary>
        /// 行番号付きのプレビュー
        /// </summary>
        public string FormattedPreview => $"Line {LineNumber}: {ContextPreview.Trim()}";
    }
}