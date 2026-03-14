#!/usr/bin/env python3
"""
OVL CLI - Ohverlay Language Command Line Tool
================================================
Compile .ovl files into HTML5 Canvas overlays.

Usage:
  python -m ovl compile myoverlay.ovl              # → myoverlay.html
  python -m ovl compile myoverlay.ovl -o output.html
  python -m ovl validate myoverlay.ovl             # Check for errors
  python -m ovl preview myoverlay.ovl              # Compile and open in browser
  python -m ovl list-creatures                     # Show built-in creatures
  python -m ovl list-particles                     # Show built-in particles

Examples:
  python -m ovl compile ovl/examples/neon-jellyfish.ovl
  python -m ovl compile ovl/examples/fairy-garden.ovl -o fairy.html
"""

import sys
import os
import argparse

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ovl.parser import OVLParser, parse_ovl_file
from ovl.compiler import compile_ovl
from ovl.spec import BUILTIN_CREATURES, BUILTIN_PARTICLES, NAMED_COLORS


def cmd_compile(args):
    """Compile an .ovl file to HTML."""
    if not os.path.exists(args.input):
        print(f"Error: File not found: {args.input}")
        return 1

    print(f"Compiling: {args.input}")

    try:
        nodes = parse_ovl_file(args.input, strict=args.strict)

        if not nodes:
            print("Error: No overlay blocks found in file.")
            return 1

        html = compile_ovl(nodes)

        # Output path
        if args.output:
            out_path = args.output
        else:
            base = os.path.splitext(args.input)[0]
            out_path = base + ".html"

        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)

        size_kb = len(html) / 1024
        print(f"Output: {out_path} ({size_kb:.1f} KB)")
        print(f"Overlay: {nodes[0].name}")
        print(f"Creatures: {sum(1 for n in nodes[0].children if n.type == 'creature')}")
        print(f"Particles: {sum(1 for n in nodes[0].children if n.type == 'particles')}")
        return 0

    except Exception as e:
        print(f"Compile error: {e}")
        return 1


def cmd_validate(args):
    """Validate an .ovl file for syntax errors."""
    if not os.path.exists(args.input):
        print(f"Error: File not found: {args.input}")
        return 1

    print(f"Validating: {args.input}")

    parser = OVLParser(strict=True)
    try:
        with open(args.input, "r", encoding="utf-8") as f:
            source = f.read()
        nodes = parser.parse(source)

        if parser.errors:
            print(f"Found {len(parser.errors)} error(s):")
            for err in parser.errors:
                print(f"  Line {err.line}: {err}")
            return 1

        print(f"Valid! Found {len(nodes)} block(s).")

        for node in nodes:
            print(f"  @{node.type} \"{node.name}\"")
            for child in node.children:
                print(f"    @{child.type} {child.name} ({len(child.properties)} properties)")

        return 0

    except Exception as e:
        print(f"Parse error: {e}")
        return 1


def cmd_preview(args):
    """Compile and open in browser."""
    result = cmd_compile(args)
    if result != 0:
        return result

    out_path = args.output or os.path.splitext(args.input)[0] + ".html"

    try:
        import webbrowser
        webbrowser.open(f"file://{os.path.abspath(out_path)}")
        print("Opened in browser.")
    except Exception:
        print(f"Open manually: {os.path.abspath(out_path)}")

    return 0


def cmd_list_creatures(args):
    """List built-in creatures."""
    print("Built-in Creatures:")
    print("=" * 40)
    descriptions = {
        "fish": "Betta fish with flowing fins",
        "jellyfish": "Translucent jellyfish with tentacles",
        "manta": "Manta ray with wing-like motion",
        "fairy": "Humanoid wireframe with wings",
        "whale": "Large gentle whale",
        "dolphin": "Playful dolphin",
        "octopus": "Multi-tentacle creature",
        "butterfly": "Winged butterfly",
        "dragon": "Eastern dragon (serpentine)",
        "phoenix": "Fire bird with particle trail",
    }
    for c in sorted(BUILTIN_CREATURES):
        desc = descriptions.get(c, "")
        print(f"  {c:<14} {desc}")


def cmd_list_particles(args):
    """List built-in particle types."""
    print("Built-in Particles:")
    print("=" * 40)
    descriptions = {
        "bubbles": "Rising circular bubbles",
        "sparks": "Short-lived bright sparks",
        "snow": "Gentle falling snowflakes",
        "rain": "Vertical rain drops",
        "fireflies": "Glowing wandering dots",
        "cherry": "Cherry blossom petals",
        "stars": "Twinkling stars",
        "dust": "Floating dust motes",
        "embers": "Rising fire embers",
        "confetti": "Colorful falling confetti",
    }
    for p in sorted(BUILTIN_PARTICLES):
        desc = descriptions.get(p, "")
        print(f"  {p:<14} {desc}")


def cmd_list_colors(args):
    """List named colors."""
    print("Named Colors:")
    print("=" * 40)
    for name, hex_val in sorted(NAMED_COLORS.items()):
        print(f"  {name:<14} {hex_val}")


def main():
    parser = argparse.ArgumentParser(
        description="OVL - The Ohverlay Language Compiler",
        epilog="Create beautiful overlays with a simple language.",
    )
    sub = parser.add_subparsers(dest="command")

    # compile
    p_compile = sub.add_parser("compile", help="Compile .ovl to HTML")
    p_compile.add_argument("input", help="Input .ovl file")
    p_compile.add_argument("-o", "--output", help="Output .html file")
    p_compile.add_argument("--strict", action="store_true", help="Strict validation")

    # validate
    p_validate = sub.add_parser("validate", help="Validate .ovl syntax")
    p_validate.add_argument("input", help="Input .ovl file")

    # preview
    p_preview = sub.add_parser("preview", help="Compile and open in browser")
    p_preview.add_argument("input", help="Input .ovl file")
    p_preview.add_argument("-o", "--output", help="Output .html file")
    p_preview.add_argument("--strict", action="store_true")

    # list commands
    sub.add_parser("list-creatures", help="List built-in creatures")
    sub.add_parser("list-particles", help="List built-in particles")
    sub.add_parser("list-colors", help="List named colors")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    commands = {
        "compile": cmd_compile,
        "validate": cmd_validate,
        "preview": cmd_preview,
        "list-creatures": cmd_list_creatures,
        "list-particles": cmd_list_particles,
        "list-colors": cmd_list_colors,
    }

    result = commands[args.command](args)
    sys.exit(result or 0)


if __name__ == "__main__":
    main()
