using FinderScope.Core.Utilities;
using FluentAssertions;
using NUnit.Framework;

namespace FinderScope.Tests.Utilities
{
    [TestFixture]
    public class WildcardMatcherTests
    {
        [Test]
        public void ConvertToRegex_WithAsterisk_ReturnsCorrectPattern()
        {
            // Arrange
            var wildcardPattern = "*.txt";

            // Act
            var regexPattern = WildcardMatcher.ConvertToRegex(wildcardPattern);

            // Assert
            regexPattern.Should().Be("^.*\\.txt$");
        }

        [Test]
        public void ConvertToRegex_WithQuestionMark_ReturnsCorrectPattern()
        {
            // Arrange
            var wildcardPattern = "test?.log";

            // Act
            var regexPattern = WildcardMatcher.ConvertToRegex(wildcardPattern);

            // Assert
            regexPattern.Should().Be("^test.\\.log$");
        }

        [Test]
        public void IsMatch_WithAsteriskPattern_ReturnsTrue()
        {
            // Arrange
            var fileName = "document.txt";
            var pattern = "*.txt";

            // Act
            var result = WildcardMatcher.IsMatch(fileName, pattern);

            // Assert
            result.Should().BeTrue();
        }

        [Test]
        public void IsMatch_WithQuestionMarkPattern_ReturnsTrue()
        {
            // Arrange
            var fileName = "test1.log";
            var pattern = "test?.log";

            // Act
            var result = WildcardMatcher.IsMatch(fileName, pattern);

            // Assert
            result.Should().BeTrue();
        }

        [Test]
        public void IsMatch_WithQuestionMarkPattern_ReturnsFalse()
        {
            // Arrange
            var fileName = "test12.log";
            var pattern = "test?.log";

            // Act
            var result = WildcardMatcher.IsMatch(fileName, pattern);

            // Assert
            result.Should().BeFalse();
        }

        [Test]
        public void IsMatch_CaseInsensitive_ReturnsTrue()
        {
            // Arrange
            var fileName = "DOCUMENT.TXT";
            var pattern = "*.txt";

            // Act
            var result = WildcardMatcher.IsMatch(fileName, pattern, caseSensitive: false);

            // Assert
            result.Should().BeTrue();
        }

        [Test]
        public void IsMatch_CaseSensitive_ReturnsFalse()
        {
            // Arrange
            var fileName = "DOCUMENT.TXT";
            var pattern = "*.txt";

            // Act
            var result = WildcardMatcher.IsMatch(fileName, pattern, caseSensitive: true);

            // Assert
            result.Should().BeFalse();
        }

        [Test]
        public void IsMatchAny_WithMultiplePatterns_ReturnsTrue()
        {
            // Arrange
            var fileName = "config.xml";
            var patterns = "*.txt;*.xml;*.json";

            // Act
            var result = WildcardMatcher.IsMatchAny(fileName, patterns);

            // Assert
            result.Should().BeTrue();
        }

        [Test]
        public void IsMatchAny_WithCommaSeparated_ReturnsTrue()
        {
            // Arrange
            var fileName = "data.json";
            var patterns = "*.txt,*.xml,*.json";

            // Act
            var result = WildcardMatcher.IsMatchAny(fileName, patterns);

            // Assert
            result.Should().BeTrue();
        }

        [Test]
        public void IsMatchAny_NoMatch_ReturnsFalse()
        {
            // Arrange
            var fileName = "image.png";
            var patterns = "*.txt;*.xml;*.json";

            // Act
            var result = WildcardMatcher.IsMatchAny(fileName, patterns);

            // Assert
            result.Should().BeFalse();
        }

        [Test]
        public void ContainsWildcards_WithAsterisk_ReturnsTrue()
        {
            // Arrange
            var pattern = "*.txt";

            // Act
            var result = WildcardMatcher.ContainsWildcards(pattern);

            // Assert
            result.Should().BeTrue();
        }

        [Test]
        public void ContainsWildcards_WithQuestionMark_ReturnsTrue()
        {
            // Arrange
            var pattern = "test?.log";

            // Act
            var result = WildcardMatcher.ContainsWildcards(pattern);

            // Assert
            result.Should().BeTrue();
        }

        [Test]
        public void ContainsWildcards_WithoutWildcards_ReturnsFalse()
        {
            // Arrange
            var pattern = "test.txt";

            // Act
            var result = WildcardMatcher.ContainsWildcards(pattern);

            // Assert
            result.Should().BeFalse();
        }

        [Test]
        public void IsValidPattern_WithValidPattern_ReturnsTrue()
        {
            // Arrange
            var pattern = "*.txt";

            // Act
            var result = WildcardMatcher.IsValidPattern(pattern);

            // Assert
            result.Should().BeTrue();
        }

        [Test]
        public void IsValidPattern_WithEmptyPattern_ReturnsFalse()
        {
            // Arrange
            var pattern = "";

            // Act
            var result = WildcardMatcher.IsValidPattern(pattern);

            // Assert
            result.Should().BeFalse();
        }

        [Test]
        public void IsMatch_ComplexPattern_ReturnsCorrectResult()
        {
            // Arrange & Act & Assert
            WildcardMatcher.IsMatch("backup_2023_01_15.txt", "backup_*_*.txt").Should().BeTrue();
            WildcardMatcher.IsMatch("log_error.txt", "log_*.txt").Should().BeTrue();
            WildcardMatcher.IsMatch("test123.log", "test???.log").Should().BeTrue();
            WildcardMatcher.IsMatch("test12.log", "test???.log").Should().BeFalse();
            WildcardMatcher.IsMatch("data.backup.old", "*.backup.*").Should().BeTrue();
        }
    }
}