using System;
using System.Collections.Generic;
using System.IO;

namespace FinderScope.Core.Models
{
    /// <summary>
    /// ファイルインデックスエントリ
    /// </summary>
    public class FileIndexEntry
    {
        public string FullPath { get; set; } = string.Empty;
        public string FileName { get; set; } = string.Empty;
        public string Directory { get; set; } = string.Empty;
        public string Extension { get; set; } = string.Empty;
        public long Size { get; set; }
        public DateTime LastModified { get; set; }
        public DateTime IndexedAt { get; set; } = DateTime.Now;
        
        /// <summary>
        /// ファイル情報から新しいエントリを作成
        /// </summary>
        public static FileIndexEntry FromFileInfo(FileInfo fileInfo)
        {
            return new FileIndexEntry
            {
                FullPath = fileInfo.FullName,
                FileName = fileInfo.Name,
                Directory = fileInfo.DirectoryName ?? string.Empty,
                Extension = fileInfo.Extension.ToLowerInvariant(),
                Size = fileInfo.Length,
                LastModified = fileInfo.LastWriteTime,
                IndexedAt = DateTime.Now
            };
        }
        
        /// <summary>
        /// ファイルが変更されているかチェック
        /// </summary>
        public bool IsModified(FileInfo fileInfo)
        {
            return fileInfo.LastWriteTime != LastModified || 
                   fileInfo.Length != Size;
        }
    }

    /// <summary>
    /// ドライブ情報
    /// </summary>
    public class DriveIndexInfo
    {
        public string DriveLetter { get; set; } = string.Empty;
        public string DriveType { get; set; } = string.Empty;
        public string Label { get; set; } = string.Empty;
        public long TotalSize { get; set; }
        public long FreeSpace { get; set; }
        public DateTime LastIndexed { get; set; }
        public int FileCount { get; set; }
        public bool IsIndexing { get; set; }
        public double IndexingProgress { get; set; }
    }

    /// <summary>
    /// インデックス統計情報
    /// </summary>
    public class IndexStatistics
    {
        public int TotalFiles { get; set; }
        public int TotalDirectories { get; set; }
        public long TotalSize { get; set; }
        public DateTime LastFullIndex { get; set; }
        public TimeSpan IndexingDuration { get; set; }
        public Dictionary<string, int> ExtensionCounts { get; set; } = new();
        public List<DriveIndexInfo> DriveInfos { get; set; } = new();
    }
}