using System;
using System.Collections.Generic;
using NUnit.Framework;
using FluentAssertions;
using FinderScope.Core.Models;

namespace FinderScope.Tests.Models
{
    [TestFixture]
    public class SearchCriteriaTests
    {
        [Test]
        public void IsValid_WithValidTargetFolder_ReturnsTrue()
        {
            // Arrange
            var criteria = new SearchCriteria
            {
                TargetFolder = @"C:\Windows"
            };

            // Act & Assert
            criteria.IsValid().Should().BeTrue();
        }

        [Test]
        public void IsValid_WithEmptyTargetFolder_ReturnsFalse()
        {
            // Arrange
            var criteria = new SearchCriteria
            {
                TargetFolder = string.Empty
            };

            // Act & Assert
            criteria.IsValid().Should().BeFalse();
        }

        [Test]
        public void IsValid_WithNullTargetFolder_ReturnsFalse()
        {
            // Arrange
            var criteria = new SearchCriteria
            {
                TargetFolder = null!
            };

            // Act & Assert
            criteria.IsValid().Should().BeFalse();
        }

        [Test]
        public void GetSummary_WithAllParameters_ReturnsFormattedString()
        {
            // Arrange
            var criteria = new SearchCriteria
            {
                TargetFolder = @"C:\TestFolder",
                FilenamePattern = "*.txt",
                FileExtensions = new List<string> { ".txt", ".log" },
                DateFrom = new DateTime(2024, 1, 1),
                DateTo = new DateTime(2024, 12, 31),
                ContentPattern = "error",
                UseRegex = true,
                CaseSensitive = false,
                IncludeSubdirectories = true
            };

            // Act
            var summary = criteria.GetSummary();

            // Assert
            summary.Should().NotBeNullOrWhiteSpace();
            summary.Should().Contain("C:\\TestFolder");
            summary.Should().Contain("*.txt");
            summary.Should().Contain(".txt, .log");
            summary.Should().Contain("error");
        }

        [Test]
        public void GetSummary_WithMinimalParameters_ReturnsBasicString()
        {
            // Arrange
            var criteria = new SearchCriteria
            {
                TargetFolder = @"C:\TestFolder"
            };

            // Act
            var summary = criteria.GetSummary();

            // Assert
            summary.Should().NotBeNullOrWhiteSpace();
            summary.Should().Contain("C:\\TestFolder");
        }

        [Test]
        public void FileExtensions_DefaultValue_IsEmptyList()
        {
            // Arrange & Act
            var criteria = new SearchCriteria();

            // Assert
            criteria.FileExtensions.Should().NotBeNull();
            criteria.FileExtensions.Should().BeEmpty();
        }

        [Test]
        public void Properties_DefaultValues_AreCorrect()
        {
            // Arrange & Act
            var criteria = new SearchCriteria();

            // Assert
            criteria.TargetFolder.Should().Be(string.Empty);
            criteria.FilenamePattern.Should().BeNull();
            criteria.FileExtensions.Should().BeEmpty();
            criteria.DateFrom.Should().BeNull();
            criteria.DateTo.Should().BeNull();
            criteria.ContentPattern.Should().BeNull();
            criteria.UseRegex.Should().BeFalse();
            criteria.CaseSensitive.Should().BeFalse();
            criteria.IncludeSubdirectories.Should().BeTrue();
        }
    }
}