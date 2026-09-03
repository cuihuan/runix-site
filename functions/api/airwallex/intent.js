/**
 * Creates an Airwallex payment intent for a prepaid top-up, and returns only
 * what the browser needs to open the hosted checkout page.
 *
 * Why a backend exists at all on a static site: Airwallex hosted checkout needs
 * an intent_id + client_secret pair minted with the merchant API key, and that
 * key cannot live in the page. Payment Links would have avoided this, but that
 * product is not enabled on the account (POST /pa/payment_links/create returns
 * configuration_error on every currency and body shape, while payment_intents
 * returns 201 — so the intent path is the one that works today).
 *
 * AMOUNTS ARE MAJOR UNITS. Verified against the live API: amount 0.5 was
 * accepted and echoed back as 0.5, and amount 10 came back as "10 USD". This is
 * the opposite of Stripe, which takes minor units. Sending cents here would
 * charge 100x. Nothing in this file re-scales the value; it is validated as a
 * major-unit decimal and passed through unchanged.
 *
 * The bounds below are the real enforcement point. The picker on /plans is a
 * hint the shopper can edit in devtools, so the floor and ceiling are checked
 * here, server-side, before an intent is ever minted.
 */

/* MIN_USD mirrors RUNIX.stripe.minUnits in assets/site-config.js and the floor
   configured on the Stripe payment link. Three copies of one business rule; the
   test asserts this one, and moving it means moving all three. */
export const MIN_USD = 10;
export const MAX_USD = 10000;
/* Credits are worth this multiple of what is paid. Stated on /plans as "twice
   what you pay"; carried into metadata so whoever grants the balance by hand
   does not have to recompute it. */
export const CREDIT_MULTIPLE = 2;
const CURRENCY = 'USD';
const API = 'https://api.airwallex.com';

const json = (status, body) =>
  new Response(JSON.stringify(body), {
    status,
    headers: {
      'content-type': 'application/json; charset=utf-8',
      'cache-control': 'no-store',
    },
  });

/** Same-origin only. This endpoint mints objects against a live merchant
 *  account, so it should not be callable from another site's page. */
function sameOrigin(request) {
  const self = new URL(request.url).origin;
  const origin = request.headers.get('origin');
  if (origin) return origin === self;
  // Some browsers omit Origin on same-origin POSTs; fall back to Referer.
  const referer = request.headers.get('referer');
  if (referer) {
    try {
      return new URL(referer).origin === self;
    } catch {
      return false;
    }
  }
  return false;
}

/** Accepts a number or numeric string, rejects anything that is not a plain
 *  amount with at most two decimal places inside the configured range.
 *  Exported so payments/airwallex-intent.test.js can pin the bounds — this is
 *  the only thing standing between a devtools-edited picker and a $0.01 or
 *  $9,000,000 charge. */
export function parseAmount(raw) {
  if (typeof raw !== 'number' && typeof raw !== 'string') return null;
  const s = String(raw).trim();
  if (!/^\d+(\.\d{1,2})?$/.test(s)) return null;
  const n = Number(s);
  if (!Number.isFinite(n)) return null;
  if (n < MIN_USD || n > MAX_USD) return null;
  // Normalise "10.00" -> 10 so the value sent matches what was validated.
  return Math.round(n * 100) / 100;
}

/** Airwallex rejects a non-HTTPS return_url, and `wrangler pages dev` serves
 *  over http, so local runs fall back to the production origin rather than
 *  failing the create outright. */
function returnBase(request) {
  const origin = new URL(request.url).origin;
  return origin.startsWith('https://') ? origin : 'https://runixcloud.io';
}

async function accessToken(env) {
  const r = await fetch(`${API}/api/v1/authentication/login`, {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      'x-client-id': env.AIRWALLEX_CLIENT_ID,
      'x-api-key': env.AIRWALLEX_API_KEY,
    },
    body: '{}',
  });
  if (!r.ok) throw new Error(`auth ${r.status}`);
  const d = await r.json();
  if (!d.token) throw new Error('auth returned no token');
  return d.token;
}

export async function onRequestPost({ request, env }) {
  if (!env.AIRWALLEX_CLIENT_ID || !env.AIRWALLEX_API_KEY) {
    return json(503, { error: 'payments_unconfigured' });
  }
  if (!sameOrigin(request)) return json(403, { error: 'forbidden' });

  let body;
  try {
    body = await request.json();
  } catch {
    return json(400, { error: 'invalid_json' });
  }

  const amount = parseAmount(body && body.amount);
  if (amount === null) {
    return json(400, {
      error: 'invalid_amount',
      message: `Amount must be between ${MIN_USD} and ${MAX_USD} ${CURRENCY}.`,
    });
  }

  try {
    const token = await accessToken(env);
    // A fresh request_id per invocation. Airwallex dedupes retries that reuse
    // one, but nothing here reuses it, so this is NOT end-to-end idempotency:
    // two clicks mint two intents. That is survivable because an unpaid intent
    // costs nothing and expires, and because only one of them can be paid.
    // Real idempotency needs a durable key tied to a cart or an order record,
    // which arrives with the webhook work — see payments/README.md.
    // merchant_order_id is what a human matches against when granting credits.
    const requestId = crypto.randomUUID();
    const r = await fetch(`${API}/api/v1/pa/payment_intents/create`, {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
        authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        request_id: requestId,
        amount,
        currency: CURRENCY,
        merchant_order_id: `topup-${Date.now()}-${requestId.slice(0, 8)}`,
        // Airwallex sends the browser here itself once the payment resolves, so
        // the landing does not depend on the SDK's callback surviving. It must
        // be HTTPS, which the local dev origin is not — hence the fallback.
        // A `descriptor` was sent here previously and silently ignored: the API
        // echoed back the account name ("Runix AI Inc") instead, so it is gone.
        return_url: `${returnBase(request)}/thanks?kind=topup&via=airwallex`,
        // Granting credits is a manual step today. This carries everything the
        // person doing it needs, straight in the provider's own ledger view.
        metadata: {
          kind: 'topup',
          paid_usd: String(amount),
          credits_usd: String(amount * CREDIT_MULTIPLE),
          source: 'plans',
        },
      }),
    });
    const d = await r.json();
    if (!r.ok || !d.id || !d.client_secret) {
      // The provider's error body can carry account-level configuration detail,
      // so it goes to the log and the caller gets a generic code instead.
      console.error('airwallex intent create failed', r.status, JSON.stringify(d));
      return json(502, { error: 'provider_error' });
    }
    return json(200, {
      intent_id: d.id,
      client_secret: d.client_secret,
      currency: d.currency,
      amount: d.amount,
    });
  } catch (e) {
    console.error('airwallex intent exception', e && e.message);
    return json(502, { error: 'provider_error' });
  }
}

/** Anything other than POST, including a curious GET, gets nothing. */
export async function onRequest({ request }) {
  if (request.method === 'POST') return; // handled by onRequestPost
  return json(405, { error: 'method_not_allowed' });
}
