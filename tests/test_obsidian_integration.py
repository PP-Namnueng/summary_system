"""
Test Obsidian Integration functionality
"""

import sys
import os
import unittest
from unittest.mock import MagicMock, patch, mock_open
import json
from pathlib import Path

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from integrations.obsidian import save_to_obsidian, find_obsidian_vaults


class TestObsidianIntegration(unittest.TestCase):
    """Test cases for Obsidian integration"""

    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.exists")
    def test_save_to_obsidian_success(self, mock_exists, mock_mkdir, mock_file):
        """Test successful save to Obsidian"""
        mock_exists.return_value = True

        result = save_to_obsidian(
            vault_path="C:/Users/Test/Obsidian",
            folder_name="Summaries",
            filename="test_summary",
            content="# Test Summary\n\nThis is test content",
            metadata={"source": "https://example.com", "date": "2024-01-01"},
        )

        self.assertTrue(result["success"])

    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.exists")
    def test_save_with_metadata(self, mock_exists, mock_mkdir, mock_file):
        """Test saving with metadata"""
        mock_exists.return_value = True

        result = save_to_obsidian(
            vault_path="C:/Users/Test/Obsidian",
            folder_name="Summaries",
            filename="test_with_metadata",
            content="Content here",
            metadata={
                "source": "https://youtube.com/watch?v=123",
                "author": "Test Author",
                "date": "2024-01-01",
                "tags": ["AI", "Summary"],
            },
        )

        self.assertTrue(result["success"])

    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.exists")
    def test_save_thai_content(self, mock_exists, mock_mkdir, mock_file):
        """Test saving Thai content"""
        mock_exists.return_value = True

        result = save_to_obsidian(
            vault_path="C:/Users/Test/Obsidian",
            folder_name="Summaries",
            filename="thai_summary",
            content="# สรุปเนื้อหา\n\nนี่คือเนื้อหาภาษาไทย",
        )

        self.assertTrue(result["success"])

    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.exists")
    def test_save_creates_folder(self, mock_exists, mock_mkdir, mock_file):
        """Test that save creates folder if it doesn't exist"""
        # First call to exists returns False (folder doesn't exist)
        # Second call returns True (after mkdir)
        mock_exists.side_effect = [False, True]

        result = save_to_obsidian(
            vault_path="C:/Users/Test/Obsidian",
            folder_name="Summaries",
            filename="test_summary",
            content="Content",
        )

        self.assertTrue(result["success"])
        mock_mkdir.assert_called()


class TestFindObsidianVaults(unittest.TestCase):
    """Test finding Obsidian vaults"""

    @patch("pathlib.Path.is_dir")
    @patch("pathlib.Path.exists")
    @patch("glob.glob")
    def test_find_vaults_default_location(self, mock_glob, mock_exists, mock_is_dir):
        """Test finding vaults in default location"""
        mock_glob.return_value = ["C:/Users/Test/Documents/Obsidian/Vault1"]
        mock_exists.return_value = True
        mock_is_dir.return_value = True

        vaults = find_obsidian_vaults()

        self.assertIsInstance(vaults, list)

    @patch("pathlib.Path.is_dir")
    @patch("pathlib.Path.exists")
    @patch("glob.glob")
    def test_find_multiple_vaults(self, mock_glob, mock_exists, mock_is_dir):
        """Test finding multiple vaults"""
        mock_glob.return_value = [
            "C:/Users/Test/Documents/Obsidian/Vault1",
            "C:/Users/Test/Documents/Obsidian/Vault2",
        ]
        mock_exists.return_value = True
        mock_is_dir.return_value = True

        vaults = find_obsidian_vaults()

        self.assertEqual(len(vaults), 2)

    @patch("glob.glob")
    def test_find_vaults_none_found(self, mock_glob):
        """Test when no vaults are found"""
        mock_glob.return_value = []

        vaults = find_obsidian_vaults()

        self.assertEqual(len(vaults), 0)


class TestObsidianErrorHandling(unittest.TestCase):
    """Test error handling in Obsidian integration"""

    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.exists")
    def test_save_invalid_vault_path(self, mock_exists, mock_mkdir, mock_file):
        """Test saving with invalid vault path"""
        mock_exists.return_value = False

        result = save_to_obsidian(
            vault_path="/invalid/path",
            folder_name="Summaries",
            filename="test",
            content="Content",
        )

        self.assertFalse(result["success"])

    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.exists")
    def test_save_permission_error(self, mock_exists, mock_mkdir, mock_file):
        """Test handling of permission errors"""
        mock_exists.return_value = True
        mock_file.side_effect = PermissionError("Access denied")

        result = save_to_obsidian(
            vault_path="C:/Users/Test/Obsidian",
            folder_name="Summaries",
            filename="test",
            content="Content",
        )

        self.assertFalse(result["success"])

    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.exists")
    def test_save_empty_content(self, mock_exists, mock_mkdir, mock_file):
        """Test saving empty content"""
        mock_exists.return_value = True

        result = save_to_obsidian(
            vault_path="C:/Obsidian",
            folder_name="Summaries",
            filename="empty",
            content="",
        )

        # Should handle empty content gracefully
        self.assertIn("success", result)


class TestObsidianFormatting(unittest.TestCase):
    """Test Obsidian note formatting"""

    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.exists")
    def test_markdown_formatting(self, mock_exists, mock_mkdir, mock_file):
        """Test Markdown formatting in saved file"""
        mock_exists.return_value = True

        markdown_content = """# Main Heading

## Subheading

- Bullet point 1
- Bullet point 2

**Bold text** and *italic text*
"""

        result = save_to_obsidian(
            vault_path="C:/Obsidian",
            folder_name="Summaries",
            filename="markdown_test",
            content=markdown_content,
        )

        self.assertTrue(result["success"])

    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.exists")
    def test_frontmatter_formatting(self, mock_exists, mock_mkdir, mock_file):
        """Test frontmatter formatting in saved file"""
        mock_exists.return_value = True

        result = save_to_obsidian(
            vault_path="C:/Obsidian",
            folder_name="Summaries",
            filename="frontmatter_test",
            content="# Summary",
            metadata={
                "title": "Test Title",
                "tags": ["tag1", "tag2"],
                "created": "2024-01-01",
            },
        )

        self.assertTrue(result["success"])


if __name__ == "__main__":
    unittest.main()
