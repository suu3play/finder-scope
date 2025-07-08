using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using System.Threading.Tasks;
using NUnit.Framework;
using FluentAssertions;
using FinderScope.Core.Models;
using FinderScope.Core.Services;

namespace FinderScope.Tests.Services
{
    [TestFixture]
    public class ExportServiceTests
    {
        private ExportService _exportService;
        private SearchResult _testSearchResult;
        private string _tempDirectory;

        [SetUp]
        public void SetUp()
        {
            _exportService = new ExportService();
            _tempDirectory = Path.Combine(Path.GetTempPath(), Path.GetRandomFileName());
            Directory.CreateDirectory(_tempDirectory);

            // テスト用の検索結果を作成
            _testSearchResult = new SearchResult
            {
                Criteria = new SearchCriteria
                {
                    TargetFolder = @"C:\TestFolder",
                    FilenamePattern = "*.txt",
                    ContentPattern = "error"
                },
                SearchStartTime = DateTime.Now,
                SearchDurationSeconds = 1.5,
                TotalFilesScanned = 100
            };

            // テストファイルマッチを追加
            var fileMatch1 = new FileMatch
            {
                FileName = "test1.txt",
                Directory = @"C:\TestFolder",
                FilePath = @"C:\TestFolder\test1.txt",
                FileSize = 1024,
                LastModified = DateTime.Now.AddDays(-1)
            };
            fileMatch1.AddContentMatch(new ContentMatch
            {
                LineNumber = 5,
                MatchedText = "error message",
                StartPosition = 10,
                EndPosition = 23
            });

            var fileMatch2 = new FileMatch
            {
                FileName = "test2.log",
                Directory = @"C:\TestFolder\logs",
                FilePath = @"C:\TestFolder\logs\test2.log",
                FileSize = 2048,
                LastModified = DateTime.Now.AddDays(-2)
            };

            _testSearchResult.AddMatch(fileMatch1);
            _testSearchResult.AddMatch(fileMatch2);
        }

        [TearDown]
        public void TearDown()
        {
            if (Directory.Exists(_tempDirectory))
            {
                Directory.Delete(_tempDirectory, true);
            }
        }

        [Test]
        public async Task ExportToCsvAsync_CreatesValidCsvFile()
        {
            // Arrange
            var csvPath = Path.Combine(_tempDirectory, "test.csv");

            // Act
            await _exportService.ExportToCsvAsync(_testSearchResult, csvPath);

            // Assert
            File.Exists(csvPath).Should().BeTrue();
            
            var csvContent = await File.ReadAllTextAsync(csvPath);
            csvContent.Should().NotBeNullOrWhiteSpace();
            csvContent.Should().Contain("ファイル名");
            csvContent.Should().Contain("test1.txt");
            csvContent.Should().Contain("test2.log");
        }

        [Test]
        public async Task ExportToJsonAsync_CreatesValidJsonFile()
        {
            // Arrange
            var jsonPath = Path.Combine(_tempDirectory, "test.json");

            // Act
            await _exportService.ExportToJsonAsync(_testSearchResult, jsonPath);

            // Assert
            File.Exists(jsonPath).Should().BeTrue();
            
            var jsonContent = await File.ReadAllTextAsync(jsonPath);
            var deserializedData = JsonSerializer.Deserialize<JsonElement>(jsonContent);
            
            deserializedData.TryGetProperty("SearchCriteria", out var searchCriteria).Should().BeTrue();
            deserializedData.TryGetProperty("SearchInfo", out var searchInfo).Should().BeTrue();
            deserializedData.TryGetProperty("Results", out var results).Should().BeTrue();
            
            results.GetArrayLength().Should().Be(2);
        }

        [Test]
        public async Task ExportToHtmlAsync_CreatesValidHtmlFile()
        {
            // Arrange
            var htmlPath = Path.Combine(_tempDirectory, "test.html");

            // Act
            await _exportService.ExportToHtmlAsync(_testSearchResult, htmlPath);

            // Assert
            File.Exists(htmlPath).Should().BeTrue();
            
            var htmlContent = await File.ReadAllTextAsync(htmlPath);
            htmlContent.Should().NotBeNullOrWhiteSpace();
            htmlContent.Should().Contain("<!DOCTYPE html>");
            htmlContent.Should().Contain("Finder Scope");
            htmlContent.Should().Contain("test1.txt");
            htmlContent.Should().Contain("test2.log");
            htmlContent.Should().Contain("検索条件");
            htmlContent.Should().Contain("検索結果統計");
        }

        [Test]
        public async Task ExportToCsvAsync_WithEmptyResults_CreatesHeaderOnlyFile()
        {
            // Arrange
            var emptyResult = new SearchResult
            {
                Criteria = new SearchCriteria { TargetFolder = @"C:\Empty" }
            };
            var csvPath = Path.Combine(_tempDirectory, "empty.csv");

            // Act
            await _exportService.ExportToCsvAsync(emptyResult, csvPath);

            // Assert
            File.Exists(csvPath).Should().BeTrue();
            
            var csvContent = await File.ReadAllTextAsync(csvPath);
            csvContent.Should().Contain("ファイル名");
            csvContent.Split('\n').Length.Should().Be(2); // Header + empty line
        }

        [Test]
        public async Task ExportToJsonAsync_WithEmptyResults_CreatesValidStructure()
        {
            // Arrange
            var emptyResult = new SearchResult
            {
                Criteria = new SearchCriteria { TargetFolder = @"C:\Empty" },
                SearchDurationSeconds = 0.1,
                TotalFilesScanned = 0
            };
            var jsonPath = Path.Combine(_tempDirectory, "empty.json");

            // Act
            await _exportService.ExportToJsonAsync(emptyResult, jsonPath);

            // Assert
            File.Exists(jsonPath).Should().BeTrue();
            
            var jsonContent = await File.ReadAllTextAsync(jsonPath);
            var deserializedData = JsonSerializer.Deserialize<JsonElement>(jsonContent);
            
            deserializedData.TryGetProperty("Results", out var results).Should().BeTrue();
            results.GetArrayLength().Should().Be(0);
        }

        [Test]
        public async Task ExportToTxtAsync_CreatesValidTxtFile()
        {
            // Arrange
            var txtPath = Path.Combine(_tempDirectory, "test.txt");

            // Act
            await _exportService.ExportToTxtAsync(_testSearchResult, txtPath);

            // Assert
            File.Exists(txtPath).Should().BeTrue();
            
            var txtContent = await File.ReadAllTextAsync(txtPath);
            txtContent.Should().NotBeNullOrWhiteSpace();
            txtContent.Should().Contain("=== Finder Scope 検索結果 ===");
            txtContent.Should().Contain("test1.txt");
            txtContent.Should().Contain("test2.log");
            txtContent.Should().Contain("検索結果統計");
            txtContent.Should().Contain("検索結果一覧");
        }

        [Test]
        public async Task ExportToTxtAsync_WithEmptyResults_CreatesValidFile()
        {
            // Arrange
            var emptyResult = new SearchResult
            {
                Criteria = new SearchCriteria { TargetFolder = @"C:\Empty" },
                SearchStartTime = DateTime.Now,
                SearchDurationSeconds = 0.1,
                TotalFilesScanned = 0
            };
            var txtPath = Path.Combine(_tempDirectory, "empty.txt");

            // Act
            await _exportService.ExportToTxtAsync(emptyResult, txtPath);

            // Assert
            File.Exists(txtPath).Should().BeTrue();
            
            var txtContent = await File.ReadAllTextAsync(txtPath);
            txtContent.Should().Contain("=== Finder Scope 検索結果 ===");
            txtContent.Should().Contain("マッチするファイルが見つかりませんでした。");
        }

        [Test]
        public void ExportToCsvAsync_WithInvalidPath_ThrowsException()
        {
            // Arrange
            var invalidPath = @"Z:\NonExistent\invalid.csv";

            // Act & Assert
            var act = async () => await _exportService.ExportToCsvAsync(_testSearchResult, invalidPath);
            act.Should().ThrowAsync<DirectoryNotFoundException>();
        }
    }
}