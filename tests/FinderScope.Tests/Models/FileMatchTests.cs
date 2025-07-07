using System;
using System.IO;
using System.Linq;
using NUnit.Framework;
using FluentAssertions;
using FinderScope.Core.Models;

namespace FinderScope.Tests.Models
{
    [TestFixture]
    public class FileMatchTests
    {
        [Test]
        public void FromFileInfo_WithValidFileInfo_CreatesCorrectFileMatch()
        {
            // Arrange
            var tempFile = Path.GetTempFileName();
            var fileInfo = new FileInfo(tempFile);
            
            try
            {
                // Act
                var fileMatch = FileMatch.FromFileInfo(fileInfo);

                // Assert
                fileMatch.FilePath.Should().Be(fileInfo.FullName);
                fileMatch.FileName.Should().Be(fileInfo.Name);
                fileMatch.Directory.Should().Be(fileInfo.DirectoryName);
                fileMatch.LastModified.Should().Be(fileInfo.LastWriteTime);
                fileMatch.FileSize.Should().Be(fileInfo.Length);
                fileMatch.FullPath.Should().Be(fileInfo.FullName);
            }
            finally
            {
                if (File.Exists(tempFile))
                    File.Delete(tempFile);
            }
        }

        [Test]
        public void FormattedSize_WithVariousSizes_ReturnsCorrectFormat()
        {
            // Test cases: (size in bytes, expected format)
            var testCases = new[]
            {
                (100L, "100 B"),
                (1024L, "1.0 KB"),
                (1536L, "1.5 KB"),
                (1048576L, "1.0 MB"),
                (1073741824L, "1.0 GB"),
                (0L, "0 B")
            };

            foreach (var (size, expected) in testCases)
            {
                // Arrange
                var fileMatch = new FileMatch { FileSize = size };

                // Act & Assert
                fileMatch.FormattedSize.Should().Be(expected, $"Size {size} should format as {expected}");
            }
        }

        [Test]
        public void FileExtension_WithDifferentPaths_ReturnsCorrectExtension()
        {
            var testCases = new[]
            {
                (@"C:\test.txt", ".txt"),
                (@"C:\folder\file.log", ".log"),
                (@"C:\noextension", ""),
                (@"C:\folder\file.", "."),
                (@"C:\folder\.hidden", ".hidden")
            };

            foreach (var (path, expectedExtension) in testCases)
            {
                // Arrange
                var fileMatch = new FileMatch { FilePath = path };

                // Act & Assert
                fileMatch.FileExtension.Should().Be(expectedExtension);
            }
        }

        [Test]
        public void AddContentMatch_AddsMatchToCollection()
        {
            // Arrange
            var fileMatch = new FileMatch();
            var contentMatch = new ContentMatch
            {
                LineNumber = 1,
                MatchedText = "test",
                StartPosition = 0,
                EndPosition = 4
            };

            // Act
            fileMatch.AddContentMatch(contentMatch);

            // Assert
            fileMatch.Matches.Should().HaveCount(1);
            fileMatch.Matches.First().Should().Be(contentMatch);
            fileMatch.MatchCount.Should().Be(1);
        }

        [Test]
        public void GetAllMatchedTexts_WithMultipleMatches_ReturnsDistinctTexts()
        {
            // Arrange
            var fileMatch = new FileMatch();
            fileMatch.AddContentMatch(new ContentMatch { MatchedText = "error" });
            fileMatch.AddContentMatch(new ContentMatch { MatchedText = "warning" });
            fileMatch.AddContentMatch(new ContentMatch { MatchedText = "error" }); // Duplicate

            // Act
            var texts = fileMatch.GetAllMatchedTexts().ToList();

            // Assert
            texts.Should().HaveCount(2);
            texts.Should().Contain("error");
            texts.Should().Contain("warning");
        }

        [Test]
        public void MatchCount_WithoutMatches_ReturnsZero()
        {
            // Arrange
            var fileMatch = new FileMatch();

            // Act & Assert
            fileMatch.MatchCount.Should().Be(0);
        }

        [Test]
        public void RelativePath_ReturnsFilePath()
        {
            // Arrange
            var filePath = @"C:\test\file.txt";
            var fileMatch = new FileMatch { FilePath = filePath };

            // Act & Assert
            fileMatch.RelativePath.Should().Be(filePath);
        }
    }
}