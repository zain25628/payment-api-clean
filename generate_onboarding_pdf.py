#!/usr/bin/env python3
"""Generate a merchant onboarding PDF from a markdown template with simple
placeholder replacement.

Usage example:
  python generate_onboarding_pdf.py \
    --merchant-name "UI Test Shop" \
    --api-key "ABC123" \
    --base-url "http://localhost:8000" \
    --environment dev
"""

import argparse
import sys
import os
import re
from datetime import date


def slugify(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")
    return s or "merchant"


def load_template(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def replace_placeholders(template: str, mapping: dict) -> str:
    out = template
    for k, v in mapping.items():
        out = out.replace("{{%s}}" % k, v)
    return out


def main():
    parser = argparse.ArgumentParser(description="Generate onboarding PDF for a merchant")
    parser.add_argument("--merchant-name", required=True)
    parser.add_argument("--api-key", required=True)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--environment", default="dev")
    parser.add_argument("--template", default="docs/MERCHANT_ONBOARDING_TEMPLATE.md")
    parser.add_argument("--output", default=None)

    args = parser.parse_args()

    template_path = args.template
    if not os.path.exists(template_path):
        print(f"Template not found: {template_path}")
        sys.exit(2)

    md = load_template(template_path)

    mapping = {
        "MERCHANT_NAME": args.merchant_name,
        "API_KEY": args.api_key,
        "BASE_URL": args.base_url,
        "ENVIRONMENT": args.environment,
    }

    filled_md = replace_placeholders(md, mapping)

    # Convert markdown -> HTML
    try:
        import markdown
    except Exception:
        print("Missing dependency 'markdown'. Install with: pip install -r requirements.txt")
        sys.exit(3)

    html_body = markdown.markdown(filled_md, extensions=["fenced_code", "tables"]) if hasattr(markdown, 'markdown') else markdown.markdown(filled_md)
    html = f"<html><head><meta charset='utf-8'><style>body{{font-family: Arial, sans-serif; padding:20px}} pre {{background:#111;color:#fff;padding:12px;border-radius:6px;overflow:auto}} code{{white-space:pre-wrap}}</style></head><body>{html_body}</body></html>"

    try:
        from weasyprint import HTML
    except Exception:
        print("Missing dependency 'WeasyPrint'. Install with: pip install -r requirements.txt")
        sys.exit(4)

    today = date.today().isoformat()
    slug = slugify(args.merchant_name)
    out_path = args.output or f"docs/{slug}-onboarding-{today}.pdf"

    try:
        HTML(string=html).write_pdf(out_path)
    except Exception as e:
        print("Failed to generate PDF:", e)
        sys.exit(5)

    print(f"✅ Onboarding PDF generated: {out_path}")


if __name__ == '__main__':
    main()
