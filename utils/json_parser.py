import json
import logging
import re
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def safe_json_parse(text: str) -> Optional[Dict[str, Any]]:
    """
    Safely parse JSON from text, handling common LLM response issues
    
    Args:
        text: Raw text that should contain JSON
        
    Returns:
        Parsed JSON dictionary or None if parsing failed
    """
    if not text:
        return None
    
    try:
        # First, try direct JSON parsing
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Try to extract JSON from text that might contain other content
    cleaned_text = extract_json_from_text(text)
    if cleaned_text:
        try:
            return json.loads(cleaned_text)
        except json.JSONDecodeError:
            pass
    
    # Try to fix common JSON issues
    fixed_text = fix_common_json_issues(text)
    if fixed_text:
        try:
            return json.loads(fixed_text)
        except json.JSONDecodeError:
            pass
    
    logger.warning(f"Failed to parse JSON from text: {text[:200]}...")
    return None

def extract_json_from_text(text: str) -> Optional[str]:
    """
    Extract JSON from text that might contain other content
    
    Args:
        text: Raw text containing JSON
        
    Returns:
        Extracted JSON string or None
    """
    # Remove HTML tags if present
    text = remove_html_tags(text)
    
    # Look for JSON-like patterns
    json_patterns = [
        r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',  # Simple nested JSON
        r'\{.*?\}',  # Basic JSON pattern
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            if is_likely_json(match):
                return match.strip()
    
    # Try to find JSON between code blocks
    code_block_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
    match = re.search(code_block_pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    return None

def remove_html_tags(text: str) -> str:
    """
    Remove HTML tags from text
    
    Args:
        text: Text that may contain HTML tags
        
    Returns:
        Text with HTML tags removed
    """
    # Remove HTML tags
    html_pattern = r'<[^>]+>'
    cleaned = re.sub(html_pattern, '', text)
    
    # Remove common HTML entities
    html_entities = {
        '&amp;': '&',
        '&lt;': '<',
        '&gt;': '>',
        '&quot;': '"',
        '&apos;': "'",
        '&nbsp;': ' ',
    }
    
    for entity, replacement in html_entities.items():
        cleaned = cleaned.replace(entity, replacement)
    
    return cleaned

def fix_common_json_issues(text: str) -> Optional[str]:
    """
    Fix common JSON formatting issues from LLM responses
    
    Args:
        text: Potentially malformed JSON text
        
    Returns:
        Fixed JSON string or None
    """
    if not text:
        return None
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    # Remove common prefixes/suffixes
    prefixes_to_remove = [
        'json', 'JSON', '```json', '```', 'Here is the JSON:',
        'The JSON response is:', 'Response:', 'Result:'
    ]
    
    for prefix in prefixes_to_remove:
        if text.startswith(prefix):
            text = text[len(prefix):].strip()
    
    # Remove common suffixes
    suffixes_to_remove = ['```', '```json']
    for suffix in suffixes_to_remove:
        if text.endswith(suffix):
            text = text[:-len(suffix)].strip()
    
    # Fix common formatting issues
    fixes = [
        # Fix single quotes to double quotes
        (r"'([^']*)':", r'"\1":'),
        # Fix unquoted keys
        (r'(\w+):', r'"\1":'),
        # Fix trailing commas
        (r',\s*}', '}'),
        (r',\s*]', ']'),
        # Fix multiple spaces
        (r'\s+', ' '),
    ]
    
    for pattern, replacement in fixes:
        text = re.sub(pattern, replacement, text)
    
    return text if is_likely_json(text) else None

def is_likely_json(text: str) -> bool:
    """
    Check if text looks like JSON
    
    Args:
        text: Text to check
        
    Returns:
        True if text looks like JSON
    """
    if not text:
        return False
    
    text = text.strip()
    
    # Must start and end with braces or brackets
    if not ((text.startswith('{') and text.endswith('}')) or
            (text.startswith('[') and text.endswith(']'))):
        return False
    
    # Should contain common JSON patterns
    json_indicators = [
        '":', '":',  # Key-value separators
        '},{', '},', # Object separators
        '[]', '{}',  # Empty containers
    ]
    
    has_json_patterns = any(indicator in text for indicator in json_indicators)
    
    return has_json_patterns

def extract_structured_data(text: str, schema_keys: list) -> Dict[str, Any]:
    """
    Extract structured data from text even if not valid JSON
    
    Args:
        text: Text containing structured data
        schema_keys: List of expected keys to extract
        
    Returns:
        Dictionary with extracted data
    """
    result = {}
    
    # Try JSON parsing first
    parsed_json = safe_json_parse(text)
    if parsed_json:
        for key in schema_keys:
            if key in parsed_json:
                result[key] = parsed_json[key]
        return result
    
    # Fallback to regex extraction
    for key in schema_keys:
        patterns = [
            rf'"{key}"\s*:\s*"([^"]*)"',  # String values
            rf'"{key}"\s*:\s*([^,}}\]]+)',  # Other values
            rf'{key}\s*:\s*"([^"]*)"',     # Unquoted keys
            rf'{key}\s*:\s*([^,}}\]]+)',   # Unquoted keys, other values
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                # Try to convert to appropriate type
                if value.lower() in ['true', 'false']:
                    result[key] = value.lower() == 'true'
                elif value.replace('.', '').replace('-', '').isdigit():
                    try:
                        result[key] = float(value) if '.' in value else int(value)
                    except ValueError:
                        result[key] = value
                else:
                    result[key] = value
                break
    
    return result
