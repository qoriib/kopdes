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

# Ensure src/ is in sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.plot_utils import file_to_base64
from utils.log_utils import get_logger

logger = get_logger("cml_utils")


def cml_publish_image(filepath):
    """
    Convert a PNG image file to a CML published external URL or base64 fallback
    and return an HTML <img> tag with width 300.

    Args:
        filepath: Path to the PNG image file.

    Returns:
        An HTML img tag string with the published URL or base64 source and width 300.
    """
    if not os.path.exists(filepath):
        logger.warning(f"Image not found: {filepath}")
        return ""

    basename = os.path.basename(filepath)
    alt_text = os.path.splitext(basename)[0].replace('_', ' ').replace('-', ' ').title()

    # 1. Try to publish image using CML to get an external URL
    try:
        res = subprocess.run(
            ["cml", "publish", filepath],
            capture_output=True,
            text=True,
            check=True
        )
        stdout_val = res.stdout.strip()
        match = re.search(r'\((https?://[^\)]+)\)', stdout_val)
        if match:
            url = match.group(1)
            logger.info(f"Published image to CML: {url}")
            return f'<img src="{url}" alt="{alt_text}" width="300">'
    except Exception as e:
        logger.warning(f"cml publish failed or not available, falling back to base64: {e}")

    # 2. Fallback to base64
    try:
        encoded = file_to_base64(filepath)
        if not encoded:
            return ""
        return f'<img src="data:image/png;base64,{encoded}" alt="{alt_text}" width="300">'
    except Exception as e:
        logger.warning(f"Failed to convert {filepath} to base64: {e}")
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


def build_cml_report(report_md_path, figure_paths=None, title=None):
    """
    Build a CML-compatible markdown report by finding and publishing
    all locally referenced figures inline.

    Args:
        report_md_path: Path to the source markdown report.
        figure_paths: Unused, kept for CLI compatibility.
        title: Optional title override for the report header.

    Returns:
        CML-ready markdown string with published inline images.
    """
    if not os.path.exists(report_md_path):
        logger.error(f"Report not found: {report_md_path}")
        return ""

    with open(report_md_path, "r", encoding="utf-8") as f:
        content = f.read()

    report_dir = os.path.dirname(report_md_path)

    # 1. Parse and replace HTML <img src="..."> tags inline
    def replace_html_img(match):
        full_tag = match.group(0)
        src = match.group(2)
        # Check if it is a local path
        if not (src.startswith("http://") or src.startswith("https://") or src.startswith("data:")):
            resolved_path = os.path.normpath(os.path.join(report_dir, src))
            if os.path.exists(resolved_path):
                img_tag = cml_publish_image(resolved_path)
                if img_tag:
                    return img_tag
        return full_tag

    # Matches <img ... src="path" ...>
    content = re.sub(r'<img([^>]+)src=["\'\s]([^"\'\s>]+)["\'\s]([^>]*)>', replace_html_img, content)

    # 2. Parse and replace Markdown ![alt](src) tags inline
    def replace_md_img(match):
        full_tag = match.group(0)
        alt = match.group(1)
        src = match.group(2)
        if not (src.startswith("http://") or src.startswith("https://") or src.startswith("data:")):
            resolved_path = os.path.normpath(os.path.join(report_dir, src))
            if os.path.exists(resolved_path):
                img_tag = cml_publish_image(resolved_path)
                if img_tag:
                    return img_tag
        return full_tag

    content = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', replace_md_img, content)

    # Optionally override the title
    if title:
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

    logger.info(f"Generating CML report from: {args.report}")
    report = build_cml_report(args.report, args.figures, args.title)

    if report:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report)
        logger.info(f"CML Report -> {args.output}")
    else:
        logger.error("Failed to generate CML report.")
        sys.exit(1)


if __name__ == "__main__":
    main()
