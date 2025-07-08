using System.Windows;
using FinderScope.WPF.ViewModels;

namespace FinderScope.WPF.Views
{
    /// <summary>
    /// SaveFilterDialog.xaml の相互作用ロジック
    /// </summary>
    public partial class SaveFilterDialog : Window
    {
        public SaveFilterDialog()
        {
            InitializeComponent();
            Loaded += OnLoaded;
        }

        private void OnLoaded(object sender, RoutedEventArgs e)
        {
            if (DataContext is SaveFilterDialogViewModel viewModel)
            {
                // ViewModelのプロパティ変更を監視してダイアログを閉じる
                viewModel.PropertyChanged += (s, args) =>
                {
                    if (args.PropertyName == nameof(SaveFilterDialogViewModel.DialogResult))
                    {
                        DialogResult = viewModel.DialogResult;
                        Close();
                    }
                };
            }
        }
    }
}