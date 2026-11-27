# Runix Lab design standard

Version 6, 2026-11-27. This file is the standard; `assets/style.css` is its
implementation and `tools/design_lint.py` is its enforcement. `deploy.sh`
refuses to ship a stylesheet that breaks a rule the lint can check, so a rule
written here without a check is a wish, and the rules below say which is which.

The site sells infrastructure to engineers and the people who sign for them.
The design has one job: make a dense, literal page easy to read and easy to
trust. It borrows from people who solved that problem before us, and each
borrowing below ends in a rule that can be checked.

## 1. Principles, and the rule each one becomes

| Source | Idea | Rule on this site |
|---|---|---|
| Dieter Rams, *Ten principles for good design* (no. 10: "as little design as possible") | Less, but better | Every element does one job. A page states a product's layer and status once (the product bar), not in a bar, a chip and a badge. No decorative badges, no gradients on text, no icons that repeat their label. |
| Josef Müller-Brockmann, *Grid Systems in Graphic Design* (Swiss / International Typographic Style) | The grid carries the page; hierarchy comes from size and position, not ornament | One 1200px container, 24px gutters, flush-left text. Centred text is allowed in exactly two places: the home hero and the closing call-to-action band. |
| Robert Bringhurst, *The Elements of Typographic Style* (modular scale) | Sizes come from a scale, like notes from a key | Twelve font sizes (section 3). No other size may appear in the stylesheet. **Checked.** |
| Gestalt psychology (proximity, common region) | Things close together read as one group | Spacing comes from a 4px scale, and the gap inside a group is always smaller than the gap between groups: label to title 12, title to lede 16, block to block 48, section to section 96 (64 under 920px). |
| Edward Tufte, *The Visual Display of Quantitative Information* (data-ink ratio) | Every drop of ink should carry data | Tables use hairlines only: no zebra stripes, no filled headers, no vertical rules. Numbers are tabular. Diagrams have no shadows. |
| Jakob Nielsen, *10 usability heuristics* (no. 4: consistency and standards) | The same thing looks the same everywhere | One component per job, one look per component, on every page and in both languages. Tokens only. **Checked.** |
| Doug McIlroy, the Unix philosophy | Do one thing well; compose | Components are small and single-purpose (a label, a card, a chip) and pages are compositions of them. It is also the brand: the stack is drawn the way Unix is described, one layer per idea. |
| W3C, *WCAG 2.2* level AA | Readable by everyone | Text contrast 4.5:1 (3:1 at 24px and up), targets 24px, nothing under 12px, every page works with JavaScript off. **Checked** (`check_contrast.cjs`, `visual_qa.py`, `nojs_check.py`). |

## 2. Colour

Colour is a signal, not decoration. There are three signals and a neutral ramp.

| Token | Value | Use, and only this use |
|---|---|---|
| `--ink` | #0d1117 | Headings, primary text, the primary button |
| `--ink-2` | #48505e | Body copy, ledes |
| `--ink-3` | #676f7b | Meta text, structural labels, table row heads |
| `--ink-meta` | #5b636f | Meta text on a tinted surface, where `--ink-3` measures under 4.5:1 |
| `--ink-4` | #8a919c | Disabled and decorative strokes only, never text |
| `--bg`, `--surface` | #ffffff | Page and card background |
| `--bg-alt` | #f5f5f7 | Alternate section band |
| `--line`, `--line-2` | 7% and 11% ink | Hairlines; `--line-2` for card borders |
| `--indigo` / `--indigo-ink` | #4a5bd6 / #3c49ad | **Accent:** links, section numbers, eyebrows, the "New" tag. `--indigo-ink` on tinted surfaces |
| `--cyan-text` | #08748d | **State: live.** The "available" status and its dot, a "yes" in a table. Never a label |
| `--danger`, `--warn` | #b3261e, #c2410c | **State: error, warning.** Form errors, a failed node in a diagram |
| `--panel` and `--on-panel-*` | #0b0e14 and four greys | The dark surfaces: code samples, the compute plinth, the closing band |
| `--code-*` | three hues | Syntax colours inside `--panel` only |

Rules:
- No raw colour value outside `:root`. **Checked** (hex; `rgba()` tints are the
  known exception, listed in section 9).
- A label (mono caps) is `--indigo-ink` when it numbers or introduces a
  section, `--ink-3` when it names a structure (a table, a menu group, a footer
  column). Cyan is never a label colour. **Checked for the classes in section 6.**

## 3. Type

Face: Archivo (self-hosted, 400 to 800), system mono for code and labels. For
Chinese, the platform's own CJK face (PingFang SC, Hiragino Sans GB,
Microsoft YaHei, Noto Sans CJK SC), section 8.

The scale, roughly a major third from 12 to 60, rounded to whole pixels:

| Token | Size | Use |
|---|---|---|
| `--text-2xs` | 12px | Mono labels, status, tags. The floor: nothing is smaller |
| `--text-xs` | 13px | Meta, captions, menu descriptions, code inside tables |
| `--text-sm` | 14px | UI text: nav, buttons, tables, chips |
| `--text-md` | 15px | Card body, dense prose |
| `--text-base` | 16px | Body |
| `--text-lg` | 18px | Ledes, card titles |
| `--text-xl` | 20px | Small section titles |
| `--text-2xl` | 24px | h3 |
| `--text-3xl` | 30px | h2 under 920px |
| `--text-4xl` | 38px | Page h1 under 920px, product h1 on a phone |
| `--text-5xl` | 48px | h2, page h1 |
| `--text-6xl` | 60px | Product h1 |
| `--text-display` | clamp(42px, 5.8vw, 80px) | The home h1 only |

Rules:
- Only these sizes. **Checked**, including inside `font:` shorthands and inline styles.
- One display weight (`--display-weight`, 640) for every headline; 600 to 650
  for titles inside components; 400 body.
- Tracking from six values: `--track-display` (-0.035em), `--track-heading`
  (-0.025em), `--track-title` (-0.015em), `0`, `--track-caps` (0.04em, small
  mono), `--track-label` (0.08em, mono caps labels). **Checked.**
- Sentence case for every heading and button. Caps only on mono labels of
  one to three words.
- Headings balance (`text-wrap: balance`), paragraphs avoid a one-word last line
  (`text-wrap: pretty`); `layout_qa.py` fails a heading, label or button that
  strands a word. **Checked.**

## 4. Space, shape, depth

- Spacing steps: 4, 8, 12, 16, 20, 24, 32, 40, 48, 64, 96. Section padding is
  96px, 64px under 920px, 48px under 560px.
- Radius: `--radius-xs` 6px (inline chips inside text, code), `--radius-sm`
  10px (buttons inside cards, small panels, code windows), `--radius` 14px
  (cards, menus, tables), `--radius-lg` 20px (the one large framed figure per
  page: the stack board, a hero panel), `--radius-pill` (buttons, chips, tags),
  `50%` (dots). **Checked.**
- Depth: hairlines carry structure. A shadow is allowed only on something that
  floats over the page (the Products menu, the at-a-glance panel, a code
  window): `--shadow` or `--shadow-float`. Cards in a grid have no shadow.
- Breakpoints: 560px (phone), 920px (tablet), 1200px (wide). `max-width` uses
  the number, `min-width` the number plus one. **Checked.**

## 5. Layout

- Three hero shapes and no others: **centred** (home), **split** (product and
  layer pages: copy left, at-a-glance panel right), **left** (every other page:
  eyebrow, h1, lede, optional actions).
- Section head: optional numbered label, h2, optional lede. Two columns on a
  wide screen (h2 left, lede right), **both aligned to the top**; one column
  under 920px. A lede longer than about 60 words goes under the h2 instead.
- Rows of cards are one height; the last line of each card (status, link)
  sits on the bottom edge. **Checked** (`layout_qa.py`, 3px tolerance).

## 6. Components

| Component | Spec |
|---|---|
| Header | 64px, sticky, translucent white. Brand left; Products menu, Solutions, Pricing, Docs, Company, the language link (once the Chinese edition is live, `i18n.ZH_LIVE`); one primary action ("Contact sales") right. |
| Products menu | One row per layer: a 160px label column (`05 AGENTS`), then products two to a row. A layer's hub link ("Agents by domain") is a full-width row under that layer's products, never in the label column, so every row is as tall as its products and no taller. Footer link "The whole stack". |
| Product bar | Under the header on product and hub pages: name, layer, status, section links, the page's own primary action. It is where layer and status are stated; the hero does not repeat them. A bar whose action is the same as the header's ("Contact sales") omits it. |
| Label | `font: 600 var(--text-2xs)/1.3 var(--mono)`, `--track-label`, uppercase. Section numbers `02 · Capabilities` are labels. |
| Status | Three literal states, one look each: **available** (cyan, with a dot), **early access** (indigo), **in development** (ink-3). The qualifier under it ("by engagement") is ink-3 lower case. The words come from `tools/stack.py` and nowhere else. |
| Button | Pill. Primary: ink fill, white text, hover `--ink-hover`. Secondary: white with a `--line-2` border. 44px tall, 36px in bars. One primary per view. |
| Card | `--surface`, 1px `--line-2`, `--radius`, padding 28px (24px under 560px), no shadow. Title `--text-lg` 650, body `--text-md` `--ink-2`, link last and on the bottom edge. |
| Chip | Pill, 1px `--line-2`, `--text-sm`. A chip that is a link says so with an arrow. |
| Tag | "New": mono `--text-2xs`, indigo on a 8% indigo tint, pill. At most one per product. |
| Code window | `--panel`, `--radius-sm`, a title bar with the command's purpose. Code is never cut off at 1440px (`code_overflow.py`). |
| Table | Hairlines only, row heads `--ink-3`, wrapped for horizontal scroll on a phone. |

## 7. Writing

The voice is literal, and the design keeps it that way (see `PRODUCT.md`):
statuses are the words in `stack.py`; no invented figures, customers or
service levels; a number on the page links to where it came from; no em
dashes in published copy. Headlines name the thing ("The AI file system for
object storage"), they do not tease it.

## 8. Two languages

`runixcloud.io` is English, `runixcloud.com` is Chinese, and they are the same
site: the same HTML, the same stylesheet, the same builders. `tools/build_cn.py`
renders the Chinese edition from the English pages and the string catalog in
`i18n/zh-CN.json`; a page ships in Chinese only when every string on it is
translated, so an English change cannot drift silently (see `i18n/README.md`).

Chinese typography rules, applied under `:lang(zh)`:
- System CJK face stack; Archivo still sets Latin words and numbers.
- No negative tracking on headings (it collides CJK glyphs); headings at the
  same size and weight.
- Body line height 1.8, headings 1.3.
- `word-break: auto-phrase` so lines break between words, not inside them.
- No italics. Full-width punctuation. A space between Chinese and Latin text or
  numbers (`Runix FS 是一个文件系统`), as the Chinese copywriting guidelines ask.
- Mono labels are not upper-cased words in Chinese; they keep their numbers
  (`02 · 能力`).

## 9. Known debt (not yet checked)

- `rgba()` tints are written inline (about 60). They should become tokens.
- Spacing values are not linted; the scale in section 4 is followed by
  convention.
- `style.css` is still ordered by when each pass landed, not by component.
  Reordering it is a pure refactor and should be done as one change with
  `visual_qa.py` before and after.
