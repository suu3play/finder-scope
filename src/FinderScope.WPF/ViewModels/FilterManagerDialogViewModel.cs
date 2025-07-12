using System;
using System.Collections.ObjectModel;
using System.Linq;
using System.Windows.Input;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using FinderScope.Core.Models;
using FinderScope.Core.Services;

namespace FinderScope.WPF.ViewModels
{
    /// <summary>
    /// フィルタ管理ダイアログのViewModel
    /// </summary>
    public partial class FilterManagerDialogViewModel : ObservableObject
    {
        private readonly IFilterService _filterService;

        [ObservableProperty]
        private ObservableCollection<SearchFilter> _savedFilters = new();

        [ObservableProperty]
        private SearchFilter? _selectedFilter;

        [ObservableProperty]
        private SearchFilter _editingFilter = new();

        public FilterManagerDialogViewModel(IFilterService filterService)
        {
            _filterService = filterService;
            LoadFilters();
        }

        partial void OnSelectedFilterChanged(SearchFilter? value)
        {
            if (value != null)
            {
                // 選択されたフィルタの内容を編集用にコピー
                EditingFilter = new SearchFilter
                {
                    Id = value.Id,
                    Name = value.Name,
                    TargetFolder = value.TargetFolder,
                    FilenamePattern = value.FilenamePattern,
                    FileExtensions = value.FileExtensions,
                    DateFrom = value.DateFrom,
                    DateTo = value.DateTo,
                    ContentPattern = value.ContentPattern,
                    UseRegex = value.UseRegex,
                    CaseSensitive = value.CaseSensitive,
                    IncludeSubdirectories = value.IncludeSubdirectories,
                    EnableAutoSearch = value.EnableAutoSearch,
                    WholeWordOnly = value.WholeWordOnly,
                    IsDefault = value.IsDefault
                };
            }
        }

        [RelayCommand]
        private async void LoadFilters()
        {
            try
            {
                var filters = await _filterService.GetFiltersAsync();
                SavedFilters.Clear();
                foreach (var filter in filters)
                {
                    SavedFilters.Add(filter);
                }
            }
            catch (Exception ex)
            {
                // エラーハンドリング
                System.Windows.MessageBox.Show($"フィルタの読み込みに失敗しました: {ex.Message}", 
                    "エラー", System.Windows.MessageBoxButton.OK, System.Windows.MessageBoxImage.Error);
            }
        }

        [RelayCommand]
        private async void DeleteFilter()
        {
            if (SelectedFilter == null) return;

            var result = System.Windows.MessageBox.Show(
                $"フィルタ '{SelectedFilter.Name}' を削除しますか？",
                "削除確認",
                System.Windows.MessageBoxButton.YesNo,
                System.Windows.MessageBoxImage.Question);

            if (result == System.Windows.MessageBoxResult.Yes)
            {
                try
                {
                    await _filterService.DeleteFilterAsync(SelectedFilter.Id);
                    SavedFilters.Remove(SelectedFilter);
                    SelectedFilter = null;
                    EditingFilter = new SearchFilter();
                }
                catch (Exception ex)
                {
                    System.Windows.MessageBox.Show($"フィルタの削除に失敗しました: {ex.Message}", 
                        "エラー", System.Windows.MessageBoxButton.OK, System.Windows.MessageBoxImage.Error);
                }
            }
        }

        [RelayCommand]
        private void DuplicateFilter()
        {
            if (SelectedFilter == null) return;

            var duplicatedFilter = new SearchFilter
            {
                Name = $"{SelectedFilter.Name}_コピー",
                TargetFolder = SelectedFilter.TargetFolder,
                FilenamePattern = SelectedFilter.FilenamePattern,
                FileExtensions = SelectedFilter.FileExtensions,
                DateFrom = SelectedFilter.DateFrom,
                DateTo = SelectedFilter.DateTo,
                ContentPattern = SelectedFilter.ContentPattern,
                UseRegex = SelectedFilter.UseRegex,
                CaseSensitive = SelectedFilter.CaseSensitive,
                IncludeSubdirectories = SelectedFilter.IncludeSubdirectories,
                EnableAutoSearch = SelectedFilter.EnableAutoSearch,
                WholeWordOnly = SelectedFilter.WholeWordOnly,
                IsDefault = false
            };

            EditingFilter = duplicatedFilter;
        }

        [RelayCommand]
        private async void SetAsDefault()
        {
            if (SelectedFilter == null) return;

            try
            {
                await _filterService.SetDefaultFilterAsync(SelectedFilter.Id);
                
                // 他のフィルタのデフォルトを解除
                foreach (var filter in SavedFilters)
                {
                    filter.IsDefault = filter.Id == SelectedFilter.Id;
                }
                
                EditingFilter.IsDefault = true;
            }
            catch (Exception ex)
            {
                System.Windows.MessageBox.Show($"デフォルト設定に失敗しました: {ex.Message}", 
                    "エラー", System.Windows.MessageBoxButton.OK, System.Windows.MessageBoxImage.Error);
            }
        }

        [RelayCommand]
        private async void SaveChanges()
        {
            if (string.IsNullOrWhiteSpace(EditingFilter.Name))
            {
                System.Windows.MessageBox.Show("フィルタ名を入力してください。", 
                    "入力エラー", System.Windows.MessageBoxButton.OK, System.Windows.MessageBoxImage.Warning);
                return;
            }

            try
            {
                if (string.IsNullOrEmpty(EditingFilter.Id))
                {
                    // 新規作成
                    EditingFilter.Id = Guid.NewGuid().ToString();
                    await _filterService.SaveFilterAsync(EditingFilter);
                    SavedFilters.Add(EditingFilter);
                }
                else
                {
                    // 既存の更新
                    await _filterService.SaveFilterAsync(EditingFilter);
                    var existingFilter = SavedFilters.FirstOrDefault(f => f.Id == EditingFilter.Id);
                    if (existingFilter != null)
                    {
                        var index = SavedFilters.IndexOf(existingFilter);
                        SavedFilters[index] = EditingFilter;
                        SelectedFilter = EditingFilter;
                    }
                }

                System.Windows.MessageBox.Show("フィルタを保存しました。", 
                    "保存完了", System.Windows.MessageBoxButton.OK, System.Windows.MessageBoxImage.Information);
            }
            catch (Exception ex)
            {
                System.Windows.MessageBox.Show($"フィルタの保存に失敗しました: {ex.Message}", 
                    "エラー", System.Windows.MessageBoxButton.OK, System.Windows.MessageBoxImage.Error);
            }
        }
    }
}