"""Utilities for formatting and escaping strings."""

import re
from typing import Optional

def escape_content(content: str) -> str:
    """Escape special characters in content string."""
    # Replace any existing quotes with escaped quotes
    content = content.replace('"', '\\"')
    # Wrap the content in quotes if it contains commas
    if ',' in content:
        content = f'"{content}"'
    return content

def unescape_content(content: str) -> str:
    """Unescape special characters in content string."""
    if content.startswith('"') and content.endswith('"'):
        content = content[1:-1]
    content = content.replace('\\"', '"')
    return content

def validate_uuid(uuid_str: Optional[str]) -> bool:
    """Validate UUID format."""
    if not uuid_str:
        return False
    uuid_pattern = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        re.IGNORECASE
    )
    return bool(uuid_pattern.match(uuid_str)) 