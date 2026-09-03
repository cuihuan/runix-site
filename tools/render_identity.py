#!/usr/bin/env python3
"""Bake the company's legal identity into the static footer of every page.

Card acquirers do not take "it's in the JavaScript" for an answer. Airwallex's
payment-method onboarding requires the site to *display* company name, business
registration number and contact details — address, email and phone — and a
reviewer may well read the page with scripts off, or read the HTML source
directly. site-config.js injects those values at runtime, which is the right
single source of truth but the wrong delivery mechanism for a compliance check.

So the values live in assets/site-config.js and this script renders them into
the markup between paired comment markers. Change the config, re-run this, and
every page agrees — without the config stopping being the one place a value is
written down. Four blocks, plus the Organization JSON-LD:

    <!--identity-->          the legal line above the footer bar, every page
    <!--identity-contact-->  the address and phone rows on /about#contact
    <!--identity-facts-->    the registration row in /about "Company facts"
    <!--identity-terms-->    "who you are contracting with", in /terms

The footer block is inserted automatically on any page with a footer bar; the
other three are only rendered where the marker already exists. The Organization
block on the homepage is patched as JSON — see patch_org_schema.

Missing values are skipped, never placeholdered. A footer that says
"Company No. [TBD]" is worse than one that doesn't mention a company number:
the first looks like an unfinished site, the second looks like a site that
hasn't published that detail yet.

Usage:
    python3 tools/render_identity.py            # report only
    python3 tools/render_identity.py --write    # rewrite the pages
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(ROOT, "assets", "site-config.js")

# Where the block goes when a page does not have it yet: immediately before the
# footer's bottom bar, so it reads as part of the legal line rather than as a
# separate section someone bolted on.
ANCHOR = '    <div class="footer-bottom">'


def read_config():
    """Pull the identity fields out of site-config.js.

    Parsing JS with a regex is normally a bad idea; here the target is a flat
    object of string-or-null literals written by hand in a file this repo owns,
    and the alternative — a JSON sidecar — would split the single source of
    truth in two. The regex only matches `key: "value"` / `key: null` at the
    top level of that object, and an unparseable field comes back as None,
    which the renderer already handles by omitting it.
    """
    src = open(CONFIG, encoding="utf-8").read()
    out = {}
    for key in (
        "legalCompanyName",
        "registrationJurisdiction",
        "registrationNumber",
        "businessAddress",
        "businessPhone",
        "supportEmail",
        "industry",
    ):
        m = re.search(r'^\s*%s:\s*(null|"((?:[^"\\]|\\.)*)")' % key, src, re.M)
        out[key] = None if not m or m.group(1) == "null" else m.group(2)
    return out


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def tel_link(phone):
    # Non-breaking spaces: the number split "+1 (308)" / "689-0770" at 1024px.
    return '<a href="tel:%s">%s</a>' % (re.sub(r"[^+\d]", "", phone), esc(phone).replace(" ", "&nbsp;"))


def mail_link(addr):
    a = esc(addr)
    return '<!--email_off--><a href="mailto:%s">%s</a><!--/email_off-->' % (a, a)


def render_footer(cfg):
    """One line, in the order a reviewer scans for it: who, registered where,
    registered as what number, reachable at which address, phone and email."""
    parts = []
    if cfg["legalCompanyName"]:
        parts.append("<strong>%s</strong>" % esc(cfg["legalCompanyName"]))
    if cfg["registrationJurisdiction"]:
        parts.append("Registered in %s" % esc(cfg["registrationJurisdiction"]))
    if cfg["registrationNumber"]:
        parts.append("Company No. %s" % esc(cfg["registrationNumber"]))
    if cfg["businessAddress"]:
        parts.append(esc(cfg["businessAddress"]))
    if cfg["businessPhone"]:
        parts.append(tel_link(cfg["businessPhone"]))
    if cfg["supportEmail"]:
        parts.append(mail_link(cfg["supportEmail"]))
    if not parts:
        return ""
    # Each separator is glued to the token after it, so a line can end on a value
    # but never on a stranded middot (it travelled with the email at 1440, with
    # "United States" at 375).
    return '    <address class="footer-identity">%s</address>\n' % " &middot;&nbsp;".join(parts)


def render_contact(cfg):
    """The rows /about#contact adds once there is a postal address and a line to
    call. Absent values produce no row at all — an "Address" label with nothing
    beside it reads as a bug, not as a detail withheld."""
    rows = []
    if cfg["businessAddress"]:
        rows.append(
            '        <div class="row"><span class="k">Address</span><span>%s</span></div>'
            % esc(cfg["businessAddress"])
        )
    if cfg["businessPhone"]:
        rows.append(
            '        <div class="row"><span class="k">Phone</span><span>%s</span></div>'
            % tel_link(cfg["businessPhone"])
        )
    return ("\n".join(rows) + "\n") if rows else ""


def render_terms(cfg):
    """Who the counterparty on the contract actually is, in the Terms themselves.
    A reader who has got as far as the governing-law clause is the reader most
    likely to want the registration number next to it."""
    bits = []
    who = cfg["legalCompanyName"] or "The company"
    where = cfg["registrationJurisdiction"]
    sentence = "%s is a company incorporated in %s" % (esc(who), esc(where)) if where else esc(who)
    if cfg["registrationNumber"]:
        sentence += " under company number %s" % esc(cfg["registrationNumber"])
    if cfg["businessAddress"]:
        sentence += ", with its registered office at %s" % esc(cfg["businessAddress"])
    bits.append(sentence + ".")
    reach = []
    if cfg["supportEmail"]:
        reach.append(mail_link(cfg["supportEmail"]))
    if cfg["businessPhone"]:
        reach.append(tel_link(cfg["businessPhone"]))
    if reach:
        bits.append("You can reach us at %s." % " or ".join(reach))
    return "  <p>%s</p>\n" % " ".join(bits)


def render_facts(cfg):
    """The "Company facts" rows: the registration number, and the industry the
    business declares — the latter so a payment provider can match the site
    against the industry on an application without inferring it from prose."""
    rows = []
    if cfg["registrationNumber"]:
        rows.append(
            '        <div class="frow"><span class="k">Registration</span>'
            '<span class="v">%s<small>%s</small></span></div>'
            % (
                esc(cfg["registrationNumber"]),
                esc(cfg["registrationJurisdiction"] or "Company registration number"),
            )
        )
    if cfg["industry"]:
        rows.append(
            '        <div class="frow"><span class="k">Industry</span>'
            '<span class="v">%s<small>Software development, cloud computing and AI '
            "infrastructure services</small></span></div>" % esc(cfg["industry"])
        )
    return ("\n".join(rows) + "\n") if rows else ""


# marker name -> (renderer, indent, anchor to insert before when absent)
BLOCKS = {
    "identity": (render_footer, "    ", ANCHOR),
    "identity-contact": (render_contact, "        ", None),
    "identity-facts": (render_facts, "        ", None),
    "identity-terms": (render_terms, "  ", None),
}


US_ADDRESS = re.compile(
    r"^(?P<street>.+?),\s*"
    r"(?P<locality>[^,]+),\s*"
    r"(?P<region>[A-Z]{2})\s+(?P<postal>\d{5}(?:-\d{4})?)"
    r"(?:,\s*(?P<country>.+))?$"
)


def split_us_address(one_line):
    """Break a US address into PostalAddress fields, or don't.

    The config holds one display line, because that is what a footer prints.
    Structured data wants it in parts, and a validator flags a PostalAddress
    whose entire address sits in streetAddress with no addressLocality. This
    only splits what unambiguously matches "street, city, ST 12345[, country]"
    — anything else (a non-US address, a PO box line, a second suite line)
    falls back to the whole string in streetAddress, which is imprecise but
    never wrong.
    """
    m = US_ADDRESS.match(one_line.strip())
    if not m:
        return {"streetAddress": one_line}
    out = {
        "streetAddress": m.group("street"),
        "addressLocality": m.group("locality"),
        "addressRegion": m.group("region"),
        "postalCode": m.group("postal"),
    }
    if m.group("country"):
        out["addressCountry"] = "US" if m.group("country").strip() in (
            "United States", "USA", "US", "United States of America",
        ) else m.group("country").strip()
    return out


def patch_org_schema(src, cfg):
    """Keep the Organization JSON-LD in step with the same three values.

    Structured data is not what an acquirer reads, but it is what everything
    else reads — and an Organization block that omits the phone and street
    address while the footer prints them is exactly the kind of disagreement
    that makes a site look assembled rather than operated. Edited as JSON, not
    as text, so a value containing a quote cannot corrupt the block.

    Only the page that *defines* the Organization is touched. Every other page
    carries `"publisher": {"@id": ".../#org"}` — a reference, not a definition —
    and an earlier version of this matched those too, which would have
    reformatted the JSON-LD on 51 pages to no purpose. So each block is parsed
    and the type checked before anything is rewritten.
    """
    m = None
    for cand in re.finditer(
        r'<script type="application/ld\+json">\s*(\{.*?\})\s*</script>', src, re.S
    ):
        try:
            parsed = json.loads(cand.group(1))
        except ValueError:
            continue
        if parsed.get("@type") == "Organization" and parsed.get("@id", "").endswith("/#org"):
            m, org = cand, parsed
            break
    if m is None:
        return src

    if cfg["legalCompanyName"]:
        org["legalName"] = cfg["legalCompanyName"]
    if cfg["registrationNumber"]:
        org["identifier"] = {
            "@type": "PropertyValue",
            "name": "Company registration number",
            "value": cfg["registrationNumber"],
        }
    if cfg["businessAddress"]:
        org.setdefault("address", {"@type": "PostalAddress"})
        org["address"].update(split_us_address(cfg["businessAddress"]))
    if cfg["businessPhone"]:
        org["telephone"] = cfg["businessPhone"]
        for cp in org.get("contactPoint", []):
            cp.setdefault("telephone", cfg["businessPhone"])

    return src[: m.start(1)] + json.dumps(org, indent=2, ensure_ascii=False) + src[m.end(1) :]


def apply_to(path, blocks, cfg):
    src = open(path, encoding="utf-8").read()
    src = patch_org_schema(src, cfg)
    for name, (block, indent, anchor) in blocks.items():
        start, end = "<!--%s-->" % name, "<!--/%s-->" % name
        wrapped = "%s%s\n%s%s%s\n" % (indent, start, block, indent, end)
        if start in src:
            # Re-render in place, swallowing the indentation of the old opening
            # marker so repeated runs do not accumulate leading spaces.
            src = re.sub(
                r"[ \t]*" + re.escape(start) + r".*?" + re.escape(end) + r"\n?",
                lambda _: wrapped,
                src,
                flags=re.S,
            )
        elif anchor and anchor in src:
            src = src.replace(anchor, wrapped + anchor, 1)
    return src


def main():
    write = "--write" in sys.argv
    cfg = read_config()
    blocks = {
        name: (renderer(cfg), indent, anchor)
        for name, (renderer, indent, anchor) in BLOCKS.items()
    }

    missing = [k for k in ("registrationNumber", "businessAddress", "businessPhone") if not cfg[k]]
    if missing:
        print("    note: not published yet -> %s" % ", ".join(missing))

    pages = sorted(
        glob.glob(os.path.join(ROOT, "*.html"))
        + glob.glob(os.path.join(ROOT, "*", "*.html"))
    )
    pages = [p for p in pages if os.path.basename(p)[0] != "_"]

    changed = 0
    for path in pages:
        before = open(path, encoding="utf-8").read()
        after = apply_to(path, blocks, cfg)
        if after == before:
            continue
        changed += 1
        if write:
            open(path, "w", encoding="utf-8").write(after)

    verb = "updated" if write else "would update"
    print("    %s %d of %d pages" % (verb, changed, len(pages)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
