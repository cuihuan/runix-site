/*
 * Runix — single source of truth for company + business configuration.
 *
 * RULES (do not violate):
 *  - Only put CONFIRMED, verifiable values here. Never fabricate a company
 *    registration number, address, EIN, tax id, certification, partner, or
 *    payment-provider relationship.
 *  - Fields whose value is not yet confirmed for PUBLIC display are set to
 *    null. UI must hide null fields — never render a placeholder like
 *    "[COMPANY NUMBER]" to a real visitor.
 *  - Prices, statement descriptor, and provider names must come from here (or
 *    a backend), not be hardcoded across pages.
 *
 * Loaded on every page as a plain global (no build step). Access via
 * `window.RUNIX`. A tiny injector below fills elements that opt in with
 * data-cfg / data-cfg-mail attributes, so footers/contact links stay in sync.
 */
(function () {
  var RUNIX = {
    // --- Identity (confirmed, safe to display) ---
    legalCompanyName: "Runix AI Inc",
    tradingName: "Runix",
    registrationJurisdiction: "Wyoming, United States",

    // --- Confirmed but NOT yet published publicly ---
    // Real values exist in the company's incorporation documents. Left null
    // here on purpose: do not display a registration number / street address
    // publicly until the owner explicitly approves it. Do NOT invent one.
    registrationNumber: null,     // e.g. set to the WY filing number when approved for display
    businessAddress: null,        // registered-office address, when approved for display
    // EIN / tax id is intentionally absent — it must never appear on the site.

    // --- Contact (addresses route to the owner's inbox via Cloudflare Email Routing) ---
    contactEmail: "contact@runixcloud.io",
    supportEmail: "support@runixcloud.io",
    salesEmail:   "sales@runixcloud.io",
    billingEmail: "billing@runixcloud.io",
    privacyEmail: "privacy@runixcloud.io",
    legalEmail:   "legal@runixcloud.io",

    // --- Commerce (fill/confirm before enabling checkout) ---
    statementDescriptor: null,    // what shows on a customer's card statement — set once a processor is live
    defaultCurrency: "USD",

    // --- Site ---
    domain: "runixcloud.io",
    siteUrl: "https://runixcloud.io",
    foundedYear: 2026,

    // --- Feature flags: keep the UI honest about what actually exists ---
    // When false, related CTAs route to "contact / request access" instead of
    // pretending a self-serve flow is live.
    features: {
      selfServeSignup: false,     // no account system yet -> "Get started" = contact/apply
      hostedCheckout:  false,     // no live payment processor connected yet
      apiConsole:      false,     // no dashboard yet
      docs:            false,     // developer docs not published yet
      statusPage:      false      // status page not published yet
    }
  };

  window.RUNIX = RUNIX;

  // Lightweight injector (runs after DOM parse). Opt-in only:
  //   <span data-cfg="legalCompanyName"></span>
  //   <a data-cfg-mail="supportEmail"></a>
  function inject() {
    document.querySelectorAll("[data-cfg]").forEach(function (el) {
      var v = RUNIX[el.getAttribute("data-cfg")];
      if (v) el.textContent = v;
    });
    document.querySelectorAll("[data-cfg-mail]").forEach(function (el) {
      var v = RUNIX[el.getAttribute("data-cfg-mail")];
      if (!v) return;
      el.setAttribute("href", "mailto:" + v);
      if (!el.textContent.trim()) el.textContent = v;
    });
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", inject);
  } else {
    inject();
  }
})();

/* ---------------------------------------------------------------------------
 * Copy buttons on code blocks.
 *
 * The whole integration pitch is "change one base URL", so the base URL and the
 * curl example are the highest-frequency thing anyone does on this site. Making
 * them selectable-by-eye and copyable-by-hand was the only option until now.
 * ------------------------------------------------------------------------- */
(function () {
  function attach(target, source) {
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "copy-btn";
    btn.textContent = "Copy";
    btn.setAttribute("aria-label", "Copy code to clipboard");
    btn.addEventListener("click", function () {
      var text = (source.innerText || source.textContent || "").trim();
      var done = function () {
        btn.textContent = "Copied";
        btn.classList.add("done");
        setTimeout(function () {
          btn.textContent = "Copy";
          btn.classList.remove("done");
        }, 1500);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done, function () {});
        return;
      }
      var ta = document.createElement("textarea");   // older browsers
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      try { document.execCommand("copy"); done(); } catch (e) {}
      document.body.removeChild(ta);
    });
    target.appendChild(btn);
  }

  document.querySelectorAll(".code-card").forEach(function (card) {
    var bar = card.querySelector(".bar");
    var pre = card.querySelector("pre");
    if (bar && pre) attach(bar, pre);
  });
  document.querySelectorAll(".article pre").forEach(function (pre) {
    attach(pre, pre);
  });
})();

/* Mobile navigation.
   This lived in an onclick attribute on every page — 48 copies of the same
   three statements, and the single thing standing between this site and a
   Content-Security-Policy without 'unsafe-inline'. Delegated from the document
   so it does not depend on when this file loads relative to the markup. */
document.addEventListener("click", function (event) {
  var toggle = event.target.closest && event.target.closest(".nav-toggle");
  if (!toggle) return;
  var links = document.querySelector(".nav-links");
  if (!links) return;
  var open = links.classList.toggle("open");
  toggle.setAttribute("aria-expanded", open ? "true" : "false");
});
