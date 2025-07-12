using System.Text.RegularExpressions;

namespace FinderScope.Core.Utilities
{
    /// <summary>
    /// ワイルドカードパターンマッチング用ユーティリティ
    /// </summary>
    public static class WildcardMatcher
    {
        /// <summary>
        /// ワイルドカードパターン（*、?）を正規表現に変換
        /// </summary>
        /// <param name="wildcardPattern">ワイルドカードパターン</param>
        /// <param name="caseSensitive">大文字小文字を区別するか</param>
        /// <returns>正規表現パターン</returns>
        public static string ConvertToRegex(string wildcardPattern, bool caseSensitive = false)
        {
            if (string.IsNullOrEmpty(wildcardPattern))
                return string.Empty;

            // 正規表現の特殊文字をエスケープ（* と ? 以外）
            var escaped = Regex.Escape(wildcardPattern);
            
            // エスケープされた * と ? を正規表現に変換
            escaped = escaped.Replace("\\*", ".*")  // * → .* (任意の文字列)
                           .Replace("\\?", ".");   // ? → .  (任意の1文字)
            
            // 完全一致にするため ^ と $ で囲む
            var regexPattern = $"^{escaped}$";
            
            return regexPattern;
        }

        /// <summary>
        /// ワイルドカードパターンでファイル名をチェック
        /// </summary>
        /// <param name="fileName">チェックするファイル名</param>
        /// <param name="wildcardPattern">ワイルドカードパターン</param>
        /// <param name="caseSensitive">大文字小文字を区別するか</param>
        /// <returns>マッチするかどうか</returns>
        public static bool IsMatch(string fileName, string wildcardPattern, bool caseSensitive = false)
        {
            if (string.IsNullOrEmpty(fileName) || string.IsNullOrEmpty(wildcardPattern))
                return false;

            try
            {
                var regexPattern = ConvertToRegex(wildcardPattern, caseSensitive);
                var options = caseSensitive ? RegexOptions.None : RegexOptions.IgnoreCase;
                
                return Regex.IsMatch(fileName, regexPattern, options);
            }
            catch (ArgumentException)
            {
                // 無効な正規表現の場合は部分一致で処理
                return fileName.Contains(wildcardPattern, caseSensitive ? StringComparison.Ordinal : StringComparison.OrdinalIgnoreCase);
            }
        }

        /// <summary>
        /// 複数のワイルドカードパターン（;または,区切り）でファイル名をチェック
        /// </summary>
        /// <param name="fileName">チェックするファイル名</param>
        /// <param name="wildcardPatterns">ワイルドカードパターン（;または,区切り）</param>
        /// <param name="caseSensitive">大文字小文字を区別するか</param>
        /// <returns>いずれかのパターンにマッチするかどうか</returns>
        public static bool IsMatchAny(string fileName, string wildcardPatterns, bool caseSensitive = false)
        {
            if (string.IsNullOrEmpty(fileName) || string.IsNullOrEmpty(wildcardPatterns))
                return false;

            // セミコロンまたはカンマで分割
            var patterns = wildcardPatterns.Split(new[] { ';', ',' }, StringSplitOptions.RemoveEmptyEntries)
                                         .Select(p => p.Trim())
                                         .Where(p => !string.IsNullOrEmpty(p));

            foreach (var pattern in patterns)
            {
                if (IsMatch(fileName, pattern, caseSensitive))
                    return true;
            }

            return false;
        }

        /// <summary>
        /// ワイルドカードパターンが有効かどうかをチェック
        /// </summary>
        /// <param name="wildcardPattern">ワイルドカードパターン</param>
        /// <returns>有効かどうか</returns>
        public static bool IsValidPattern(string wildcardPattern)
        {
            if (string.IsNullOrEmpty(wildcardPattern))
                return false;

            try
            {
                var regexPattern = ConvertToRegex(wildcardPattern);
                _ = new Regex(regexPattern);
                return true;
            }
            catch
            {
                return false;
            }
        }

        /// <summary>
        /// パターンにワイルドカードが含まれているかどうかをチェック
        /// </summary>
        /// <param name="pattern">チェックするパターン</param>
        /// <returns>ワイルドカードが含まれているかどうか</returns>
        public static bool ContainsWildcards(string pattern)
        {
            return !string.IsNullOrEmpty(pattern) && (pattern.Contains('*') || pattern.Contains('?'));
        }
    }
}