"""Build the static test site from the design canvas's page files.

    python -I tools/sync_from_canvas.py [canvas_folder]

canvas_folder defaults to ./canvas (copies of the canvas's project/*.dc.html
files). Each page becomes a plain .html file at the repo root. Its template and
the templates of every component it uses are embedded inline, and
assets/dc-lite.js renders them in the browser, so the site needs no server-side
code and works on GitHub Pages or straight from disk.
"""
import html
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANVAS = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(ROOT, "canvas")

# canvas file -> (published file, page title, description)
PAGES = {
    "Home.dc.html": ("index.html", "Legacy Global | Live well, leave a legacy",
                     "Donor-advised funds, fiscal sponsorship and complex charitable gifts from Legacy Global."),
    "Services.dc.html": ("services.html", "Services | Legacy Global",
                         "Compare Legacy Global's five charitable giving vehicles."),
    "Svc-DAF.dc.html": ("donor-advised-funds.html", "Donor-Advised Funds | Legacy Global",
                        "Donor-advised funds sponsored by Legacy Global Foundation."),
    "Svc-FSP.dc.html": ("fiscal-sponsorship.html", "Fiscal Sponsorship | Legacy Global",
                        "Fiscal sponsorship for charitable programs through Legacy Global Programs."),
    "Svc-Complex.dc.html": ("complex-giving.html", "Complex Giving | Legacy Global",
                            "Gifts of business interests, real estate and other non-cash assets."),
    "Svc-Split.dc.html": ("split-interest-giving.html", "Split-Interest Giving | Legacy Global",
                          "Charitable remainder and lead trusts."),
    "Svc-Premium.dc.html": ("premium-financed-giving.html", "Premium Financed Giving | Legacy Global",
                            "Life insurance with financed premiums used for charitable planning."),
    "Family.dc.html": ("legacy-family.html", "The Legacy Family | Legacy Global",
                       "Legacy Global Foundation, Legacy Global Programs and Legacy Offices."),
    "About.dc.html": ("about.html", "About | Legacy Global",
                      "Legacy Global's mission, expertise and team."),
    "Gateway.dc.html": ("gateway.html", "The Legacy Gateway | Legacy Global",
                        "Requests for donors, fund advisors and charitable programs."),
    "Contact.dc.html": ("contact.html", "Contact | Legacy Global",
                        "Contact Legacy Global."),
}

NOT_FOUND = """<x-dc>
<div style="background: #1f2622; color: #ecebe2; font-family: 'IBM Plex Sans', system-ui, sans-serif; min-height: 100vh; display: flex; flex-direction: column">
<dc-import name="Header" current="none"></dc-import>
<section style="flex: 1; max-width: 1180px; width: 100%; margin: 0 auto; padding: 120px clamp(20px, 4vw, 48px); box-sizing: border-box">
<p style="margin: 0; font-family: 'IBM Plex Mono', monospace; font-size: 12px; letter-spacing: 0.12em; color: #7fc4c2">ERROR 404</p>
<h1 style="margin: 20px 0 0; font-family: 'Archivo', sans-serif; font-stretch: 108%; font-weight: 600; font-size: clamp(2.6rem, 6vw, 5rem); line-height: 0.96; letter-spacing: -0.035em">That key isn't mapped.</h1>
<p style="margin: 24px 0 0; max-width: 520px; font-size: 18px; color: #c8ccc4">The page you were looking for doesn't exist on this preview site.</p>
<a href="index.html" style="display: inline-flex; align-items: center; min-height: 50px; margin-top: 32px; padding: 0 22px; border-radius: 6px; background: #2A7173; color: #ffffff; font-family: 'IBM Plex Mono', monospace; font-size: 13px; letter-spacing: 0.08em; text-decoration: none; box-shadow: inset 0 -4px 0 rgba(0,0,0,0.3)">BACK TO HOME</a>
</section>
</div>
</x-dc>
<script type="text/x-dc" data-dc-script data-props='{}'>
class Component extends DCLogic { renderVals() { return {}; } }
</script>"""

LINK_MAP = {src: dst for src, (dst, _, _) in PAGES.items()}
RE_XDC = re.compile(r"<x-dc>(.*?)</x-dc>", re.S)
RE_SCRIPT = re.compile(r"<script type=\"text/x-dc\" data-dc-script(?: data-props='([^']*)')?>(.*?)</script>", re.S)
RE_IMPORT = re.compile(r"<dc-import\s+name=\"([A-Za-z0-9_-]+)\"")


def rewrite_links(text):
    for src, dst in LINK_MAP.items():
        text = re.sub(r"(?<![\w-])" + re.escape(src), dst, text)
    return text


def parse(text, label):
    m = RE_XDC.search(text)
    s = RE_SCRIPT.search(text)
    if not m or not s:
        raise SystemExit("Could not find the template or logic in " + label)
    return rewrite_links(m.group(1)), s.group(1) or "{}", rewrite_links(s.group(2))


def load_component(name):
    path = os.path.join(CANVAS, name + ".dc.html")
    if not os.path.exists(path):
        raise SystemExit("Missing component file: " + path)
    with open(path, encoding="utf-8") as f:
        return parse(f.read(), path)


def block(name, template, props, logic):
    return ('<template id="dc-%s">%s</template>\n'
            '<script type="text/x-dc" data-for="%s" data-props=\'%s\'>%s</script>\n'
            % (name, template, name, props, logic))


def build_page(out_name, title, description, page_parts, base=""):
    template, props, logic = page_parts
    blocks = [block("page", template, props, logic)]
    seen, queue = set(), RE_IMPORT.findall(template)
    while queue:
        name = queue.pop(0)
        if name in seen:
            continue
        seen.add(name)
        parts = load_component(name)
        blocks.append(block(name, *parts))
        queue.extend(RE_IMPORT.findall(parts[0]))
    base_tag = '<base href="%s">\n' % base if base else ""
    doc = (
        "<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        "<meta name=\"robots\" content=\"noindex, nofollow\">\n" + base_tag +
        "<title>%s</title>\n<meta name=\"description\" content=\"%s\">\n"
        "<link rel=\"icon\" href=\"assets/favicon.svg\" type=\"image/svg+xml\">\n"
        "<style id=\"dc-cloak\">body{visibility:hidden;background:#1f2622}</style>\n"
        "<noscript><style>body{visibility:visible !important}</style></noscript>\n"
        "<script src=\"assets/dc-lite.js\" defer></script>\n</head>\n<body>\n"
        % (html.escape(title), html.escape(description))
        + "".join(blocks) +
        "<noscript><p style=\"padding:24px;font:16px system-ui;color:#ecebe2\">This preview site needs JavaScript turned on.</p></noscript>\n"
        "</body>\n</html>\n"
    )
    with open(os.path.join(ROOT, out_name), "w", encoding="utf-8", newline="\n") as f:
        f.write(doc)
    print("  %-30s %6d bytes  components: %s" % (out_name, len(doc), ", ".join(sorted(seen)) or "none"))


def main():
    print("Building from " + CANVAS)
    for src, (dst, title, desc) in PAGES.items():
        with open(os.path.join(CANVAS, src), encoding="utf-8") as f:
            build_page(dst, title, desc, parse(f.read(), src))
    # The 404 page is served at any missing path, so it needs an absolute base.
    # Set SITE_BASE if the site moves (for example to a custom domain: "/").
    base = os.environ.get("SITE_BASE", "/legacy-global-test-site/")
    if not base.startswith("/"):
        raise SystemExit("SITE_BASE must start with '/'. Got %r; on Git Bash set MSYS_NO_PATHCONV=1." % base)
    build_page("404.html", "Page not found | Legacy Global", "Page not found.", parse(NOT_FOUND, "404"), base)


main()
