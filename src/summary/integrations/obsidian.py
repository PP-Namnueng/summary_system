"""
Obsidian vault integration for saving summaries
"""
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional


class ObsidianIntegration:
    """Save summaries directly to Obsidian vault"""

    def __init__(self, vault_path: str, summary_folder: str = "Summaries"):
        """
        Initialize Obsidian integration
        
        Args:
            vault_path: Path to Obsidian vault root
            summary_folder: Folder name for summaries inside vault
        """
        self.vault_path = Path(vault_path)
        self.summary_folder = summary_folder
        self.output_path = self.vault_path / summary_folder
        
    def is_valid_vault(self) -> bool:
        """Check if the vault path is valid"""
        # Check if .obsidian folder exists (indicates an Obsidian vault)
        obsidian_folder = self.vault_path / ".obsidian"
        return self.vault_path.exists() and obsidian_folder.exists()

    def ensure_folder_exists(self) -> bool:
        """Create summary folder if it doesn't exist"""
        try:
            self.output_path.mkdir(parents=True, exist_ok=True)
            return True
        except Exception:
            return False

    def sanitize_filename(self, title: str) -> str:
        """Convert title to safe filename"""
        # Remove invalid characters
        safe_title = re.sub(r'[<>:"/\\|?*]', '', title)
        # Replace spaces and multiple dashes
        safe_title = re.sub(r'\s+', ' ', safe_title).strip()
        # Limit length to 50 chars for cleaner names
        if len(safe_title) > 50:
            safe_title = safe_title[:50].rsplit(' ', 1)[0]  # Cut at word boundary
        return safe_title or "Untitled"

    def generate_filename(self, title: str = None, source_type: str = None) -> str:
        """Generate filename from title (no timestamp for readability)"""
        if title:
            safe_title = self.sanitize_filename(title)
            base_filename = safe_title
        elif source_type:
            base_filename = f"{source_type}_summary"
        else:
            # Only use timestamp if no title available
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"summary_{timestamp}"
        
        # Check if file exists, add number if needed
        filename = f"{base_filename}.md"
        file_path = self.output_path / filename
        counter = 2
        
        while file_path.exists():
            filename = f"{base_filename}_{counter}.md"
            file_path = self.output_path / filename
            counter += 1
        
        return filename

    def create_frontmatter(
        self,
        title: str = None,
        source_url: str = None,
        source_type: str = None,
        language: str = None,
        tags: list[str] = None,
    ) -> str:
        """Generate YAML frontmatter for Obsidian"""
        now = datetime.now()
        
        frontmatter_lines = [
            "---",
            f"created: {now.strftime('%Y-%m-%d %H:%M')}",
            f"type: summary",
        ]
        
        if title:
            # Escape quotes in title
            safe_title = title.replace('"', '\\"')
            frontmatter_lines.append(f'title: "{safe_title}"')
        
        if source_type:
            frontmatter_lines.append(f"source_type: {source_type}")
        
        if source_url:
            frontmatter_lines.append(f"source_url: {source_url}")
        
        if language:
            frontmatter_lines.append(f"language: {language}")
        
        # Default tags
        all_tags = ["summary", "ai-generated"]
        if source_type:
            all_tags.append(source_type)
        if tags:
            all_tags.extend(tags)
        
        tags_str = ", ".join(all_tags)
        frontmatter_lines.append(f"tags: [{tags_str}]")
        
        frontmatter_lines.append("---")
        
        return "\n".join(frontmatter_lines)

    def save_summary(
        self,
        summary: str,
        title: str = None,
        source_url: str = None,
        source_type: str = None,
        language: str = "th",
        include_frontmatter: bool = True,
        custom_filename: str = None,
    ) -> dict:
        """
        Save summary to Obsidian vault
        
        Args:
            summary: The summary content (markdown)
            title: Title for the note
            source_url: Original source URL
            source_type: Type of source (youtube, webpage, pdf, text)
            language: Summary language
            include_frontmatter: Whether to add YAML frontmatter
            custom_filename: Custom filename (optional)
            
        Returns:
            dict with success status and file path
        """
        # Validate vault
        if not self.vault_path.exists():
            return {
                "success": False,
                "error": f"Vault path does not exist: {self.vault_path}",
            }
        
        # Ensure output folder exists
        if not self.ensure_folder_exists():
            return {
                "success": False,
                "error": f"Could not create folder: {self.output_path}",
            }
        
        # Generate filename
        if custom_filename:
            filename = custom_filename if custom_filename.endswith('.md') else f"{custom_filename}.md"
        else:
            filename = self.generate_filename(title, source_type)
        
        file_path = self.output_path / filename
        
        # Build content
        content_parts = []
        
        if include_frontmatter:
            frontmatter = self.create_frontmatter(
                title=title,
                source_url=source_url,
                source_type=source_type,
                language=language,
            )
            content_parts.append(frontmatter)
        
        # Add title as H1 if provided
        if title:
            content_parts.append(f"\n# {title}\n")
        
        # Add source link
        if source_url:
            content_parts.append(f"> 🔗 Source: {source_url}\n")
        
        # Add summary content
        content_parts.append(summary)
        
        # Add footer
        footer = f"\n\n---\n*Generated by Knowledge Summary System | {datetime.now().strftime('%Y-%m-%d %H:%M')}*"
        content_parts.append(footer)
        
        full_content = "\n".join(content_parts)
        
        # Write file
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(full_content)
            
            return {
                "success": True,
                "file_path": str(file_path),
                "filename": filename,
                "folder": str(self.output_path),
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to write file: {str(e)}",
            }

    def list_summaries(self, limit: int = 10) -> list[dict]:
        """List recent summaries in the vault"""
        if not self.output_path.exists():
            return []
        
        summaries = []
        md_files = sorted(
            self.output_path.glob("*.md"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        
        for file_path in md_files[:limit]:
            summaries.append({
                "filename": file_path.name,
                "path": str(file_path),
                "modified": datetime.fromtimestamp(file_path.stat().st_mtime),
            })
        
        return summaries


def find_obsidian_vaults() -> list[str]:
    """Try to find Obsidian vaults in common locations"""
    possible_locations = []
    
    # Common locations on Windows
    home = Path.home()
    common_paths = [
        home / "Documents" / "Obsidian",
        home / "Documents",
        home / "Obsidian",
        home / "OneDrive" / "Documents" / "Obsidian",
        home / "OneDrive" / "Obsidian",
        Path("D:/Obsidian"),
        Path("D:/Documents/Obsidian"),
    ]
    
    vaults = []
    for path in common_paths:
        if path.exists():
            # Check if this is a vault
            if (path / ".obsidian").exists():
                vaults.append(str(path))
            else:
                # Check subfolders
                for subfolder in path.iterdir():
                    if subfolder.is_dir() and (subfolder / ".obsidian").exists():
                        vaults.append(str(subfolder))
    
    return vaults
