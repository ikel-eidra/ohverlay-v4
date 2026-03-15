"""
OVL Parser - Ohverlay Language Parser
=======================================
Parses .ovl files into an AST (Abstract Syntax Tree) that the
compiler uses to generate HTML5 Canvas overlays.

Grammar (simplified):
  document     = block*
  block        = '@' IDENT STRING? NEWLINE property*
  property     = INDENT IDENT ':' value NEWLINE
  value        = STRING | NUMBER | IDENT | color | size | range | list
  list         = value (',' value)*
  range        = NUMBER '~' NUMBER
  size         = NUMBER 'x' NUMBER
  color        = HEX | NAMED_COLOR | 'rgb(' NUMBER ',' NUMBER ',' NUMBER ')'
  percentage   = NUMBER '%'
"""

import re
from typing import List, Dict, Optional, Any
from ovl.spec import (
    VALID_BLOCKS, NAMED_COLORS, VALID_STYLES,
    VALID_MOVEMENTS, BUILTIN_CREATURES, BUILTIN_PARTICLES,
)


class OVLParseError(Exception):
    """Raised when an OVL file has syntax or semantic errors."""
    def __init__(self, message, line=0, col=0):
        self.line = line
        self.col = col
        super().__init__(f"Line {line}: {message}")


class OVLNode:
    """A node in the OVL AST."""
    def __init__(self, node_type, name="", properties=None, children=None, line=0):
        self.type = node_type       # 'overlay', 'creature', 'particles', etc.
        self.name = name            # Optional name string
        self.properties = properties or {}
        self.children = children or []
        self.line = line

    def get(self, key, default=None):
        return self.properties.get(key, default)

    def __repr__(self):
        return f"OVLNode({self.type}, name={self.name!r}, props={len(self.properties)}, children={len(self.children)})"


class OVLParser:
    """
    Parses OVL source text into an AST.

    Usage:
        parser = OVLParser()
        ast = parser.parse(ovl_source_text)
        # ast is a list of OVLNode (usually one @overlay root)
    """

    def __init__(self, strict=False):
        self.strict = strict
        self.errors = []

    def parse(self, source: str) -> List[OVLNode]:
        """Parse OVL source text and return list of top-level nodes."""
        self.errors = []
        lines = source.split("\n")
        nodes = []
        i = 0

        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # Skip empty lines and comments
            if not stripped or stripped.startswith("//"):
                i += 1
                continue

            # Block declaration: @keyword "name"
            if stripped.startswith("@"):
                node, i = self._parse_block(lines, i)
                if node:
                    nodes.append(node)
            else:
                self._error(f"Unexpected line (expected @block): {stripped}", i + 1)
                i += 1

        return nodes

    def _parse_block(self, lines, start):
        """Parse a block starting with @ and its indented children."""
        line = lines[start].strip()
        line_num = start + 1

        # Extract block type and optional name
        match = re.match(r'^@(\w+)\s*(?:"([^"]*)")?(.*)$', line)
        if not match:
            self._error(f"Invalid block syntax: {line}", line_num)
            return None, start + 1

        block_type = match.group(1).lower()
        block_name = match.group(2) or ""
        remainder = match.group(3).strip()

        # If no quoted name, the word after @type is the name
        if not block_name and remainder and not remainder.startswith("//"):
            # e.g. @creature jellyfish or @particles bubbles
            name_match = re.match(r'^(\w[\w-]*)', remainder)
            if name_match:
                block_name = name_match.group(1)

        if self.strict and block_type not in VALID_BLOCKS:
            self._error(f"Unknown block type: @{block_type}", line_num)

        node = OVLNode(block_type, block_name, line=line_num)

        # Parse indented properties and child blocks
        i = start + 1
        base_indent = self._get_indent(lines[start]) if start < len(lines) else 0

        while i < len(lines):
            current_line = lines[i]
            stripped = current_line.strip()

            # Skip empty lines and comments within block
            if not stripped or stripped.startswith("//"):
                i += 1
                continue

            current_indent = self._get_indent(current_line)

            # If dedented back to or beyond parent level, block is done
            if current_indent <= base_indent:
                break

            # Nested block
            if stripped.startswith("@"):
                child, i = self._parse_block(lines, i)
                if child:
                    node.children.append(child)
                continue

            # Property: key: value
            prop_match = re.match(r'^([\w-]+)\s*:\s*(.+)$', stripped)
            if prop_match:
                key = prop_match.group(1).lower()
                raw_value = prop_match.group(2).strip()
                # Remove inline comment
                if " //" in raw_value:
                    raw_value = raw_value[:raw_value.index(" //")].strip()
                node.properties[key] = self._parse_value(raw_value, key)
            elif stripped.startswith("on "):
                # Behavior rule: on <event>: <action>
                beh_match = re.match(r'^on\s+([\w-]+)\s*:\s*(.+)$', stripped)
                if beh_match:
                    event = beh_match.group(1).lower()
                    action = beh_match.group(2).strip()
                    if "behaviors" not in node.properties:
                        node.properties["behaviors"] = {}
                    node.properties["behaviors"][event] = action
            else:
                self._error(f"Invalid property syntax: {stripped}", i + 1)

            i += 1

        return node, i

    def _parse_value(self, raw: str, key: str = "") -> Any:
        """Parse a property value into a typed Python object."""

        # Boolean
        if raw.lower() in ("true", "yes", "on"):
            return True
        if raw.lower() in ("false", "no", "off"):
            return False

        # None
        if raw.lower() in ("none", "null"):
            return None

        # Percentage: 70%
        pct_match = re.match(r'^(\d+(?:\.\d+)?)\s*%$', raw)
        if pct_match:
            return {"type": "percent", "value": float(pct_match.group(1))}

        # Size: 800 x 600 or 800x600
        size_match = re.match(r'^(\d+)\s*x\s*(\d+)$', raw, re.IGNORECASE)
        if size_match:
            return {"type": "size", "width": int(size_match.group(1)), "height": int(size_match.group(2))}

        # Fullscreen
        if raw.lower() == "fullscreen":
            return {"type": "size", "width": "full", "height": "full"}

        # Range: 0.5 ~ 1.2
        range_match = re.match(r'^([\d.]+)\s*~\s*([\d.]+)$', raw)
        if range_match:
            return {"type": "range", "min": float(range_match.group(1)), "max": float(range_match.group(2))}

        # Time: 2s, 500ms, 1.5m
        time_match = re.match(r'^([\d.]+)\s*(ms|s|m)$', raw)
        if time_match:
            val = float(time_match.group(1))
            unit = time_match.group(2)
            if unit == "ms":
                val /= 1000
            elif unit == "m":
                val *= 60
            return {"type": "time", "seconds": val}

        # Color: hex
        hex_match = re.match(r'^#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})$', raw)
        if hex_match:
            return {"type": "color", "value": raw.lower()}

        # Color: named
        if raw.lower() in NAMED_COLORS:
            return {"type": "color", "value": NAMED_COLORS[raw.lower()]}

        # Color: rainbow
        if raw.lower() == "rainbow":
            return {"type": "color", "value": "rainbow"}

        # Gradient: gradient(#ff0000, #0000ff)
        grad_match = re.match(r'^gradient\s*\(\s*(.+)\s*\)$', raw, re.IGNORECASE)
        if grad_match:
            colors = [c.strip() for c in grad_match.group(1).split(",")]
            resolved = []
            for c in colors:
                if c.lower() in NAMED_COLORS:
                    resolved.append(NAMED_COLORS[c.lower()])
                else:
                    resolved.append(c)
            return {"type": "gradient", "colors": resolved}

        # Comma-separated list
        if "," in raw:
            items = [self._parse_value(v.strip(), key) for v in raw.split(",")]
            return {"type": "list", "items": items}

        # Glow shorthand: cyan 0.8
        glow_match = re.match(r'^(\w+)\s+([\d.]+)$', raw)
        if glow_match and key == "glow":
            color_name = glow_match.group(1).lower()
            intensity = float(glow_match.group(2))
            color_val = NAMED_COLORS.get(color_name, f"#{color_name}" if len(color_name) == 6 else color_name)
            return {"type": "glow", "color": color_val, "intensity": intensity}

        # Pure number
        num_match = re.match(r'^-?(\d+(?:\.\d+)?)$', raw)
        if num_match:
            val = float(raw)
            return int(val) if val == int(val) else val

        # Plain string/identifier
        return raw.strip()

    def _get_indent(self, line):
        """Count leading spaces (tabs count as 2 spaces)."""
        count = 0
        for ch in line:
            if ch == " ":
                count += 1
            elif ch == "\t":
                count += 2
            else:
                break
        return count

    def _error(self, msg, line):
        err = OVLParseError(msg, line)
        self.errors.append(err)
        if self.strict:
            raise err


def parse_ovl(source: str, strict=False) -> List[OVLNode]:
    """Convenience function to parse OVL source text."""
    parser = OVLParser(strict=strict)
    return parser.parse(source)


def parse_ovl_file(filepath: str, strict=False) -> List[OVLNode]:
    """Parse an OVL file from disk."""
    with open(filepath, "r", encoding="utf-8") as f:
        return parse_ovl(f.read(), strict=strict)
