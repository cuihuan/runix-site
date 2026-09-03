#!/usr/bin/env python3
"""Put the failover story on /router as a picture instead of three bullets.

The page asserts "a bad provider hour is not your outage" in prose and then
asks the reader to take it on faith. This draws what actually happens: the
application keeps talking to one base URL while the gateway moves traffic off
a degrading provider and back again.

Everything drawn here is behaviour /docs/router already documents — circuit
breaker on errors, rate limits and timeouts; re-issue to a healthy alternative
under a retry budget; a degraded provider removed from rotation until health
checks pass. No capability is depicted that the docs do not state, and no
number appears anywhere in it.

Inline SVG, so it costs no request and survives the strict CSP. Below 720px it
is replaced by an ordered list of the same steps — a 880-wide diagram scaled
to a phone would render its labels at about 6px, which is worse than no
diagram. Both are in the DOM; exactly one is shown.

Idempotent. Run from the site root.
"""
import os
import pathlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

FIGURE = """
<section class="section">
  <div class="container">
    <div class="section-head center">
      <h2>What a provider's bad hour looks like from your side</h2>
      <p>Your application holds one base URL and one key. Everything below happens behind that line, while the request is still in flight.</p>
    </div>

    <figure class="diagram">
      <svg viewBox="0 0 880 330" role="img" aria-labelledby="fd-t fd-d" class="diagram-svg">
        <title id="fd-t">How Runix Router handles a degrading provider</title>
        <desc id="fd-d">Your application sends every request to one Runix endpoint. Runix watches provider health, trips a circuit breaker when a provider starts erroring, rate-limiting or timing out, and re-issues the request to a healthy provider under a retry budget. The degraded provider returns to rotation once health checks pass.</desc>

        <defs>
          <marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">
            <path d="M0 0 L10 5 L0 10 z" fill="currentColor"/>
          </marker>
        </defs>

        <!-- application -->
        <g class="d-node">
          <rect x="6" y="122" width="168" height="86" rx="12"/>
          <text x="90" y="155" class="d-title">Your application</text>
          <text x="90" y="177" class="d-sub">one base URL</text>
          <text x="90" y="194" class="d-sub">one key</text>
        </g>

        <!-- app to gateway -->
        <g class="d-flow">
          <line x1="180" y1="165" x2="252" y2="165" marker-end="url(#ar)"/>
          <text x="216" y="152" class="d-edge">request</text>
        </g>

        <!-- gateway -->
        <g class="d-node d-gw">
          <rect x="258" y="74" width="212" height="182" rx="12"/>
          <text x="364" y="106" class="d-title">Runix Router</text>
          <g class="d-chip">
            <rect x="278" y="124" width="172" height="30" rx="8"/>
            <text x="364" y="144">health checks</text>
            <rect x="278" y="162" width="172" height="30" rx="8"/>
            <text x="364" y="182">circuit breaker</text>
            <rect x="278" y="200" width="172" height="30" rx="8"/>
            <text x="364" y="220">retry budget</text>
          </g>
        </g>

        <!-- gateway to providers -->
        <g class="d-flow d-ok">
          <path d="M476 150 C 530 150, 540 74, 596 74" marker-end="url(#ar)" fill="none"/>
          <text x="540" y="100" class="d-edge">re-issued here</text>
        </g>
        <g class="d-flow d-down">
          <path d="M476 165 L 596 165" marker-end="url(#ar)" fill="none" stroke-dasharray="5 5"/>
          <g class="d-x">
            <line x1="528" y1="157" x2="544" y2="173"/>
            <line x1="544" y1="157" x2="528" y2="173"/>
          </g>
        </g>
        <g class="d-flow d-idle">
          <path d="M476 182 C 530 182, 540 256, 596 256" marker-end="url(#ar)" fill="none" stroke-dasharray="2 6"/>
        </g>

        <!-- providers -->
        <g class="d-node d-prov">
          <rect x="602" y="46" width="272" height="56" rx="10"/>
          <text x="622" y="70" class="d-title d-left">Healthy provider</text>
          <text x="622" y="89" class="d-sub d-left">serving your traffic</text>
        </g>
        <g class="d-node d-prov d-prov-down">
          <rect x="602" y="137" width="272" height="56" rx="10"/>
          <text x="622" y="161" class="d-title d-left">Degrading provider</text>
          <text x="622" y="180" class="d-sub d-left">errors, 429s or timeouts</text>
        </g>
        <g class="d-node d-prov d-prov-idle">
          <rect x="602" y="228" width="272" height="56" rx="10"/>
          <text x="622" y="252" class="d-title d-left">Standby provider</text>
          <text x="622" y="271" class="d-sub d-left">available if the first choice also fails</text>
        </g>
      </svg>

      <ol class="diagram-steps">
        <li><b>Your application</b> sends every request to one Runix base URL, with one key.</li>
        <li><b>Runix Router</b> tracks provider health, and trips a circuit breaker on errors, rate limits and timeouts.</li>
        <li><b>The degrading provider</b> is taken out of rotation before it drags your latency.</li>
        <li><b>The request is re-issued</b> to a healthy provider under a retry budget, so a retry storm cannot become the second incident.</li>
        <li><b>The provider returns</b> to rotation when health checks pass. Nothing in your application changed.</li>
      </ol>

      <figcaption>Your code never learns any of this happened. The base URL it holds does not change, and no redeploy is involved — which is the point of putting a gateway on the hot path at all.</figcaption>
    </figure>
  </div>
</section>
"""

CSS = """
/* ---------- Failover diagram (/router) ---------- */
.diagram { margin: 0; max-width: 940px; margin-inline: auto; }
.diagram-svg {
  width: 100%; height: auto; display: block;
  border: 1px solid var(--line); border-radius: var(--radius);
  background: var(--bg); padding: 20px 12px;
}
.diagram-svg .d-node rect { fill: var(--bg); stroke: var(--line-2); stroke-width: 1.25; }
.diagram-svg .d-gw rect { fill: var(--bg-alt); stroke: var(--indigo); }
.diagram-svg .d-title {
  font-weight: 700; font-size: 15px; fill: var(--ink); text-anchor: middle;
}
.diagram-svg .d-sub {
  font-weight: 400; font-size: 13px; fill: var(--ink-3); text-anchor: middle;
}
.diagram-svg .d-left { text-anchor: start; }
.diagram-svg .d-chip rect { fill: var(--bg); stroke: var(--line-2); stroke-width: 1; }
.diagram-svg .d-chip text {
  font: 600 13px/1 var(--mono); fill: var(--ink-2); text-anchor: middle;
  letter-spacing: 0.02em;
}
.diagram-svg .d-flow { color: var(--ink-3); }
.diagram-svg .d-flow line, .diagram-svg .d-flow path {
  stroke: currentColor; stroke-width: 1.5;
}
.diagram-svg .d-edge {
  font: 600 12px/1 var(--mono); fill: var(--ink-3); text-anchor: middle;
  letter-spacing: 0.04em; text-transform: uppercase;
}
.diagram-svg .d-ok { color: var(--cyan-text); }
.diagram-svg .d-ok .d-edge { fill: var(--cyan-text); }
.diagram-svg .d-down, .diagram-svg .d-idle { color: var(--ink-4, #9aa3af); }
.diagram-svg .d-x line { stroke: #c2410c; stroke-width: 2; stroke-linecap: round; }
.diagram-svg .d-prov-down rect { stroke-dasharray: 5 4; }
.diagram-svg .d-prov-idle rect, .diagram-svg .d-prov-idle text { opacity: 0.62; }

.diagram-steps {
  display: none; margin: 0; padding-left: 22px;
  border: 1px solid var(--line); border-radius: var(--radius);
  background: var(--bg); padding: 22px 22px 22px 42px;
}
.diagram-steps li { margin: 0 0 12px; color: var(--ink-2); line-height: 1.6; }
.diagram-steps li:last-child { margin-bottom: 0; }
.diagram-steps b { color: var(--ink); font-weight: 600; }

.diagram figcaption {
  margin-top: 16px; color: var(--ink-3); font-size: 14.5px; line-height: 1.6;
  text-align: center; max-width: 640px; margin-inline: auto;
}

/* A 880-wide drawing on a phone puts its labels at about 6px. Below that, the
   ordered list says the same thing at a readable size. */
@media (max-width: 719px) {
  .diagram-svg { display: none; }
  .diagram-steps { display: block; }
  .diagram figcaption { text-align: left; }
}
"""

page = pathlib.Path("router.html")
html = page.read_text()
if 'class="diagram"' in html:
    print("  /router already has the diagram")
else:
    anchor = '<section class="section">\n  <div class="container">\n    <div class="section-head center">\n      <h2>Common questions</h2>'
    assert anchor in html, "could not find the questions section to insert before"
    page.write_text(html.replace(anchor, FIGURE.strip() + "\n\n" + anchor, 1))
    print("  /router: diagram inserted before the questions section")

css = pathlib.Path("assets/style.css")
s = css.read_text()
if ".diagram-svg" in s:
    print("  style.css already carries the diagram styles")
else:
    css.write_text(s + CSS)
    print("  style.css: diagram styles appended")
