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
    // Stated on /about so a payment provider can match the site against the
    // industry declared in an application. Keep the two identical — a website
    // whose nature disagrees with the declared industry is a rejection reason
    // in its own right, independently of anything else being wrong.
    industry: "Software / SaaS — AI infrastructure",

    // --- Business identification (published in the footer of every page) ---
    // Card acquirers require a website to display company name, business
    // registration number and contact details (address, email, phone) —
    // Airwallex checks all three before enabling a payment method.
    //
    // Never invent one: a wrong filing number is worse than a missing one, and
    // the renderer hides whatever is null rather than printing a placeholder.
    // After changing any of these, run `python3 tools/render_identity.py --write`
    // so the values are baked into the static markup (they must be visible
    // with JavaScript disabled, which is how a reviewer may fetch the page).
    // deploy.sh runs it for you.
    registrationNumber: "2026-002036618",   // WY filing ID, as printed on the certificate
    businessAddress: "30 N Gould St Ste R, Sheridan, WY 82801, United States",
    businessPhone: "+1 (308) 689-0770",     // display form; the tel: link is derived, digits only
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

    // Stripe Buy Button — Stripe-hosted checkout embedded in the top-up card.
    //
    // buyButtonId stays null until a button exists whose Price is ONE-TIME.
    // The first button created for this site was a $98/month subscription, and
    // /pricing states in three places that there is no subscription and no
    // monthly fee; shipping it would have contradicted the page's own billing
    // terms, which is the kind of inconsistency a customer quotes back during a
    // dispute. Nothing renders while this is null — same rule as every other
    // unconfirmed field here.
    //
    // The Price this points at must be $1.00/unit with adjustable quantity, not
    // a fixed amount: the page offers $10/$20/$50/$200 and a free-form box, so a
    // fixed-amount button would charge something other than what the visitor
    // picked. $1.00/unit is also exactly what the gateway's own integration
    // requires (STRIPE-ROLLOUT.md §4.6 — quota = quantity × QuotaPerUnit), so
    // one Price serves both and there is no second object to keep in step.
    //
    // publishableKey is Stripe's publishable (pk_) key, the class Stripe
    // documents as intended for client-side markup. Committing it here is the
    // documented usage, unlike an sk_ secret key, which must not appear in this
    // repository or in any page it serves.
    stripe: {
      publishableKey: "pk_live_51U2k7U3NBFXLsdrEVMDZdbW1o4DTYEGcvGCzz12vhrdjWNHtZOYKytU1u6LbJ9CRGG5eVF7qARknLca32CcKWgO100wlqnLwLz",
      buyButtonId: null,
      minUnits: 10
    },

    // --- Site ---
    domain: "runixcloud.io",
    siteUrl: "https://runixcloud.io",
    foundedYear: 2026,

    // --- Feature flags: keep the UI honest about what actually exists ---
    // When false, related CTAs route to "contact / request access" instead of
    // pretending a self-serve flow is live.
    features: {
      selfServeSignup: false,     // no account system yet -> "Get started" = contact/apply
      // Two live hosted checkouts ship on /plans: a Stripe payment link, and
      // Airwallex via functions/api/airwallex/intent.js. Left true so nothing
      // downstream reroutes a working checkout to a contact form. Note the
      // Stripe Buy Button below is a separate, still-unconfigured path — this
      // flag describes whether a checkout exists, not which mechanism.
      hostedCheckout:  true,
      apiConsole:      false,     // no dashboard yet
      docs:            false,     // developer docs not published yet
      statusPage:      false      // status page not published yet
    }
  };

  window.RUNIX = RUNIX;

  // Lightweight injector (runs after DOM parse). Opt-in only:
  //   <span data-cfg="legalCompanyName"></span>
  //   <a data-cfg-mail="supportEmail"></a>
  //   <a data-cfg-tel="businessPhone"></a>
  //   <div data-cfg-row="businessAddress">      <- removed entirely when null,
  //                                                so a contact table never
  //                                                shows an empty "Address" row
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
    document.querySelectorAll("[data-cfg-tel]").forEach(function (el) {
      var v = RUNIX[el.getAttribute("data-cfg-tel")];
      if (!v) return;
      el.setAttribute("href", "tel:" + v.replace(/[^+\d]/g, ""));
      if (!el.textContent.trim()) el.textContent = v;
    });
    document.querySelectorAll("[data-cfg-row]").forEach(function (el) {
      if (!RUNIX[el.getAttribute("data-cfg-row")] && el.parentNode) {
        el.parentNode.removeChild(el);
      }
    });
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", inject);
  } else {
    inject();
  }
})();

/* ---------------------------------------------------------------------------
 * Stripe Buy Button.
 *
 * Renders only when RUNIX.stripe.buyButtonId is set. When it is null this
 * removes the container from the DOM instead of leaving it empty, so an
 * unconfigured button does not leave a heading behind for a payment method that
 * is not connected — the same rule the config injector applies to unconfirmed
 * identity fields.
 *
 * The third-party script is requested only on a page that has the container AND
 * a configured id, so pages without checkout make no request to js.stripe.com.
 *
 * CSP: script-src / frame-src / connect-src / img-src / form-action in _headers
 * already list the Stripe and Link origins this needs, including
 * merchant-ui-api.stripe.com, which the button calls for its own configuration
 * before it will render anything.
 * ------------------------------------------------------------------------- */
(function () {
  var SCRIPT_SRC = "https://js.stripe.com/v3/buy-button.js";

  function render() {
    var hosts = document.querySelectorAll("[data-stripe-buy-button]");
    if (!hosts.length) return;

    var cfg = (window.RUNIX && window.RUNIX.stripe) || {};
    if (!cfg.buyButtonId || !cfg.publishableKey) {
      hosts.forEach(function (host) {
        if (host.parentNode) host.parentNode.removeChild(host);
      });
      return;
    }

    if (!document.querySelector('script[src="' + SCRIPT_SRC + '"]')) {
      var s = document.createElement("script");
      s.src = SCRIPT_SRC;
      s.async = true;
      document.head.appendChild(s);
    }

    hosts.forEach(function (host) {
      var btn = document.createElement("stripe-buy-button");
      btn.setAttribute("buy-button-id", cfg.buyButtonId);
      btn.setAttribute("publishable-key", cfg.publishableKey);
      // Carries a value back on the Checkout Session as client_reference_id.
      // Left unset here because this static page has no account context to put
      // in it; the gateway sets its own order number on the sessions it creates.
      var ref = host.getAttribute("data-client-reference-id");
      if (ref) btn.setAttribute("client-reference-id", ref);
      host.appendChild(btn);
      host.removeAttribute("hidden");
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", render);
  } else {
    render();
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
