using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using FinderScope.Core.Models;
using FinderScope.Core.Services;

namespace FinderScope.WPF.ViewModels
{
    /// <summary>
    /// フィルタ保存ダイアログのViewModel
    /// </summary>
    public partial class SaveFilterDialogViewModel : ObservableObject
    {
        private readonly IFilterService _filterService;

        [ObservableProperty]
        private string _filterName = string.Empty;

        [ObservableProperty]
        private string _description = string.Empty;

        [ObservableProperty]
        private bool _setAsDefault = false;

        [ObservableProperty]
        private bool _isNameValid = false;

        [ObservableProperty]
        private string _nameValidationMessage = string.Empty;

        [ObservableProperty]
        private bool _isValidating = false;

        public SearchCriteria? SearchCriteria { get; set; }
        
        [ObservableProperty]
        private bool _dialogResult = false;

        public SaveFilterDialogViewModel(IFilterService filterService)
        {
            _filterService = filterService;
        }

        [RelayCommand]
        private async Task ValidateFilterNameAsync()
        {
            if (string.IsNullOrWhiteSpace(FilterName))
            {
                IsNameValid = false;
                NameValidationMessage = "フィルタ名を入力してください。";
                return;
            }

            if (FilterName.Length > 100)
            {
                IsNameValid = false;
                NameValidationMessage = "フィルタ名は100文字以内で入力してください。";
                return;
            }

            IsValidating = true;
            try
            {
                var nameExists = await _filterService.IsFilterNameExistsAsync(FilterName);
                if (nameExists)
                {
                    IsNameValid = false;
                    NameValidationMessage = "このフィルタ名は既に使用されています。";
                }
                else
                {
                    IsNameValid = true;
                    NameValidationMessage = string.Empty;
                }
            }
            catch (Exception ex)
            {
                IsNameValid = false;
                NameValidationMessage = $"検証エラー: {ex.Message}";
            }
            finally
            {
                IsValidating = false;
            }
        }

        [RelayCommand]
        private async Task SaveFilterAsync()
        {
            if (SearchCriteria == null || !IsNameValid)
                return;

            try
            {
                var filter = new SearchFilter
                {
                    Name = FilterName.Trim(),
                    Description = string.IsNullOrWhiteSpace(Description) ? null : Description.Trim(),
                    Criteria = SearchCriteria,
                    IsDefault = SetAsDefault
                };

                await _filterService.SaveFilterAsync(filter);

                DialogResult = true;
            }
            catch (Exception ex)
            {
                NameValidationMessage = $"保存エラー: {ex.Message}";
                IsNameValid = false;
            }
        }

        [RelayCommand]
        private void Cancel()
        {
            DialogResult = false;
        }

        partial void OnFilterNameChanged(string value)
        {
            // 名前が変更されたら即座に検証
            _ = ValidateFilterNameAsync();
        }

        /// <summary>
        /// フィルタ名から推奨名を生成
        /// </summary>
        public void GenerateSuggestedName()
        {
            if (SearchCriteria == null) return;

            var suggestions = new List<string>();

            if (!string.IsNullOrWhiteSpace(SearchCriteria.TargetFolder))
            {
                var folderName = System.IO.Path.GetFileName(SearchCriteria.TargetFolder);
                if (!string.IsNullOrWhiteSpace(folderName))
                    suggestions.Add(folderName);
            }

            if (!string.IsNullOrWhiteSpace(SearchCriteria.FilenamePattern))
                suggestions.Add(SearchCriteria.FilenamePattern);

            if (SearchCriteria.FileExtensions.Any())
                suggestions.Add(string.Join(",", SearchCriteria.FileExtensions));

            if (!string.IsNullOrWhiteSpace(SearchCriteria.ContentPattern))
                suggestions.Add($"「{SearchCriteria.ContentPattern}」");

            if (suggestions.Any())
            {
                FilterName = string.Join(" - ", suggestions.Take(2));
            }
            else
            {
                FilterName = $"フィルタ {DateTime.Now:MM/dd HH:mm}";
            }
        }
    }
}