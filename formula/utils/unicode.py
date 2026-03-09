"""
Unicode Normalizer for LP DSL Engine

This module provides Unicode normalization for mathematical expressions,
ensuring compatibility with Windows PowerShell and mixed encoding environments.

Week 2 Requirements:
1. Support both ASCII and Unicode comparison operators
2. Normalize Unicode operators to ASCII before AST parsing
3. Handle UTF-8 decoding with fallback strategies
4. Normalize line endings (CRLF → LF) for Windows compatibility
5. Provide PowerShell-safe text processing

Design Principles:
- Isolated normalization logic
- Backward compatibility with ASCII operators
- Safe handling of mixed encodings
- PowerShell execution awareness
"""

import unicodedata
from typing import Union
import html


class UnicodeNormalizer:
    """
    Normalizes Unicode text for consistent parsing in LP DSL engine.
    
    Handles:
    - Unicode operator replacement (≤ → <=, ≥ → >=, ＝ → ==)
    - UTF-8 decoding with fallback
    - Line ending normalization (CRLF → LF)
    - Tab normalization (tabs → spaces)
    - HTML entity decoding
    """
    
    def __init__(self):
        """Initialize the Unicode normalizer with operator mappings."""
        # Unicode to ASCII operator mappings
        self.unicode_to_ascii = {
            '≤': '<=',      # Unicode less-than-or-equal
            '≥': '>=',      # Unicode greater-than-or-equal
            '＝': '==',      # Unicode equals (fullwidth)
            '≠': '!=',      # Unicode not equal
            '＜': '<',       # Unicode less-than (fullwidth)
            '＞': '>',       # Unicode greater-than (fullwidth)
            '≈': '~=',      # Unicode approximately equal
        }
        
        # Additional Unicode math symbols that might appear
        self.additional_replacements = {
            '·': '*',       # Middle dot as multiplication
            '×': '*',       # Multiplication sign
            '÷': '/',       # Division sign
            '−': '-',       # Minus sign (different from hyphen)
            '–': '-',       # En dash
            '—': '-',       # Em dash
        }
        
        # Combine all replacements
        self.all_replacements = {**self.unicode_to_ascii, **self.additional_replacements}
    
    def normalize(self, text: Union[str, bytes]) -> str:
        """
        Normalize text for consistent parsing.
        
        Args:
            text: Input text (string or bytes)
            
        Returns:
            Normalized string ready for AST parsing
        """
        # Step 1: Ensure we have a string
        if isinstance(text, bytes):
            text = self._safe_decode(text)
        
        # Convert to string for type safety
        text_str = str(text)
        
        # Step 2: Decode HTML entities (for compatibility with existing system)
        text_str = html.unescape(text_str)
        
        # Step 3: Normalize Unicode characters (NFKC form)
        text_str = unicodedata.normalize('NFKC', text_str)
        
        # Step 4: Replace Unicode operators with ASCII equivalents
        text_str = self._replace_unicode_operators(text_str)
        
        # Step 5: Normalize line endings (Windows compatibility)
        text_str = self._normalize_line_endings(text_str)
        
        # Step 6: Normalize tabs to spaces (optional, for consistency)
        text_str = self._normalize_tabs(text_str)
        
        # Step 7: Remove any zero-width or invisible characters
        text_str = self._remove_invisible_chars(text_str)
        
        return text_str
    
    def _safe_decode(self, data: bytes) -> str:
        """
        Safely decode bytes to string with multiple fallback strategies.
        
        Args:
            data: Bytes to decode
            
        Returns:
            Decoded string
        """
        # Try UTF-8 first (most common)
        try:
            return data.decode('utf-8')
        except UnicodeDecodeError:
            pass
        
        # Try common Windows encodings
        encodings = ['cp1252', 'latin-1', 'iso-8859-1', 'ascii']
        
        for encoding in encodings:
            try:
                return data.decode(encoding)
            except UnicodeDecodeError:
                continue
        
        # Final fallback: replace errors with replacement character
        return data.decode('utf-8', errors='replace')
    
    def _replace_unicode_operators(self, text: str) -> str:
        """
        Replace Unicode operators with ASCII equivalents.
        
        Args:
            text: Input text
            
        Returns:
            Text with Unicode operators replaced
        """
        for unicode_char, ascii_replacement in self.all_replacements.items():
            text = text.replace(unicode_char, ascii_replacement)
        return text
    
    def _normalize_line_endings(self, text: str) -> str:
        """
        Normalize line endings to Unix-style (LF).
        
        Args:
            text: Input text
            
        Returns:
            Text with normalized line endings
        """
        # Replace CRLF with LF
        text = text.replace('\r\n', '\n')
        # Replace any remaining CR with LF
        text = text.replace('\r', '\n')
        return text
    
    def _normalize_tabs(self, text: str) -> str:
        """
        Normalize tabs to spaces (4 spaces per tab).
        
        Args:
            text: Input text
            
        Returns:
            Text with tabs replaced by spaces
        """
        return text.replace('\t', '    ')
    
    def _remove_invisible_chars(self, text: str) -> str:
        """
        Remove zero-width and invisible characters.
        
        Args:
            text: Input text
            
        Returns:
            Text with invisible characters removed
        """
        # Common invisible/zero-width characters
        invisible_chars = [
            '\u200b',  # Zero-width space
            '\u200c',  # Zero-width non-joiner
            '\u200d',  # Zero-width joiner
            '\u2060',  # Word joiner
            '\ufeff',  # Byte order mark
            '\u00a0',  # Non-breaking space (replace with regular space)
        ]
        
        for char in invisible_chars:
            if char == '\u00a0':  # Non-breaking space
                text = text.replace(char, ' ')
            else:
                text = text.replace(char, '')
        
        return text
    
    def normalize_expression(self, expression: str) -> str:
        """
        Convenience method for normalizing mathematical expressions.
        
        Args:
            expression: Mathematical expression string
            
        Returns:
            Normalized expression ready for parsing
        """
        return self.normalize(expression)
    
    def is_unicode_operator_present(self, text: str) -> bool:
        """
        Check if text contains Unicode operators.
        
        Args:
            text: Text to check
            
        Returns:
            True if Unicode operators are present
        """
        for unicode_char in self.unicode_to_ascii.keys():
            if unicode_char in text:
                return True
        return False
    
    def extract_unicode_operators(self, text: str) -> list:
        """
        Extract all Unicode operators found in text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of Unicode operators found
        """
        found = []
        for unicode_char in self.unicode_to_ascii.keys():
            if unicode_char in text:
                found.append(unicode_char)
        return found


# ============================================================================
# PUBLIC API FUNCTIONS
# ============================================================================

def normalize_expression(expression: Union[str, bytes]) -> str:
    """
    Normalize a mathematical expression for parsing.
    
    Args:
        expression: Expression string or bytes
        
    Returns:
        Normalized expression string
    """
    normalizer = UnicodeNormalizer()
    return normalizer.normalize(expression)


def normalize_for_powershell(text: Union[str, bytes]) -> str:
    """
    Normalize text specifically for PowerShell execution.
    
    Args:
        text: Text to normalize
        
    Returns:
        PowerShell-safe normalized text
    """
    normalizer = UnicodeNormalizer()
    normalized = normalizer.normalize(text)
    
    # Additional PowerShell-specific normalization
    # Ensure no backticks that might cause issues
    normalized = normalized.replace('`', "'")
    
    return normalized


def test_unicode_normalization():
    """
    Test the Unicode normalization functionality.
    
    Returns:
        Dictionary of test results
    """
    normalizer = UnicodeNormalizer()
    
    test_cases = [
        ("x ≤ y", "x <= y"),
        ("a ≥ b", "a >= b"),
        ("c ＝ d", "c == d"),
        ("x ≠ y", "x != y"),
        ("a·b", "a*b"),
        ("x×y", "x*y"),
        ("a÷b", "a/b"),
        ("a−b", "a-b"),
        ("x\r\ny", "x\ny"),  # CRLF normalization
        ("x\ty", "x    y"),  # Tab normalization
        ("x&le;y", "x<=y"),  # HTML entity
    ]
    
    results = []
    for input_text, expected in test_cases:
        normalized = normalizer.normalize(input_text)
        passed = normalized == expected
        results.append({
            'input': input_text,
            'normalized': normalized,
            'expected': expected,
            'passed': passed
        })
    
    return results


# ============================================================================
# MAIN MODULE TEST
# ============================================================================

if __name__ == "__main__":
    """Test the Unicode normalizer module."""
    print("Unicode Normalizer - Week 2 Implementation")
    print("=" * 60)
    
    # Run tests
    test_results = test_unicode_normalization()
    
    all_passed = True
    for result in test_results:
        status = "✓" if result['passed'] else "✗"
        print(f"{status} Input: {repr(result['input'])}")
        print(f"  Normalized: {repr(result['normalized'])}")
        print(f"  Expected: {repr(result['expected'])}")
        if not result['passed']:
            all_passed = False
        print()
    
    print("=" * 60)
    if all_passed:
        print("All tests passed! ✓")
    else:
        print("Some tests failed! ✗")
    
    # Example usage
    print("\nExample usage:")
    expr = "x ≤ y AND a ≥ b"
    normalized = normalize_expression(expr)
    print(f"Original: {expr}")
    print(f"Normalized: {normalized}")
    
    # Check for Unicode operators
    normalizer = UnicodeNormalizer()
    has_unicode = normalizer.is_unicode_operator_present(expr)
    print(f"Contains Unicode operators: {has_unicode}")
    
    if has_unicode:
        operators = normalizer.extract_unicode_operators(expr)
        print(f"Unicode operators found: {operators}")