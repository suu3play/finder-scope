using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;

namespace FinderScope.Core.Models
{
    /// <summary>
    /// 検索にマッチしたファイル情報
    /// </summary>
    public class FileMatch
    {
        public string FilePath { get; set; } = string.Empty;
        public string FileName { get; set; } = string.Empty;
        public string Directory { get; set; } = string.Empty;
        public DateTime LastModified { get; set; }
        public long FileSize { get; set; }
        public List<ContentMatch> Matches { get; set; } = new();

        /// <summary>
        /// フルパス（FilePath のエイリアス）
        /// </summary>
        public string FullPath => FilePath;

        /// <summary>
        /// ファイル情報から FileMatch を作成
        /// </summary>
        public static FileMatch FromFileInfo(FileInfo fileInfo)
        {
            return new FileMatch
            {
                FilePath = fileInfo.FullName,
                FileName = fileInfo.Name,
                Directory = fileInfo.DirectoryName ?? string.Empty,
                LastModified = fileInfo.LastWriteTime,
                FileSize = fileInfo.Length
            };
        }

        /// <summary>
        /// マッチ数
        /// </summary>
        public int MatchCount => Matches.Count;

        /// <summary>
        /// ファイル拡張子
        /// </summary>
        public string FileExtension => Path.GetExtension(FilePath);

        /// <summary>
        /// 相対パス表示用
        /// </summary>
        public string RelativePath => FilePath;

        /// <summary>
        /// ファイルサイズの整形表示
        /// </summary>
        public string FormattedSize
        {
            get
            {
                const long KB = 1024;
                const long MB = KB * 1024;
                const long GB = MB * 1024;

                return FileSize switch
                {
                    < KB => $"{FileSize} B",
                    < MB => $"{FileSize / (double)KB:F1} KB",
                    < GB => $"{FileSize / (double)MB:F1} MB",
                    _ => $"{FileSize / (double)GB:F1} GB"
                };
            }
        }

        /// <summary>
        /// コンテンツマッチを追加
        /// </summary>
        public void AddContentMatch(ContentMatch match)
        {
            Matches.Add(match);
        }

        /// <summary>
        /// すべてのマッチテキストを取得
        /// </summary>
        public IEnumerable<string> GetAllMatchedTexts()
        {
            return Matches.Select(m => m.MatchedText).Distinct();
        }
    }
}