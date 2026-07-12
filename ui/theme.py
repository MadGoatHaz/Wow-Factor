"""
UI Theme System - Centralized Design Tokens

Provides a single source of truth for colors, spacing, and typography
to eliminate hardcoded values across the UI.
"""

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class ColorPalette:
    """
    Centralized color definitions using CSS-compatible hex codes.
    All colors are defined as named constants for consistency.
    """
    # Primary Brand Colors
    PRIMARY_CYAN: str = "#06b6d4"      # Cyan-500 equivalent
    PRIMARY_DARK: str = "#0891b2"      # Cyan-700 equivalent
    
    # Accent Colors
    PRIMARY_BLUE: str = "#3b82f6"      # Blue-500 - Primary blue variant
    ACCENT_MAGENTA: str = "#d946ef"    # Fuchsia-500 equivalent
    ACCENT_PINK: str = "#ec4899"       # Pink-500 equivalent
    ACCENT_PURPLE: str = "#a855f7"     # Purple-500 equivalent
    ACCENT_YELLOW: str = "#eab308"     # Yellow-500 - Accent yellow
    ACCENT_ORANGE: str = "#f97316"     # Orange-500 - Accent orange
    
    # Semantic Colors (Status Indicators)
    SUCCESS_GREEN: str = "#22c55e"     # Green-500
    WARNING_YELLOW: str = "#eab308"    # Yellow-500
    ERROR_RED: str = "#ef4444"         # Red-500
    INFO_BLUE: str = "#3b82f6"         # Blue-500
    
    # Neutral Colors (Grays)
    BG_DARK: str = "#0f172a"           # Slate-900 - Main background
    BG_DARKER: str = "#020617"         # Slate-950 - Deepest background
    BG_CARD: str = "#1e293b"           # Slate-800 - Card backgrounds
    BG_HOVER: str = "#334155"          # Slate-700 - Hover states
    
    # Text Colors
    TEXT_PRIMARY: str = "#f8fafc"      # Slate-50 - Main text
    TEXT_SECONDARY: str = "#cbd5e1"    # Slate-300 - Secondary text
    TEXT_MUTED: str = "#64748b"        # Slate-500 - Muted/disabled text
    TEXT_DARK: str = "#0f172a"         # Slate-900 - Dark text on light backgrounds
    
    # Border/Divider Colors
    BORDER_SUBTLE: str = "#334155"     # Slate-700 - Subtle borders
    BORDER_DEFAULT: str = "#475569"    # Slate-600 - Default borders
    BORDER_STRONG: str = "#94a3b8"     # Slate-400 - Strong borders
    
    # Gradient Endpoints (for gradient utilities)
    GRADIENT_START: str = "#06b6d4"    # Cyan start
    GRADIENT_END: str = "#d946ef"      # Fuchsia end
    
    @classmethod
    def get_rgb(cls, hex_color: str) -> Tuple[int, int, int]:
        """
        Convert a hex color string to RGB tuple.
        
        Args:
            hex_color: Hex color string (e.g., '#06b6d4')
            
        Returns:
            Tuple of (R, G, B) values
        """
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    @classmethod
    def get_css_rgb(cls, hex_color: str) -> str:
        """
        Convert a hex color string to CSS rgb() format.
        
        Args:
            hex_color: Hex color string (e.g., '#06b6d4')
            
        Returns:
            CSS rgb() string (e.g., 'rgb(6, 182, 212)')
        """
        r, g, b = cls.get_rgb(hex_color)
        return f"rgb({r}, {g}, {b})"


@dataclass(frozen=True)
class SpacingScale:
    """
    Consistent spacing scale based on 2px base unit.
    All margins and paddings should use these values.
    """
    SPACING_XS: int = 1      # Extra small - minimal spacing
    SPACING_SM: int = 2      # Small - compact elements
    SPACING_MD: int = 4      # Medium - standard spacing
    SPACING_LG: int = 8      # Large - generous spacing
    SPACING_XL: int = 16     # Extra large - section dividers
    SPACING_2XL: int = 32    # Two extra large - major sections
    
    @classmethod
    def get(cls, size_name: str) -> int:
        """
        Get spacing value by name.
        
        Args:
            size_name: One of SPACING_XS, SPACING_SM, etc.
            
        Returns:
            Spacing value in pixels
        """
        return getattr(cls, size_name)
    
    @classmethod
    def double(cls, base_size: int) -> int:
        """
        Double a spacing value (useful for margins).
        
        Args:
            base_size: Base spacing value from SpacingScale
            
        Returns:
            Doubled spacing value
        """
        return base_size * 2


@dataclass(frozen=True)
class Typography:
    """
    Typography tokens for consistent text styling.
    """
    # Font Weights
    FONT_LIGHT: int = 300
    FONT_NORMAL: int = 400
    FONT_MEDIUM: int = 500
    FONT_SEMIBOLD: int = 600
    FONT_BOLD: int = 700
    FONT_EXTRABOLD: int = 800
    
    # Font Sizes (in pixels)
    TEXT_XS: int = 12        # Extra small - captions, hints
    TEXT_SM: int = 14        # Small - secondary text
    TEXT_MD: int = 16        # Medium - body text
    TEXT_LG: int = 18        # Large - headings
    TEXT_XL: int = 20        # Extra large - section headers
    TEXT_2XL: int = 24       # Two extra large - page titles
    TEXT_3XL: int = 30       # Three extra large - hero text
    
    @classmethod
    def get_weight(cls, weight_name: str) -> int:
        """
        Get font weight by name.
        
        Args:
            weight_name: One of FONT_LIGHT, FONT_NORMAL, etc.
            
        Returns:
            Font weight value
        """
        return getattr(cls, weight_name)
    
    @classmethod
    def get_size(cls, size_name: str) -> int:
        """
        Get font size by name.
        
        Args:
            size_name: One of TEXT_XS, TEXT_SM, etc.
            
        Returns:
            Font size in pixels
        """
        return getattr(cls, size_name)
