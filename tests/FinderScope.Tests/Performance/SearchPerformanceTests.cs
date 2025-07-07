using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Threading.Tasks;
using NUnit.Framework;
using FluentAssertions;
using FinderScope.Core.Models;
using FinderScope.Core.Services;

namespace FinderScope.Tests.Performance
{
    [TestFixture]
    [Category("Performance")]
    public class SearchPerformanceTests
    {
        private FileSearchService _searchService;
        private string _testDirectory;
        private const int TEST_FILE_COUNT = 1000;
        private const int PERFORMANCE_THRESHOLD_MS = 5000; // 5秒以内

        [OneTimeSetUp]
        public void OneTimeSetUp()
        {
            _searchService = new FileSearchService();
            _testDirectory = Path.Combine(Path.GetTempPath(), "FinderScopePerformanceTest");
            
            // テスト用ディレクトリ構造を作成
            CreateTestFileStructure();
        }

        [OneTimeTearDown]
        public void OneTimeTearDown()
        {
            if (Directory.Exists(_testDirectory))
            {
                Directory.Delete(_testDirectory, true);
            }
        }

        [Test]
        public async Task SearchAsync_LargeFileSet_CompletesWithinTimeLimit()
        {
            // Arrange
            var criteria = new SearchCriteria
            {
                TargetFolder = _testDirectory,
                FilenamePattern = "*.txt",
                IncludeSubdirectories = true
            };

            var stopwatch = Stopwatch.StartNew();

            // Act
            var result = await _searchService.SearchAsync(criteria);

            // Assert
            stopwatch.Stop();
            
            stopwatch.ElapsedMilliseconds.Should().BeLessThan(PERFORMANCE_THRESHOLD_MS, 
                $"Search should complete within {PERFORMANCE_THRESHOLD_MS}ms for {TEST_FILE_COUNT} files");
            
            result.FileMatches.Should().NotBeEmpty();
            result.TotalFilesScanned.Should().BeGreaterThan(0);
        }

        [Test]
        public async Task SearchAsync_ContentSearch_PerformanceAcceptable()
        {
            // Arrange
            var criteria = new SearchCriteria
            {
                TargetFolder = _testDirectory,
                ContentPattern = "test content",
                IncludeSubdirectories = true
            };

            var stopwatch = Stopwatch.StartNew();

            // Act
            var result = await _searchService.SearchAsync(criteria);

            // Assert
            stopwatch.Stop();
            
            // コンテンツ検索は時間がかかるので、少し余裕を持たせる
            stopwatch.ElapsedMilliseconds.Should().BeLessThan(PERFORMANCE_THRESHOLD_MS * 2, 
                "Content search should complete within reasonable time");
            
            result.Should().NotBeNull();
        }

        [Test]
        public async Task SearchAsync_RegexSearch_PerformanceAcceptable()
        {
            // Arrange
            var criteria = new SearchCriteria
            {
                TargetFolder = _testDirectory,
                FilenamePattern = @"test_\d+\.txt",
                UseRegex = true,
                IncludeSubdirectories = true
            };

            var stopwatch = Stopwatch.StartNew();

            // Act
            var result = await _searchService.SearchAsync(criteria);

            // Assert
            stopwatch.Stop();
            
            stopwatch.ElapsedMilliseconds.Should().BeLessThan(PERFORMANCE_THRESHOLD_MS, 
                "Regex search should complete within acceptable time");
            
            result.FileMatches.Should().NotBeEmpty();
        }

        [Test]
        public void SearchAsync_MemoryUsage_RemainsReasonable()
        {
            // Arrange
            var initialMemory = GC.GetTotalMemory(true);
            var criteria = new SearchCriteria
            {
                TargetFolder = _testDirectory,
                IncludeSubdirectories = true
            };

            // Act
            var result = _searchService.Search(criteria);

            // Assert
            var finalMemory = GC.GetTotalMemory(false);
            var memoryIncrease = finalMemory - initialMemory;
            
            // メモリ増加が100MB以下であることを確認
            memoryIncrease.Should().BeLessThan(100 * 1024 * 1024, 
                "Memory usage should not increase dramatically during search");
            
            result.Should().NotBeNull();
        }

        [Test]
        public async Task SearchAsync_ConcurrentSearches_HandleCorrectly()
        {
            // Arrange
            var criteria = new SearchCriteria
            {
                TargetFolder = _testDirectory,
                FilenamePattern = "*.txt"
            };

            var tasks = new List<Task<SearchResult>>();
            var stopwatch = Stopwatch.StartNew();

            // Act - 複数の検索を並行実行
            for (int i = 0; i < 5; i++)
            {
                tasks.Add(_searchService.SearchAsync(criteria));
            }

            var results = await Task.WhenAll(tasks);

            // Assert
            stopwatch.Stop();
            
            stopwatch.ElapsedMilliseconds.Should().BeLessThan(PERFORMANCE_THRESHOLD_MS * 2, 
                "Concurrent searches should not take significantly longer");
            
            results.Should().HaveCount(5);
            foreach (var result in results)
            {
                result.Should().NotBeNull();
                result.IsSuccess.Should().BeTrue();
            }
        }

        private void CreateTestFileStructure()
        {
            if (Directory.Exists(_testDirectory))
            {
                Directory.Delete(_testDirectory, true);
            }
            
            Directory.CreateDirectory(_testDirectory);

            // メインディレクトリにファイルを作成
            for (int i = 0; i < TEST_FILE_COUNT / 2; i++)
            {
                var fileName = Path.Combine(_testDirectory, $"test_{i:D4}.txt");
                File.WriteAllText(fileName, $"This is test content for file {i}\nSome sample text here.");
            }

            // サブディレクトリを作成
            var subDir1 = Path.Combine(_testDirectory, "SubDir1");
            var subDir2 = Path.Combine(_testDirectory, "SubDir2");
            Directory.CreateDirectory(subDir1);
            Directory.CreateDirectory(subDir2);

            // サブディレクトリにファイルを作成
            for (int i = 0; i < TEST_FILE_COUNT / 4; i++)
            {
                var fileName1 = Path.Combine(subDir1, $"sub1_file_{i:D4}.txt");
                var fileName2 = Path.Combine(subDir2, $"sub2_file_{i:D4}.log");
                
                File.WriteAllText(fileName1, $"SubDir1 content {i}\ntest content");
                File.WriteAllText(fileName2, $"SubDir2 log entry {i}\nerror message");
            }

            // 別の拡張子のファイルも作成
            for (int i = 0; i < TEST_FILE_COUNT / 4; i++)
            {
                var fileName = Path.Combine(_testDirectory, $"document_{i:D4}.doc");
                File.WriteAllText(fileName, $"Document content {i}");
            }
        }
    }
}