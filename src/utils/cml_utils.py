"""
CML Report Utilities for SIMKOPDES Pipeline.

Provides helper functions and a CLI to generate CML-compatible markdown reports
by publishing PNG figures via `cml image` command.

CLI Usage:
    python src/utils/cml_utils.py \\
        --report reports/eda_summary.md \\
        --figures reports/figures/eda_top_provinces.png reports/figures/eda_top_regencies_transaksi.png \\
        --output reports/cml_eda.md \\
        --title "📊 Laporan EDA SIMKOPDES"
"""
import os
import sys
import re
import subprocess
import argparse

from utils.plot_utils import file_to_base64


def cml_publish_image(filepath):
    """
    Convert a PNG image file to base64 and return an HTML <img> tag with width 300.

    Args:
        filepath: Path to the PNG image file.

    Returns:
        An HTML img tag string with base64 source and width 300.
    """
    if not os.path.exists(filepath):
        print(f"[WARN] Image not found: {filepath}")
        return ""

    try:
        encoded = file_to_base64(filepath)
        if not encoded:
            return ""
        basename = os.path.basename(filepath)
        alt_text = os.path.splitext(basename)[0].replace('_', ' ').replace('-', ' ').title()
        return f'<img src="data:image/png;base64,{encoded}" alt="{alt_text}" width="300">'
    except Exception as e:
        print(f"[WARN] Failed to convert {filepath} to base64: {e}")
        basename = os.path.basename(filepath)
        return f"![{basename}](figures/{basename})"


def strip_base64_images(md_content):
    """
    Remove base64-encoded image lines from markdown content.

    Lines matching `![...](data:image/png;base64,...)` or `<img src="data:image/png;base64,...">`
    are replaced with an empty placeholder so the text structure is preserved.

    Args:
        md_content: Raw markdown string.

    Returns:
        Cleaned markdown string without base64 images.
    """
    # Match markdown image syntax with base64 data URI
    pattern_md = r'!\[[^\]]*\]\(data:image/[^)]+\)'
    content = re.sub(pattern_md, '', md_content)
    # Match HTML image syntax with base64 data URI
    pattern_html = r'<img src="data:image/[^"]+"[^>]*>'
    return re.sub(pattern_html, '', content)


def build_cml_report(report_md_path, figure_paths, title=None):
    """
    Build a CML-compatible markdown report.

    Reads the original markdown report, strips base64 images, publishes
    PNG figures via `cml image`, and assembles the final report.

    Args:
        report_md_path: Path to the source markdown report.
        figure_paths: List of PNG file paths to publish via CML.
        title: Optional title override for the report header.

    Returns:
        CML-ready markdown string.
    """
    # Read source report
    if not os.path.exists(report_md_path):
        print(f"[ERROR] Report not found: {report_md_path}")
        return ""

    with open(report_md_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Strip base64 images
    content = strip_base64_images(content)

    # Clean up empty lines left by stripped images
    content = re.sub(r'\n{3,}', '\n\n', content)

    # Publish figures and build image section
    if figure_paths:
        image_section = "\n\n## Visualisasi\n\n"
        for fig_path in figure_paths:
            if os.path.exists(fig_path):
                img_tag = cml_publish_image(fig_path)
                if img_tag:
                    image_section += f"{img_tag}\n\n"
        content += image_section

    # Optionally override the title
    if title:
        # Replace the first H1 heading
        content = re.sub(r'^#\s+.+$', f'# {title}', content, count=1, flags=re.MULTILINE)

    return content


def main():
    parser = argparse.ArgumentParser(
        description="Generate a CML-compatible markdown report with published images."
    )
    parser.add_argument(
        "--report",
        required=True,
        help="Path to the source markdown report file."
    )
    parser.add_argument(
        "--figures",
        nargs="*",
        default=[],
        help="Paths to PNG figure files to publish via `cml image`."
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to write the CML-ready report."
    )
    parser.add_argument(
        "--title",
        default=None,
        help="Optional title override for the report header."
    )

    args = parser.parse_args()

    print(f"[+] Generating CML report from: {args.report}")
    report = build_cml_report(args.report, args.figures, args.title)

    if report:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"[SAVED] CML Report -> {args.output}")
    else:
        print("[ERROR] Failed to generate CML report.")
        sys.exit(1)


if __name__ == "__main__":
    main()
