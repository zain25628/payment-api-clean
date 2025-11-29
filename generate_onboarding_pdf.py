import argparse
from datetime import date
from pathlib import Path
import textwrap

import markdown

# حاول نستورد WeasyPrint، بس لا نفشل لو مش شغّال بالكامل (ويندوز 🙃)
try:
    from weasyprint import HTML  # type: ignore
except Exception as e:  # ImportError أو مشاكل DLL
    HTML = None
    WEASYPRINT_IMPORT_ERROR = e
else:
    WEASYPRINT_IMPORT_ERROR = None


TEMPLATE_PATH = Path("docs") / "MERCHANT_ONBOARDING_TEMPLATE.md"


def slugify(name: str) -> str:
    base = name.strip().lower().replace(" ", "-")
    # احتفظ فقط بالأرقام والحروف والـ -
    return "".join(ch for ch in base if ch.isalnum() or ch == "-") or "merchant"


def render_template(merchant_name: str, api_key: str, base_url: str, environment: str) -> str:
    if not TEMPLATE_PATH.exists():
        raise SystemExit(f"Template not found at {TEMPLATE_PATH!s}")

    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    replacements = {
        "MERCHANT_NAME": merchant_name,
        "API_KEY": api_key,
        "BASE_URL": base_url,
        "ENVIRONMENT": environment,
    }

    text = template
    for key, value in replacements.items():
        text = text.replace(f"{{{{{key}}}}}", value)

    return text


def build_html(markdown_text: str, title: str) -> str:
    body = markdown.markdown(
        markdown_text,
        extensions=["fenced_code", "tables"],
    )

    css = textwrap.dedent(
        """
        body {
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            font-size: 14px;
            color: #111827;
            line-height: 1.5;
            margin: 2rem;
        }
        h1, h2, h3 {
            color: #111827;
        }
        code {
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
        }
        pre {
            background: #0b1020;
            color: #e5e7eb;
            padding: 1rem;
            border-radius: 0.75rem;
            overflow-x: auto;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 1rem 0;
        }
        table, th, td {
            border: 1px solid #e5e7eb;
        }
        th, td {
            padding: 0.5rem;
            text-align: left;
        }
        """
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  <style>{css}</style>
</head>
<body>
{body}
</body>
</html>
"""
    return html


def generate_onboarding(
    merchant_name: str,
    api_key: str,
    base_url: str,
    environment: str,
    output_dir: Path,
) -> tuple[Path, Path | None]:
    """Generate onboarding HTML and optionally PDF.

    Returns (html_path, pdf_path_or_none).
    """
    markdown_text = render_template(
        merchant_name=merchant_name,
        api_key=api_key,
        base_url=base_url,
        environment=environment,
    )

    slug = slugify(merchant_name)
    today = date.today().isoformat()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    base_name = f"{slug}-onboarding-{environment}-{today}"
    html_path = output_dir / f"{base_name}.html"
    pdf_path = output_dir / f"{base_name}.pdf"

    html = build_html(markdown_text, title=f"{merchant_name} – Onboarding")

    html_path.write_text(html, encoding="utf-8")

    # If WeasyPrint is not importable, return None for pdf_path
    if HTML is None:
        return html_path, None

    try:
        HTML(string=html).write_pdf(str(pdf_path))
    except Exception:
        return html_path, None
    return html_path, pdf_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate merchant onboarding PDF/HTML from template.")
    parser.add_argument("--merchant-name", required=True)
    parser.add_argument("--api-key", required=True)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--environment", default="dev")
    parser.add_argument(
        "--output-dir",
        default="docs",
        help="Directory for output files (default: docs)",
    )

    args = parser.parse_args()

    # Use the reusable API below
    html_path, pdf_path = generate_onboarding(
        merchant_name=args.merchant_name,
        api_key=args.api_key,
        base_url=args.base_url,
        environment=args.environment,
        output_dir=Path(args.output_dir),
    )

    print(f"✅ HTML onboarding doc generated at: {html_path}")
    if pdf_path is not None:
        print(f"✅ PDF onboarding doc generated at: {pdf_path}")
    else:
        print(
            "\n⚠️ PDF not generated (WeasyPrint missing or failed). You can open the HTML file in a browser and Print → Save as PDF."
        )


if __name__ == "__main__":
    main()
