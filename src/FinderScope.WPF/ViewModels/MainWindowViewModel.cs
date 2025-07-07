using System;
using System.Collections.ObjectModel;
using System.IO;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Input;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using FinderScope.Core.Models;
using FinderScope.Core.Services;
using Microsoft.Win32;
using WinMessageBox = System.Windows.MessageBox;

namespace FinderScope.WPF.ViewModels
{
    /// <summary>
    /// メインウィンドウのViewModel
    /// </summary>
    public partial class MainWindowViewModel : ObservableObject
    {
        private readonly IFileSearchService _fileSearchService;
        private readonly IExportService _exportService;
        private CancellationTokenSource? _searchCancellationTokenSource;
        private SearchResult? _lastSearchResult;

        [ObservableProperty]
        private string _targetFolder = Environment.GetFolderPath(Environment.SpecialFolder.Desktop);

        [ObservableProperty]
        private string _filenamePattern = string.Empty;

        [ObservableProperty]
        private string _fileExtensions = string.Empty;

        [ObservableProperty]
        private DateTime? _dateFrom;

        [ObservableProperty]
        private DateTime? _dateTo;

        [ObservableProperty]
        private string _contentPattern = string.Empty;

        [ObservableProperty]
        private bool _useRegex = false;

        [ObservableProperty]
        private bool _caseSensitive = false;

        [ObservableProperty]
        private bool _includeSubdirectories = true;

        [ObservableProperty]
        private bool _isSearching = false;

        [ObservableProperty]
        private string _searchStatus = "検索準備完了";

        [ObservableProperty]
        private double _progressPercentage = 0;

        [ObservableProperty]
        private int _filesScanned = 0;

        [ObservableProperty]
        private int _filesMatched = 0;

        [ObservableProperty]
        private string _currentFile = string.Empty;

        [ObservableProperty]
        private TimeSpan _elapsedTime;

        public ObservableCollection<FileMatch> SearchResults { get; } = new();

        public MainWindowViewModel(IFileSearchService fileSearchService, IExportService exportService)
        {
            _fileSearchService = fileSearchService;
            _exportService = exportService;
            _fileSearchService.ProgressChanged += OnSearchProgressChanged;
        }

        [RelayCommand]
        private async Task StartSearchAsync()
        {
            if (IsSearching) return;

            // 検索条件の検証
            if (string.IsNullOrWhiteSpace(TargetFolder) || !Directory.Exists(TargetFolder))
            {
                WinMessageBox.Show("有効なフォルダを指定してください。", "エラー",  MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            try
            {
                IsSearching = true;
                SearchStatus = "検索中...";
                SearchResults.Clear();
                ProgressPercentage = 0;
                FilesScanned = 0;
                FilesMatched = 0;
                CurrentFile = string.Empty;
                ElapsedTime = TimeSpan.Zero;

                _searchCancellationTokenSource = new CancellationTokenSource();

                var criteria = CreateSearchCriteria();
                var result = await _fileSearchService.SearchAsync(criteria, _searchCancellationTokenSource.Token);

                // 検索結果を保存
                _lastSearchResult = result;

                // 結果をUIに反映
                foreach (var fileMatch in result.FileMatches)
                {
                    SearchResults.Add(fileMatch);
                }

                if (result.WasCancelled)
                {
                    SearchStatus = "検索がキャンセルされました";
                }
                else if (!string.IsNullOrEmpty(result.ErrorMessage))
                {
                    SearchStatus = $"エラー: {result.ErrorMessage}";
                    WinMessageBox.Show($"検索中にエラーが発生しました: {result.ErrorMessage}", "エラー", MessageBoxButton.OK, MessageBoxImage.Error);
                }
                else
                {
                    SearchStatus = $"検索完了 - {result.FileMatches.Count}件のファイルが見つかりました ({result.SearchDurationSeconds:F2}秒)";
                }
            }
            catch (OperationCanceledException)
            {
                SearchStatus = "検索がキャンセルされました";
            }
            catch (Exception ex)
            {
                SearchStatus = $"エラー: {ex.Message}";
                WinMessageBox.Show($"検索中にエラーが発生しました: {ex.Message}", "エラー", MessageBoxButton.OK, MessageBoxImage.Error);
            }
            finally
            {
                IsSearching = false;
                _searchCancellationTokenSource?.Dispose();
                _searchCancellationTokenSource = null;
            }
        }

        [RelayCommand]
        private void CancelSearch()
        {
            _searchCancellationTokenSource?.Cancel();
        }

        [RelayCommand]
        private void BrowseFolder()
        {
            var dialog = new OpenFileDialog
            {
                Title = "検索対象フォルダを選択してください",
                CheckFileExists = false,
                CheckPathExists = true,
                ValidateNames = false,
                FileName = "フォルダを選択",
                Filter = "フォルダ|*.folder"
            };

            if (!string.IsNullOrEmpty(TargetFolder) && Directory.Exists(TargetFolder))
            {
                dialog.InitialDirectory = TargetFolder;
            }

            if (dialog.ShowDialog() == true)
            {
                TargetFolder = Path.GetDirectoryName(dialog.FileName) ?? TargetFolder;
            }
        }

        [RelayCommand]
        private void OpenFile(FileMatch? fileMatch)
        {
            if (fileMatch == null) return;

            try
            {
                System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo
                {
                    FileName = fileMatch.FullPath,
                    UseShellExecute = true
                });
            }
            catch (Exception ex)
            {
                WinMessageBox.Show($"ファイルを開けませんでした: {ex.Message}", "エラー", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        [RelayCommand]
        private void OpenFileLocation(FileMatch? fileMatch)
        {
            if (fileMatch == null) return;

            try
            {
                System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo
                {
                    FileName = "explorer.exe",
                    Arguments = $"/select,\"{fileMatch.FullPath}\"",
                    UseShellExecute = true
                });
            }
            catch (Exception ex)
            {
                WinMessageBox.Show($"フォルダを開けませんでした: {ex.Message}", "エラー", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        [RelayCommand]
        private void ClearResults()
        {
            SearchResults.Clear();
            SearchStatus = "検索準備完了";
            ProgressPercentage = 0;
            FilesScanned = 0;
            FilesMatched = 0;
            CurrentFile = string.Empty;
            ElapsedTime = TimeSpan.Zero;
            _lastSearchResult = null;
        }

        [RelayCommand]
        private async Task ExportToCsvAsync()
        {
            await ExportResultsAsync(ExportFormat.Csv, "CSV ファイル (*.csv)|*.csv");
        }

        [RelayCommand]
        private async Task ExportToJsonAsync()
        {
            await ExportResultsAsync(ExportFormat.Json, "JSON ファイル (*.json)|*.json");
        }

        [RelayCommand]
        private async Task ExportToHtmlAsync()
        {
            await ExportResultsAsync(ExportFormat.Html, "HTML ファイル (*.html)|*.html");
        }

        private async Task ExportResultsAsync(ExportFormat format, string filter)
        {
            if (_lastSearchResult == null || !_lastSearchResult.FileMatches.Any())
            {
                WinMessageBox.Show("エクスポートする検索結果がありません。", "情報", MessageBoxButton.OK, MessageBoxImage.Information);
                return;
            }

            var saveDialog = new Microsoft.Win32.SaveFileDialog
            {
                Filter = filter,
                DefaultExt = format.ToString().ToLower(),
                FileName = $"FinderScope_検索結果_{DateTime.Now:yyyyMMdd_HHmmss}"
            };

            if (saveDialog.ShowDialog() == true)
            {
                try
                {
                    switch (format)
                    {
                        case ExportFormat.Csv:
                            await _exportService.ExportToCsvAsync(_lastSearchResult, saveDialog.FileName);
                            break;
                        case ExportFormat.Json:
                            await _exportService.ExportToJsonAsync(_lastSearchResult, saveDialog.FileName);
                            break;
                        case ExportFormat.Html:
                            await _exportService.ExportToHtmlAsync(_lastSearchResult, saveDialog.FileName);
                            break;
                    }

                    WinMessageBox.Show($"エクスポートが完了しました。\n{saveDialog.FileName}", "完了", MessageBoxButton.OK, MessageBoxImage.Information);
                }
                catch (Exception ex)
                {
                    WinMessageBox.Show($"エクスポート中にエラーが発生しました: {ex.Message}", "エラー", MessageBoxButton.OK, MessageBoxImage.Error);
                }
            }
        }

        private SearchCriteria CreateSearchCriteria()
        {
            var extensions = FileExtensions
                .Split(new[] { ',', ';', ' ' }, StringSplitOptions.RemoveEmptyEntries)
                .Select(ext => ext.Trim())
                .Where(ext => !string.IsNullOrWhiteSpace(ext))
                .Select(ext => ext.StartsWith(".") ? ext : "." + ext)
                .ToList();

            return new SearchCriteria
            {
                TargetFolder = TargetFolder,
                FilenamePattern = string.IsNullOrWhiteSpace(FilenamePattern) ? null : FilenamePattern,
                FileExtensions = extensions,
                DateFrom = DateFrom,
                DateTo = DateTo,
                ContentPattern = string.IsNullOrWhiteSpace(ContentPattern) ? null : ContentPattern,
                UseRegex = UseRegex,
                CaseSensitive = CaseSensitive,
                IncludeSubdirectories = IncludeSubdirectories
            };
        }

        private void OnSearchProgressChanged(object? sender, SearchProgressEventArgs e)
        {
            System.Windows.Application.Current.Dispatcher.Invoke(() =>
            {
                FilesScanned = e.FilesScanned;
                FilesMatched = e.FilesMatched;
                CurrentFile = Path.GetFileName(e.CurrentFile);
                ProgressPercentage = e.ProgressPercentage;
                ElapsedTime = e.ElapsedTime;
            });
        }
    }
}