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
        private readonly IFilterService _filterService;
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

        [ObservableProperty]
        private SearchFilter? _selectedFilter;

        public ObservableCollection<FileMatch> SearchResults { get; } = new();
        public ObservableCollection<SearchFilter> SavedFilters { get; } = new();

        public MainWindowViewModel(IFileSearchService fileSearchService, IExportService exportService, IFilterService filterService)
        {
            _fileSearchService = fileSearchService;
            _exportService = exportService;
            _filterService = filterService;
            _fileSearchService.ProgressChanged += OnSearchProgressChanged;
            
            // 保存済みフィルタの読み込み
            _ = LoadSavedFiltersAsync();
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

        [RelayCommand]
        private async Task ExportToTxtAsync()
        {
            await ExportResultsAsync(ExportFormat.Txt, "テキスト ファイル (*.txt)|*.txt");
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
                        case ExportFormat.Txt:
                            await _exportService.ExportToTxtAsync(_lastSearchResult, saveDialog.FileName);
                            break;
                    }

                    // エクスポート完了ダイアログを表示し、ファイルを開くかどうか確認
                    var result = WinMessageBox.Show(
                        $"エクスポートが完了しました。\n{saveDialog.FileName}\n\nファイルを開きますか？", 
                        "エクスポート完了", 
                        MessageBoxButton.YesNo, 
                        MessageBoxImage.Information);

                    if (result == MessageBoxResult.Yes)
                    {
                        OpenExportedFile(saveDialog.FileName);
                    }
                }
                catch (Exception ex)
                {
                    WinMessageBox.Show($"エクスポート中にエラーが発生しました: {ex.Message}", "エラー", MessageBoxButton.OK, MessageBoxImage.Error);
                }
            }
        }

        /// <summary>
        /// エクスポートされたファイルを開く
        /// </summary>
        private void OpenExportedFile(string filePath)
        {
            try
            {
                System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo
                {
                    FileName = filePath,
                    UseShellExecute = true
                });
            }
            catch (Exception ex)
            {
                WinMessageBox.Show($"ファイルを開けませんでした: {ex.Message}", "エラー", MessageBoxButton.OK, MessageBoxImage.Error);
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

        #region フィルタ関連メソッド

        /// <summary>
        /// 保存済みフィルタを読み込み
        /// </summary>
        private async Task LoadSavedFiltersAsync()
        {
            try
            {
                var filters = await _filterService.GetFiltersAsync();
                SavedFilters.Clear();
                
                // 空のアイテムを先頭に追加（フィルタなし選択用）
                SavedFilters.Add(new SearchFilter { Name = "-- フィルタなし --", Id = string.Empty });
                
                foreach (var filter in filters)
                {
                    SavedFilters.Add(filter);
                }

                // デフォルトフィルタがある場合は適用
                var defaultFilter = await _filterService.GetDefaultFilterAsync();
                if (defaultFilter != null)
                {
                    SelectedFilter = SavedFilters.FirstOrDefault(f => f.Id == defaultFilter.Id);
                    if (SelectedFilter != null)
                    {
                        ApplyFilter(SelectedFilter);
                    }
                }
            }
            catch (Exception ex)
            {
                WinMessageBox.Show($"フィルタの読み込みでエラーが発生しました: {ex.Message}", "エラー", MessageBoxButton.OK, MessageBoxImage.Warning);
            }
        }

        /// <summary>
        /// フィルタを適用
        /// </summary>
        [RelayCommand]
        private async Task ApplySelectedFilterAsync()
        {
            if (SelectedFilter != null && !string.IsNullOrEmpty(SelectedFilter.Id))
            {
                ApplyFilter(SelectedFilter);
                await _filterService.RecordFilterUsageAsync(SelectedFilter.Id);
            }
        }

        /// <summary>
        /// フィルタを検索条件に適用
        /// </summary>
        private void ApplyFilter(SearchFilter filter)
        {
            if (string.IsNullOrEmpty(filter.Id)) return; // "フィルタなし"の場合は何もしない

            var criteria = filter.Criteria;
            TargetFolder = criteria.TargetFolder;
            FilenamePattern = criteria.FilenamePattern ?? string.Empty;
            FileExtensions = string.Join(", ", criteria.FileExtensions);
            DateFrom = criteria.DateFrom;
            DateTo = criteria.DateTo;
            ContentPattern = criteria.ContentPattern ?? string.Empty;
            UseRegex = criteria.UseRegex;
            CaseSensitive = criteria.CaseSensitive;
            IncludeSubdirectories = criteria.IncludeSubdirectories;
        }

        /// <summary>
        /// 現在の検索条件をフィルタとして保存
        /// </summary>
        [RelayCommand]
        private async Task SaveCurrentFilterAsync()
        {
            try
            {
                var criteria = CreateSearchCriteria();
                if (!criteria.IsValid())
                {
                    WinMessageBox.Show("有効な検索条件を入力してからフィルタを保存してください。", "情報", MessageBoxButton.OK, MessageBoxImage.Information);
                    return;
                }

                var dialog = new Views.SaveFilterDialog();
                var viewModel = new SaveFilterDialogViewModel(_filterService)
                {
                    SearchCriteria = criteria
                };
                
                // 推奨名を生成
                viewModel.GenerateSuggestedName();
                
                dialog.DataContext = viewModel;
                dialog.Owner = System.Windows.Application.Current.MainWindow;

                if (dialog.ShowDialog() == true && viewModel.DialogResult)
                {
                    // フィルタリストを再読み込み
                    await LoadSavedFiltersAsync();
                    WinMessageBox.Show("フィルタが保存されました。", "完了", MessageBoxButton.OK, MessageBoxImage.Information);
                }
            }
            catch (Exception ex)
            {
                WinMessageBox.Show($"フィルタの保存でエラーが発生しました: {ex.Message}", "エラー", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        /// <summary>
        /// 選択したフィルタを削除
        /// </summary>
        [RelayCommand]
        private async Task DeleteSelectedFilterAsync()
        {
            if (SelectedFilter == null || string.IsNullOrEmpty(SelectedFilter.Id))
            {
                WinMessageBox.Show("削除するフィルタを選択してください。", "情報", MessageBoxButton.OK, MessageBoxImage.Information);
                return;
            }

            var result = WinMessageBox.Show(
                $"フィルタ「{SelectedFilter.Name}」を削除しますか？", 
                "確認", 
                MessageBoxButton.YesNo, 
                MessageBoxImage.Question);

            if (result == MessageBoxResult.Yes)
            {
                try
                {
                    await _filterService.DeleteFilterAsync(SelectedFilter.Id);
                    await LoadSavedFiltersAsync();
                    WinMessageBox.Show("フィルタが削除されました。", "完了", MessageBoxButton.OK, MessageBoxImage.Information);
                }
                catch (Exception ex)
                {
                    WinMessageBox.Show($"フィルタの削除でエラーが発生しました: {ex.Message}", "エラー", MessageBoxButton.OK, MessageBoxImage.Error);
                }
            }
        }

        /// <summary>
        /// 選択したフィルタをデフォルトに設定
        /// </summary>
        [RelayCommand]
        private async Task SetAsDefaultFilterAsync()
        {
            if (SelectedFilter == null || string.IsNullOrEmpty(SelectedFilter.Id))
            {
                WinMessageBox.Show("デフォルトに設定するフィルタを選択してください。", "情報", MessageBoxButton.OK, MessageBoxImage.Information);
                return;
            }

            try
            {
                await _filterService.SetDefaultFilterAsync(SelectedFilter.Id);
                await LoadSavedFiltersAsync();
                WinMessageBox.Show($"フィルタ「{SelectedFilter.Name}」をデフォルトに設定しました。", "完了", MessageBoxButton.OK, MessageBoxImage.Information);
            }
            catch (Exception ex)
            {
                WinMessageBox.Show($"デフォルト設定でエラーが発生しました: {ex.Message}", "エラー", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        #endregion
    }
}