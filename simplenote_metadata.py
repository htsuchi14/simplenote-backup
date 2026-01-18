"""
Simplenote Metadata Utilities
Handles ID comments embedded in markdown files for reliable sync.

Format: <!-- simplenote-id: 9f8a7c6b5e4d3c2b1a0f9e8d7c6b5a4f -->
"""
import re
from typing import Optional

# Pattern matches: <!-- simplenote-id: <32 hex chars> -->
ID_COMMENT_PATTERN = re.compile(r'^<!-- simplenote-id: ([0-9a-f]{32}) -->\n?', re.MULTILINE)


def extract_id_from_content(content: str) -> Optional[str]:
    """Extract Simplenote ID from content string.

    Args:
        content: File content as string

    Returns:
        Note ID (32 hex chars) if found, None otherwise
    """
    match = ID_COMMENT_PATTERN.match(content)
    if match:
        return match.group(1)
    return None


def extract_id_from_file(filepath: str) -> Optional[str]:
    """Extract Simplenote ID from a file.

    Args:
        filepath: Path to the markdown file

    Returns:
        Note ID (32 hex chars) if found, None otherwise
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return extract_id_from_content(content)
    except (IOError, OSError):
        return None


def write_id_to_file(filepath: str, note_id: str) -> bool:
    """Write or update Simplenote ID comment at the start of a file.

    If the file already has an ID comment, it will be replaced.

    Args:
        filepath: Path to the markdown file
        note_id: The 32-character hex note ID

    Returns:
        True if successful, False otherwise
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Remove existing ID comment if present
        content = get_content_without_id(content)

        # Add new ID comment at the start
        id_comment = f"<!-- simplenote-id: {note_id} -->\n"
        new_content = id_comment + content

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)

        return True
    except (IOError, OSError):
        return False


def get_content_without_id(content: str) -> str:
    """Remove the ID comment from content.

    Args:
        content: File content as string

    Returns:
        Content with ID comment removed
    """
    return ID_COMMENT_PATTERN.sub('', content, count=1)


def build_content_with_id(note_id: str, content: str) -> str:
    """Build file content with ID comment prepended.

    Args:
        note_id: The 32-character hex note ID
        content: The note content (without ID comment)

    Returns:
        Content with ID comment at the start
    """
    # Ensure content doesn't already have an ID
    clean_content = get_content_without_id(content)
    id_comment = f"<!-- simplenote-id: {note_id} -->\n"
    return id_comment + clean_content
