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

export const MIN_USD = 10;
export const MAX_USD = 10000;
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
    // request_id makes the create idempotent from Airwallex's side if the
    // network retries; merchant_order_id is what shows up in reconciliation,
    // which is how credits actually get granted today (manually, against the
    // Airwallex ledger) — so it has to be something a human can match up.
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
        descriptor: 'Runix credits',
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
