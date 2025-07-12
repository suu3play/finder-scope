using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using FinderScope.Core.Models;

namespace FinderScope.Core.Services
{
    /// <summary>
    /// ファイルプレビュー機能を提供するサービス
    /// </summary>
    public class FilePreviewService : IFilePreviewService
    {
        private static readonly HashSet<string> BinaryExtensions = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
        {
            ".exe", ".dll", ".lib", ".obj", ".bin", ".dat", ".db", ".sqlite", ".mdb",
            ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".ico", ".webp",
            ".mp3", ".wav", ".ogg", ".flac", ".mp4", ".avi", ".mov", ".wmv", ".flv",
            ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz",
            ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx"
        };

        /// <summary>
        /// ファイルのプレビューを生成する
        /// </summary>
        public async Task<FilePreview> GeneratePreviewAsync(FileMatch fileMatch, PreviewSettings settings, CancellationToken cancellationToken = default)
        {
            var stopwatch = System.Diagnostics.Stopwatch.StartNew();
            
            try
            {
                var fileInfo = new FileInfo(fileMatch.FullPath);
                if (!fileInfo.Exists)
                {
                    return new FilePreview
                    {
                        FilePath = fileMatch.FullPath,
                        IsPreviewable = false,
                        PreviewErrorMessage = "ファイルが存在しません",
                        FileSize = 0,
                        LoadTime = stopwatch.Elapsed
                    };
                }

                // ファイルサイズチェック
                if (fileInfo.Length > settings.MaxPreviewSize)
                {
                    return new FilePreview
                    {
                        FilePath = fileMatch.FullPath,
                        IsPreviewable = false,
                        PreviewErrorMessage = $"ファイルサイズが大きすぎます ({fileInfo.Length:N0} bytes)",
                        FileSize = fileInfo.Length,
                        LoadTime = stopwatch.Elapsed
                    };
                }

                // バイナリファイルチェック
                if (settings.EnableBinaryDetection && await IsBinaryFileAsync(fileMatch.FullPath))
                {
                    return new FilePreview
                    {
                        FilePath = fileMatch.FullPath,
                        IsPreviewable = false,
                        PreviewErrorMessage = "バイナリファイルはプレビューできません",
                        FileSize = fileInfo.Length,
                        IsBinaryFile = true,
                        LoadTime = stopwatch.Elapsed
                    };
                }

                // エンコーディング検出
                var encoding = settings.EnableEncodingDetection 
                    ? await DetectEncodingAsync(fileMatch.FullPath, cancellationToken)
                    : Encoding.UTF8;

                // ファイル内容読み込み
                var content = await ReadFileContentAsync(fileMatch.FullPath, encoding, cancellationToken);
                var lines = content.Split('\n');

                var preview = new FilePreview
                {
                    FilePath = fileMatch.FullPath,
                    IsPreviewable = true,
                    FileSize = fileInfo.Length,
                    TotalLines = lines.Length,
                    Encoding = encoding.EncodingName,
                    LoadTime = stopwatch.Elapsed
                };

                // 検索マッチがある場合はその周辺を表示
                if (fileMatch.Matches.Any())
                {
                    ProcessSearchMatches(preview, lines, fileMatch, settings);
                }
                else
                {
                    // マッチがない場合はファイルの先頭から表示
                    ProcessFileFromBeginning(preview, lines, settings);
                }

                return preview;
            }
            catch (Exception ex)
            {
                return new FilePreview
                {
                    FilePath = fileMatch.FullPath,
                    IsPreviewable = false,
                    PreviewErrorMessage = $"プレビュー生成エラー: {ex.Message}",
                    LoadTime = stopwatch.Elapsed
                };
            }
        }

        /// <summary>
        /// ファイルがプレビュー可能かどうかを判定する
        /// </summary>
        public bool IsPreviewable(string filePath)
        {
            try
            {
                var extension = Path.GetExtension(filePath);
                return !BinaryExtensions.Contains(extension);
            }
            catch
            {
                return false;
            }
        }

        /// <summary>
        /// ファイルがバイナリファイルかどうかを判定する
        /// </summary>
        public async Task<bool> IsBinaryFileAsync(string filePath)
        {
            try
            {
                var extension = Path.GetExtension(filePath);
                if (BinaryExtensions.Contains(extension))
                    return true;

                // ファイルの先頭を読んでバイナリチェック
                var buffer = new byte[8192];
                using var stream = new FileStream(filePath, FileMode.Open, FileAccess.Read, FileShare.Read);
                var bytesRead = await stream.ReadAsync(buffer, 0, buffer.Length);
                
                // NULL文字があるかチェック
                for (int i = 0; i < bytesRead; i++)
                {
                    if (buffer[i] == 0)
                        return true;
                }

                return false;
            }
            catch
            {
                return true; // エラーの場合はバイナリとみなす
            }
        }

        /// <summary>
        /// ファイルのエンコーディングを検出する
        /// </summary>
        private static async Task<Encoding> DetectEncodingAsync(string filePath, CancellationToken cancellationToken)
        {
            try
            {
                var buffer = new byte[4096];
                using var stream = new FileStream(filePath, FileMode.Open, FileAccess.Read, FileShare.Read);
                var bytesRead = await stream.ReadAsync(buffer, 0, buffer.Length, cancellationToken);

                // BOM検出
                if (bytesRead >= 3 && buffer[0] == 0xEF && buffer[1] == 0xBB && buffer[2] == 0xBF)
                    return Encoding.UTF8;
                
                if (bytesRead >= 2 && buffer[0] == 0xFF && buffer[1] == 0xFE)
                    return Encoding.Unicode;
                
                if (bytesRead >= 2 && buffer[0] == 0xFE && buffer[1] == 0xFF)
                    return Encoding.BigEndianUnicode;

                // UTF-8判定（簡易版）
                try
                {
                    var testString = Encoding.UTF8.GetString(buffer, 0, bytesRead);
                    var reEncoded = Encoding.UTF8.GetBytes(testString);
                    if (reEncoded.Take(bytesRead).SequenceEqual(buffer.Take(bytesRead)))
                        return Encoding.UTF8;
                }
                catch
                {
                    // UTF-8でない
                }

                return Encoding.UTF8; // デフォルト
            }
            catch
            {
                return Encoding.UTF8;
            }
        }

        /// <summary>
        /// ファイル内容を読み込む
        /// </summary>
        private static async Task<string> ReadFileContentAsync(string filePath, Encoding encoding, CancellationToken cancellationToken)
        {
            using var reader = new StreamReader(filePath, encoding);
            return await reader.ReadToEndAsync();
        }

        /// <summary>
        /// 検索マッチの周辺行を処理
        /// </summary>
        private static void ProcessSearchMatches(FilePreview preview, string[] lines, FileMatch fileMatch, PreviewSettings settings)
        {
            var matches = new List<PreviewMatch>();
            var displayLines = new List<string>();
            var processedLines = new HashSet<int>();

            foreach (var match in fileMatch.Matches)
            {
                var lineIndex = match.LineNumber - 1;
                if (lineIndex < 0 || lineIndex >= lines.Length) continue;

                // 周辺行を取得
                var startLine = Math.Max(0, lineIndex - settings.ContextLines);
                var endLine = Math.Min(lines.Length - 1, lineIndex + settings.ContextLines);

                for (int i = startLine; i <= endLine; i++)
                {
                    if (!processedLines.Contains(i))
                    {
                        displayLines.Add(lines[i]);
                        processedLines.Add(i);

                        // マッチした行の場合はPreviewMatchを作成
                        if (i == lineIndex)
                        {
                            matches.Add(new PreviewMatch
                            {
                                LineNumber = i + 1,
                                StartIndex = match.StartPosition,
                                Length = match.Length,
                                MatchedText = match.MatchedText,
                                Context = lines[i]
                            });
                        }
                    }
                }
            }

            preview.Content = string.Join("\n", displayLines);
            preview.Matches = matches;
            preview.StartLineNumber = processedLines.Any() ? processedLines.Min() + 1 : 1;
            preview.DisplayLines = displayLines.Count;
        }

        /// <summary>
        /// ファイルの先頭から処理
        /// </summary>
        private static void ProcessFileFromBeginning(FilePreview preview, string[] lines, PreviewSettings settings)
        {
            var displayLineCount = Math.Min(lines.Length, settings.MaxDisplayLines);
            var displayLines = lines.Take(displayLineCount).ToArray();

            preview.Content = string.Join("\n", displayLines);
            preview.Matches = new List<PreviewMatch>();
            preview.StartLineNumber = 1;
            preview.DisplayLines = displayLines.Length;
        }
    }
}