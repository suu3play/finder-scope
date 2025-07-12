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
    public partial class MainWindowViewModel : ObservableObject, IDisposable
    {
        private readonly IFileSearchService _fileSearchService;
        private readonly IExportService _exportService;
        private readonly IFilterService _filterService;
        private readonly IFileIndexService _fileIndexService;
        private readonly ISearchHistoryService _searchHistoryService;
        private readonly IFilePreviewService _filePreviewService;
        private CancellationTokenSource? _searchCancellationTokenSource;
        private SearchResult? _lastSearchResult;
        private Timer? _autoSearchTimer;
        private DateTime _lastSearchTime;
        private bool _isApplyingFilter = false;

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

        // 拡張子選択用プロパティ
        [ObservableProperty]
        private bool _isTxtSelected;

        [ObservableProperty]
        private bool _isLogSelected;

        [ObservableProperty]
        private bool _isCsSelected;

        [ObservableProperty]
        private bool _isJsSelected;

        [ObservableProperty]
        private bool _isPySelected;

        [ObservableProperty]
        private bool _isXmlSelected;

        [ObservableProperty]
        private bool _isJsonSelected;

        [ObservableProperty]
        private bool _enableAutoSearch = false;

        [ObservableProperty]
        private bool _caseInsensitive = true;

        [ObservableProperty]
        private bool _wholeWordOnly = false;

        [ObservableProperty]
        private FileMatch? _selectedFileMatch;

        [ObservableProperty]
        private FilePreview? _currentFilePreview;

        [ObservableProperty]
        private bool _isPreviewLoading = false;

        [ObservableProperty]
        private string _previewStatusMessage = string.Empty;

        [ObservableProperty]
        private FileCategory _selectedCategory = FileCategory.Document;

        // ラジオボタン用のカテゴリ選択プロパティ
        [ObservableProperty]
        private bool _isDocumentCategorySelected = true;

        [ObservableProperty]
        private bool _isCodeCategorySelected = false;

        [ObservableProperty]
        private bool _isWebCategorySelected = false;

        [ObservableProperty]
        private bool _isAllCategorySelected = false;

        // カテゴリ別の拡張子ボタンの表示状態
        [ObservableProperty]
        private bool _isTxtVisible;

        [ObservableProperty]
        private bool _isLogVisible;

        [ObservableProperty]
        private bool _isCsVisible;

        [ObservableProperty]
        private bool _isJsVisible;

        [ObservableProperty]
        private bool _isPyVisible;

        [ObservableProperty]
        private bool _isXmlVisible;

        [ObservableProperty]
        private bool _isJsonVisible;

        public ObservableCollection<FileMatch> SearchResults { get; } = new();
        public ObservableCollection<SearchFilter> SavedFilters { get; } = new();
        public ObservableCollection<FileCategoryInfo> FileCategories { get; } = new();

        public MainWindowViewModel(IFileSearchService fileSearchService, IExportService exportService, IFilterService filterService, IFileIndexService fileIndexService, ISearchHistoryService searchHistoryService, IFilePreviewService filePreviewService)
        {
            _fileSearchService = fileSearchService;
            _exportService = exportService;
            _filterService = filterService;
            _fileIndexService = fileIndexService;
            _searchHistoryService = searchHistoryService;
            _filePreviewService = filePreviewService;
            _fileSearchService.ProgressChanged += OnSearchProgressChanged;
            
            // カテゴリの初期化
            InitializeFileCategories();
            
            // 保存済みフィルタの読み込み
            _ = LoadSavedFiltersAsync();
            
            // 自動検索タイマーの初期化
            InitializeAutoSearchTimer();
        }

        partial void OnIsTxtSelectedChanged(bool value) => UpdateFileExtensions();
        partial void OnIsLogSelectedChanged(bool value) => UpdateFileExtensions();
        partial void OnIsCsSelectedChanged(bool value) => UpdateFileExtensions();
        partial void OnIsJsSelectedChanged(bool value) => UpdateFileExtensions();
        partial void OnIsPySelectedChanged(bool value) => UpdateFileExtensions();
        partial void OnIsXmlSelectedChanged(bool value) => UpdateFileExtensions();
        partial void OnIsJsonSelectedChanged(bool value) => UpdateFileExtensions();

        partial void OnTargetFolderChanged(string value) => TriggerAutoSearch();
        partial void OnFilenamePatternChanged(string value) => TriggerAutoSearch();
        partial void OnContentPatternChanged(string value) => TriggerAutoSearch();
        partial void OnFileExtensionsChanged(string value) => TriggerAutoSearch();
        partial void OnEnableAutoSearchChanged(bool value) => ToggleAutoSearch(value);
        partial void OnSelectedFileMatchChanged(FileMatch? value) => _ = LoadFilePreviewAsync(value);
        partial void OnSelectedFilterChanged(SearchFilter? value) => _ = ApplyFilterOnSelectionChangeAsync(value);
        partial void OnSelectedCategoryChanged(FileCategory value) => UpdateExtensionButtonVisibility();
        
        // ラジオボタン変更時の処理
        partial void OnIsDocumentCategorySelectedChanged(bool value) { if (value) UpdateSelectedCategory(FileCategory.Document); }
        partial void OnIsCodeCategorySelectedChanged(bool value) { if (value) UpdateSelectedCategory(FileCategory.Code); }
        partial void OnIsWebCategorySelectedChanged(bool value) { if (value) UpdateSelectedCategory(FileCategory.Web); }
        partial void OnIsAllCategorySelectedChanged(bool value) { if (value) UpdateSelectedCategory(FileCategory.All); }

        private void UpdateFileExtensions()
        {
            var extensions = new List<string>();
            
            if (IsTxtSelected) extensions.Add(".txt");
            if (IsLogSelected) extensions.Add(".log");
            if (IsCsSelected) extensions.Add(".cs");
            if (IsJsSelected) extensions.Add(".js");
            if (IsPySelected) extensions.Add(".py");
            if (IsXmlSelected) extensions.Add(".xml");
            if (IsJsonSelected) extensions.Add(".json");

            // 既存の手入力拡張子と統合
            var currentExtensions = FileExtensions
                .Split(new[] { ',', ';', ' ' }, StringSplitOptions.RemoveEmptyEntries)
                .Select(ext => ext.Trim())
                .Where(ext => !string.IsNullOrWhiteSpace(ext))
                .Where(ext => !extensions.Contains(ext, StringComparer.OrdinalIgnoreCase))
                .ToList();

            extensions.AddRange(currentExtensions);
            FileExtensions = string.Join(", ", extensions.Distinct());
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
        private void OpenFilterManager()
        {
            var dialog = new Views.FilterManagerDialog();
            var viewModel = new FilterManagerDialogViewModel(_filterService);
            dialog.DataContext = viewModel;
            dialog.Owner = Application.Current.MainWindow;
            dialog.ShowDialog();
            
            // フィルタ管理ダイアログが閉じられた後、保存フィルタを再読み込み
            _ = LoadSavedFiltersAsync();
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
                IncludeSubdirectories = IncludeSubdirectories,
                CaseInsensitive = CaseInsensitive,
                WholeWordOnly = WholeWordOnly
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
        /// メニューからフィルタを適用
        /// </summary>
        [RelayCommand]
        private async Task ApplyFilterAsync(SearchFilter filter)
        {
            if (filter != null && !string.IsNullOrEmpty(filter.Id))
            {
                ApplyFilter(filter);
                SelectedFilter = filter;
                try
                {
                    await _filterService.RecordFilterUsageAsync(filter.Id);
                }
                catch (Exception ex)
                {
                    System.Diagnostics.Debug.WriteLine($"フィルタ使用記録の保存に失敗: {ex.Message}");
                }
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
        /// フィルタ選択変更時の自動適用処理
        /// </summary>
        private async Task ApplyFilterOnSelectionChangeAsync(SearchFilter? filter)
        {
            if (_isApplyingFilter) return; // 重複実行を防ぐ
            
            if (filter != null && !string.IsNullOrEmpty(filter.Id))
            {
                _isApplyingFilter = true;
                try
                {
                    ApplyFilter(filter);
                    try
                    {
                        await _filterService.RecordFilterUsageAsync(filter.Id);
                    }
                    catch (Exception ex)
                    {
                        // 使用記録の失敗は致命的ではないため、エラーログのみ
                        System.Diagnostics.Debug.WriteLine($"フィルタ使用記録の保存に失敗: {ex.Message}");
                    }
                }
                finally
                {
                    _isApplyingFilter = false;
                }
            }
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

        #region カテゴリ機能

        /// <summary>
        /// ファイルカテゴリの初期化
        /// </summary>
        private void InitializeFileCategories()
        {
            FileCategories.Clear();
            
            FileCategories.Add(new FileCategoryInfo(FileCategory.Document, "ドキュメント", 
                new List<string> { ".txt", ".log" }, "テキストファイル・ログファイル"));
            
            FileCategories.Add(new FileCategoryInfo(FileCategory.Code, "プログラムコード", 
                new List<string> { ".cs", ".js", ".py" }, "C#、JavaScript、Pythonファイル"));
            
            FileCategories.Add(new FileCategoryInfo(FileCategory.Web, "Web・マークアップ", 
                new List<string> { ".xml", ".json" }, "XML、JSONファイル"));
            
            FileCategories.Add(new FileCategoryInfo(FileCategory.All, "すべて", 
                new List<string> { ".txt", ".log", ".cs", ".js", ".py", ".xml", ".json" }, "すべてのファイル形式"));

            // 初期表示の更新
            UpdateExtensionButtonVisibility();
        }

        /// <summary>
        /// 選択されたカテゴリに応じて拡張子ボタンの表示状態を更新
        /// </summary>
        private void UpdateExtensionButtonVisibility()
        {
            var selectedCategory = FileCategories.FirstOrDefault(c => c.Category == SelectedCategory);
            if (selectedCategory == null) return;

            var extensions = selectedCategory.Extensions;

            IsTxtVisible = extensions.Contains(".txt");
            IsLogVisible = extensions.Contains(".log");
            IsCsVisible = extensions.Contains(".cs");
            IsJsVisible = extensions.Contains(".js");
            IsPyVisible = extensions.Contains(".py");
            IsXmlVisible = extensions.Contains(".xml");
            IsJsonVisible = extensions.Contains(".json");

            // カテゴリ変更時に現在選択されている拡張子をリセット
            ResetExtensionSelections();
        }

        /// <summary>
        /// 拡張子選択をリセット
        /// </summary>
        private void ResetExtensionSelections()
        {
            IsTxtSelected = false;
            IsLogSelected = false;
            IsCsSelected = false;
            IsJsSelected = false;
            IsPySelected = false;
            IsXmlSelected = false;
            IsJsonSelected = false;
        }

        /// <summary>
        /// ラジオボタンからカテゴリを更新
        /// </summary>
        private void UpdateSelectedCategory(FileCategory category)
        {
            if (SelectedCategory != category)
            {
                SelectedCategory = category;
            }
        }

        #endregion

        #region 自動検索機能

        /// <summary>
        /// 自動検索タイマーの初期化
        /// </summary>
        private void InitializeAutoSearchTimer()
        {
            _autoSearchTimer = new Timer(AutoSearchCallback, null, Timeout.Infinite, Timeout.Infinite);
        }

        /// <summary>
        /// 自動検索のトリガー
        /// </summary>
        private void TriggerAutoSearch()
        {
            if (!EnableAutoSearch || IsSearching) return;

            _lastSearchTime = DateTime.Now;
            _autoSearchTimer?.Change(1000, Timeout.Infinite); // 1秒後に実行
        }

        /// <summary>
        /// 自動検索の有効/無効切り替え
        /// </summary>
        private void ToggleAutoSearch(bool enabled)
        {
            if (!enabled)
            {
                _autoSearchTimer?.Change(Timeout.Infinite, Timeout.Infinite);
            }
        }

        /// <summary>
        /// 自動検索コールバック
        /// </summary>
        private async void AutoSearchCallback(object? state)
        {
            // 最後の変更から1秒経過していない場合はスキップ
            if (DateTime.Now - _lastSearchTime < TimeSpan.FromSeconds(1))
                return;

            if (!EnableAutoSearch || IsSearching)
                return;

            try
            {
                // UIスレッドで検索を実行
                await System.Windows.Application.Current.Dispatcher.InvokeAsync(async () =>
                {
                    await StartSearchAsync();
                });
            }
            catch
            {
                // 自動検索のエラーは無視
            }
        }

        #endregion

        #region ファイルプレビュー機能

        /// <summary>
        /// ファイルプレビューを読み込む
        /// </summary>
        private async Task LoadFilePreviewAsync(FileMatch? fileMatch)
        {
            if (fileMatch == null)
            {
                CurrentFilePreview = null;
                PreviewStatusMessage = "ファイルを選択してください";
                return;
            }

            try
            {
                IsPreviewLoading = true;
                PreviewStatusMessage = "プレビューを読み込み中...";
                
                var settings = new PreviewSettings
                {
                    MaxPreviewSize = 1024 * 1024, // 1MB
                    MaxDisplayLines = 100,
                    ContextLines = 3,
                    TimeoutMs = 5000,
                    EnableEncodingDetection = true,
                    EnableBinaryDetection = true
                };

                using var cts = new CancellationTokenSource(TimeSpan.FromMilliseconds(settings.TimeoutMs));
                var preview = await _filePreviewService.GeneratePreviewAsync(fileMatch, settings, cts.Token);
                
                CurrentFilePreview = preview;
                
                if (preview.IsPreviewable)
                {
                    PreviewStatusMessage = $"行数: {preview.DisplayLines}/{preview.TotalLines}, エンコーディング: {preview.Encoding}";
                }
                else
                {
                    PreviewStatusMessage = preview.PreviewErrorMessage ?? "プレビューできません";
                }
            }
            catch (OperationCanceledException)
            {
                CurrentFilePreview = null;
                PreviewStatusMessage = "プレビューがタイムアウトしました";
            }
            catch (Exception ex)
            {
                CurrentFilePreview = null;
                PreviewStatusMessage = $"エラー: {ex.Message}";
            }
            finally
            {
                IsPreviewLoading = false;
            }
        }

        /// <summary>
        /// プレビューを更新する
        /// </summary>
        [RelayCommand]
        private async Task RefreshPreviewAsync()
        {
            if (SelectedFileMatch != null)
            {
                await LoadFilePreviewAsync(SelectedFileMatch);
            }
        }

        #endregion

        #region IDisposable

        /// <summary>
        /// リソースの解放
        /// </summary>
        protected virtual void Dispose(bool disposing)
        {
            if (disposing)
            {
                _autoSearchTimer?.Dispose();
                _searchCancellationTokenSource?.Dispose();
            }
        }

        public void Dispose()
        {
            Dispose(true);
            GC.SuppressFinalize(this);
        }

        #endregion
    }
}