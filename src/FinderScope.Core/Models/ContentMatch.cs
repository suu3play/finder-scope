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
        public int ColumnNumber { get; set; }
        public int Length => MatchedText?.Length ?? 0;

        /// <summary>
        /// デフォルトコンストラクタ
        /// </summary>
        public ContentMatch()
        {
        }

        /// <summary>
        /// パラメータ付きコンストラクタ
        /// </summary>
        public ContentMatch(int lineNumber, int columnNumber, string matchedText, int startPosition, int endPosition)
        {
            LineNumber = lineNumber;
            ColumnNumber = columnNumber;
            MatchedText = matchedText ?? string.Empty;
            StartPosition = startPosition;
            EndPosition = endPosition;
        }

        /// <summary>
        /// マッチ部分のプレビューテキスト
        /// </summary>
        public string ContextPreview => $"{ContextBefore}{MatchedText}{ContextAfter}";

        /// <summary>
        /// 行番号付きのプレビュー
        /// </summary>
        public string FormattedPreview => $"Line {LineNumber}: {ContextPreview.Trim()}";

        /// <summary>
        /// マッチの詳細情報
        /// </summary>
        public string GetDetails()
        {
            return $"Line {LineNumber}, Column {ColumnNumber}: '{MatchedText}' (Length: {Length})";
        }
    }
}