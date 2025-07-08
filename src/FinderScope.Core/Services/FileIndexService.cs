using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using FinderScope.Core.Models;

namespace FinderScope.Core.Services
{
    /// <summary>
    /// ファイルインデックスサービスの実装
    /// </summary>
    public class FileIndexService : IFileIndexService, IDisposable
    {
        private readonly string _indexDirectory;
        private readonly string _indexFilePath;
        private readonly JsonSerializerOptions _jsonOptions;
        private readonly ConcurrentDictionary<string, FileIndexEntry> _fileIndex;
        private readonly Timer? _backgroundTimer;
        private readonly SemaphoreSlim _indexingSemaphore;
        private bool _isIndexing;
        private bool _disposed;

        public event EventHandler<IndexProgressEventArgs>? IndexProgressChanged;

        public bool IsIndexing => _isIndexing;

        public FileIndexService()
        {
            // インデックスデータの保存場所
            var appDataPath = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);
            _indexDirectory = Path.Combine(appDataPath, "FinderScope", "Index");
            _indexFilePath = Path.Combine(_indexDirectory, "file_index.json");

            _jsonOptions = new JsonSerializerOptions
            {
                WriteIndented = false,
                PropertyNamingPolicy = JsonNamingPolicy.CamelCase
            };

            _fileIndex = new ConcurrentDictionary<string, FileIndexEntry>();
            _indexingSemaphore = new SemaphoreSlim(1, 1);

            // バックグラウンドで5分おきにインデックス更新
            _backgroundTimer = new Timer(BackgroundUpdate, null, TimeSpan.FromMinutes(5), TimeSpan.FromMinutes(5));

            // 初期化時にインデックスを読み込み
            _ = Task.Run(LoadIndexAsync);
        }

        /// <summary>
        /// 全ドライブのインデックスを開始
        /// </summary>
        public async Task StartFullIndexAsync(CancellationToken cancellationToken = default)
        {
            if (!await _indexingSemaphore.WaitAsync(100, cancellationToken))
                return; // 既に実行中

            try
            {
                _isIndexing = true;
                var startTime = DateTime.Now;

                // 利用可能なドライブを取得
                var drives = DriveInfo.GetDrives()
                    .Where(d => d.IsReady && (d.DriveType == DriveType.Fixed || d.DriveType == DriveType.Removable))
                    .ToList();

                var totalFiles = 0;
                var processedFiles = 0;

                foreach (var drive in drives)
                {
                    if (cancellationToken.IsCancellationRequested)
                        break;

                    await IndexDriveAsync(drive, cancellationToken, (current, total, elapsed) =>
                    {
                        processedFiles = current;
                        var progress = totalFiles > 0 ? (double)processedFiles / totalFiles * 100 : 0;
                        
                        IndexProgressChanged?.Invoke(this, new IndexProgressEventArgs
                        {
                            CurrentDrive = drive.Name,
                            FilesProcessed = processedFiles,
                            TotalFiles = totalFiles,
                            ProgressPercentage = progress,
                            ElapsedTime = elapsed
                        });
                    });
                }

                await SaveIndexAsync();

                IndexProgressChanged?.Invoke(this, new IndexProgressEventArgs
                {
                    FilesProcessed = processedFiles,
                    TotalFiles = totalFiles,
                    ProgressPercentage = 100,
                    ElapsedTime = DateTime.Now - startTime,
                    IsCompleted = true
                });
            }
            catch (Exception ex)
            {
                IndexProgressChanged?.Invoke(this, new IndexProgressEventArgs
                {
                    ErrorMessage = ex.Message,
                    IsCompleted = true
                });
            }
            finally
            {
                _isIndexing = false;
                _indexingSemaphore.Release();
            }
        }

        /// <summary>
        /// 特定のドライブのインデックスを開始
        /// </summary>
        public async Task StartDriveIndexAsync(string driveLetter, CancellationToken cancellationToken = default)
        {
            var drive = DriveInfo.GetDrives()
                .FirstOrDefault(d => d.Name.StartsWith(driveLetter, StringComparison.OrdinalIgnoreCase));

            if (drive?.IsReady != true)
                throw new ArgumentException($"ドライブ {driveLetter} は利用できません。");

            if (!await _indexingSemaphore.WaitAsync(100, cancellationToken))
                return;

            try
            {
                _isIndexing = true;
                await IndexDriveAsync(drive, cancellationToken);
                await SaveIndexAsync();
            }
            finally
            {
                _isIndexing = false;
                _indexingSemaphore.Release();
            }
        }

        /// <summary>
        /// ファイル名でクイック検索
        /// </summary>
        public async Task<IEnumerable<FileIndexEntry>> QuickSearchAsync(string fileName, int maxResults = 1000)
        {
            await EnsureIndexLoadedAsync();

            if (string.IsNullOrWhiteSpace(fileName))
                return Enumerable.Empty<FileIndexEntry>();

            var searchTerm = fileName.ToLowerInvariant();
            
            return _fileIndex.Values
                .Where(entry => entry.FileName.ToLowerInvariant().Contains(searchTerm))
                .OrderBy(entry => entry.FileName.Length) // より短いファイル名を優先
                .ThenBy(entry => entry.FileName.ToLowerInvariant())
                .Take(maxResults)
                .ToList();
        }

        /// <summary>
        /// 拡張子でフィルタリング
        /// </summary>
        public async Task<IEnumerable<FileIndexEntry>> SearchByExtensionAsync(IEnumerable<string> extensions, int maxResults = 1000)
        {
            await EnsureIndexLoadedAsync();

            var extSet = new HashSet<string>(
                extensions.Select(ext => ext.StartsWith(".") ? ext.ToLowerInvariant() : $".{ext.ToLowerInvariant()}")
            );

            return _fileIndex.Values
                .Where(entry => extSet.Contains(entry.Extension))
                .OrderBy(entry => entry.FileName)
                .Take(maxResults)
                .ToList();
        }

        /// <summary>
        /// パターンマッチング検索
        /// </summary>
        public async Task<IEnumerable<FileIndexEntry>> SearchByPatternAsync(string pattern, bool useRegex = false, bool caseSensitive = false, int maxResults = 1000)
        {
            await EnsureIndexLoadedAsync();

            if (string.IsNullOrWhiteSpace(pattern))
                return Enumerable.Empty<FileIndexEntry>();

            if (useRegex)
            {
                try
                {
                    var regexOptions = caseSensitive ? RegexOptions.None : RegexOptions.IgnoreCase;
                    var regex = new Regex(pattern, regexOptions);

                    return _fileIndex.Values
                        .Where(entry => regex.IsMatch(entry.FileName))
                        .OrderBy(entry => entry.FileName)
                        .Take(maxResults)
                        .ToList();
                }
                catch
                {
                    // 正規表現が無効な場合は通常検索にフォールバック
                }
            }

            var comparison = caseSensitive ? StringComparison.Ordinal : StringComparison.OrdinalIgnoreCase;
            
            return _fileIndex.Values
                .Where(entry => entry.FileName.Contains(pattern, comparison))
                .OrderBy(entry => entry.FileName)
                .Take(maxResults)
                .ToList();
        }

        /// <summary>
        /// インデックス統計情報を取得
        /// </summary>
        public async Task<IndexStatistics> GetStatisticsAsync()
        {
            await EnsureIndexLoadedAsync();

            var stats = new IndexStatistics
            {
                TotalFiles = _fileIndex.Count,
                TotalSize = _fileIndex.Values.Sum(f => f.Size)
            };

            // 拡張子別統計
            foreach (var group in _fileIndex.Values.GroupBy(f => f.Extension))
            {
                stats.ExtensionCounts[group.Key] = group.Count();
            }

            // ドライブ別統計
            foreach (var group in _fileIndex.Values.GroupBy(f => Path.GetPathRoot(f.FullPath)))
            {
                var driveLetter = group.Key ?? "Unknown";
                var driveInfo = new DriveIndexInfo
                {
                    DriveLetter = driveLetter,
                    FileCount = group.Count(),
                    LastIndexed = group.Max(f => f.IndexedAt)
                };
                stats.DriveInfos.Add(driveInfo);
            }

            return stats;
        }

        /// <summary>
        /// インデックス更新（変更された部分のみ）
        /// </summary>
        public async Task UpdateIndexAsync(CancellationToken cancellationToken = default)
        {
            if (_isIndexing) return;

            await EnsureIndexLoadedAsync();

            // 変更されたファイルを検出して更新
            var updatedEntries = new List<FileIndexEntry>();
            var removedPaths = new List<string>();

            foreach (var entry in _fileIndex.Values.ToList())
            {
                if (cancellationToken.IsCancellationRequested) break;

                try
                {
                    if (File.Exists(entry.FullPath))
                    {
                        var fileInfo = new FileInfo(entry.FullPath);
                        if (entry.IsModified(fileInfo))
                        {
                            var updatedEntry = FileIndexEntry.FromFileInfo(fileInfo);
                            _fileIndex.TryUpdate(entry.FullPath, updatedEntry, entry);
                            updatedEntries.Add(updatedEntry);
                        }
                    }
                    else
                    {
                        // ファイルが削除されている
                        _fileIndex.TryRemove(entry.FullPath, out _);
                        removedPaths.Add(entry.FullPath);
                    }
                }
                catch
                {
                    // アクセスできないファイルはスキップ
                }
            }

            if (updatedEntries.Any() || removedPaths.Any())
            {
                await SaveIndexAsync();
            }
        }

        /// <summary>
        /// インデックスをクリア
        /// </summary>
        public async Task ClearIndexAsync()
        {
            _fileIndex.Clear();
            await SaveIndexAsync();
        }

        /// <summary>
        /// インデックスが利用可能か確認
        /// </summary>
        public async Task<bool> IsIndexAvailableAsync()
        {
            await EnsureIndexLoadedAsync();
            return _fileIndex.Any();
        }

        /// <summary>
        /// バックグラウンドでインデックス更新を開始
        /// </summary>
        public void StartBackgroundIndexing()
        {
            // バックグラウンドタイマーは既に開始されている
        }

        /// <summary>
        /// バックグラウンドインデックス更新を停止
        /// </summary>
        public void StopBackgroundIndexing()
        {
            _backgroundTimer?.Change(Timeout.Infinite, Timeout.Infinite);
        }

        private async Task IndexDriveAsync(DriveInfo drive, CancellationToken cancellationToken, Action<int, int, TimeSpan>? progressCallback = null)
        {
            var startTime = DateTime.Now;
            var processedCount = 0;

            try
            {
                await Task.Run(() =>
                {
                    IndexDirectoryRecursive(drive.RootDirectory, cancellationToken, ref processedCount, startTime, progressCallback);
                }, cancellationToken);
            }
            catch (OperationCanceledException)
            {
                // キャンセルされた場合は正常終了
            }
        }

        private void IndexDirectoryRecursive(DirectoryInfo directory, CancellationToken cancellationToken, ref int processedCount, DateTime startTime, Action<int, int, TimeSpan>? progressCallback)
        {
            if (cancellationToken.IsCancellationRequested) return;

            try
            {
                // ファイルを処理
                foreach (var file in directory.EnumerateFiles())
                {
                    if (cancellationToken.IsCancellationRequested) break;

                    try
                    {
                        var entry = FileIndexEntry.FromFileInfo(file);
                        _fileIndex.AddOrUpdate(file.FullName, entry, (key, old) => entry);
                        
                        processedCount++;
                        
                        if (processedCount % 100 == 0) // 100ファイル毎に進行状況を報告
                        {
                            progressCallback?.Invoke(processedCount, 0, DateTime.Now - startTime);
                        }
                    }
                    catch
                    {
                        // アクセスできないファイルはスキップ
                    }
                }

                // サブディレクトリを処理
                foreach (var subDir in directory.EnumerateDirectories())
                {
                    if (cancellationToken.IsCancellationRequested) break;

                    try
                    {
                        IndexDirectoryRecursive(subDir, cancellationToken, ref processedCount, startTime, progressCallback);
                    }
                    catch
                    {
                        // アクセスできないディレクトリはスキップ
                    }
                }
            }
            catch
            {
                // ディレクトリアクセスエラーはスキップ
            }
        }

        private async Task EnsureIndexLoadedAsync()
        {
            if (!_fileIndex.Any() && File.Exists(_indexFilePath))
            {
                await LoadIndexAsync();
            }
        }

        private async Task LoadIndexAsync()
        {
            try
            {
                if (File.Exists(_indexFilePath))
                {
                    var json = await File.ReadAllTextAsync(_indexFilePath);
                    var entries = JsonSerializer.Deserialize<List<FileIndexEntry>>(json, _jsonOptions);
                    
                    if (entries != null)
                    {
                        _fileIndex.Clear();
                        foreach (var entry in entries)
                        {
                            _fileIndex.TryAdd(entry.FullPath, entry);
                        }
                    }
                }
            }
            catch
            {
                // インデックスファイルが破損している場合は空で開始
                _fileIndex.Clear();
            }
        }

        private async Task SaveIndexAsync()
        {
            try
            {
                if (!Directory.Exists(_indexDirectory))
                {
                    Directory.CreateDirectory(_indexDirectory);
                }

                var entries = _fileIndex.Values.ToList();
                var json = JsonSerializer.Serialize(entries, _jsonOptions);
                await File.WriteAllTextAsync(_indexFilePath, json);
            }
            catch
            {
                // 保存エラーは無視（次回保存時に再試行）
            }
        }

        private async void BackgroundUpdate(object? state)
        {
            if (_isIndexing) return;

            try
            {
                await UpdateIndexAsync();
            }
            catch
            {
                // バックグラウンド更新のエラーは無視
            }
        }

        public void Dispose()
        {
            if (!_disposed)
            {
                _backgroundTimer?.Dispose();
                _indexingSemaphore?.Dispose();
                _disposed = true;
            }
        }
    }
}