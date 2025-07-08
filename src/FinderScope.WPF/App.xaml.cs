using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using System.Windows;
using FinderScope.Core.Services;
using FinderScope.WPF.ViewModels;

namespace FinderScope.WPF
{
    public partial class App : Application
    {
        private IHost? _host;

        protected override void OnStartup(StartupEventArgs e)
        {
            // Dependency Injection の設定
            _host = Host.CreateDefaultBuilder()
                .ConfigureServices((context, services) =>
                {
                    // Core Services
                    services.AddSingleton<IFileSearchService, FileSearchService>();
                    services.AddSingleton<IExportService, ExportService>();
                    services.AddSingleton<IFilterService, FilterService>();
                    services.AddSingleton<IFileIndexService, FileIndexService>();
                    services.AddSingleton<ISearchHistoryService, SearchHistoryService>();
                    
                    // ViewModels
                    services.AddTransient<MainWindowViewModel>();
                })
                .Build();

            // メインウィンドウを作成
            var mainWindow = new Views.MainWindow();
            var viewModel = _host.Services.GetRequiredService<MainWindowViewModel>();
            mainWindow.DataContext = viewModel;
            
            MainWindow = mainWindow;
            mainWindow.Show();

            base.OnStartup(e);
        }

        protected override void OnExit(ExitEventArgs e)
        {
            _host?.Dispose();
            base.OnExit(e);
        }
    }
}