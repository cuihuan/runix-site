// Money — safe money handling for the Runix commerce layer.
//
// Rules:
//  - Amounts are ALWAYS integers in the currency's minor unit (e.g. cents for
//    USD, so $10.00 === 1000). Never use floats for money.
//  - Every amount carries its currency. Cross-currency math throws.
//  - This module is pure (no I/O, no secrets). It is safe to unit-test and to
//    reuse on a server. It must NOT handle card data.

/** @typedef {{ amount: number, currency: string }} Money */

// Minor-unit exponent per ISO 4217 currency. Extend as needed.
const EXPONENTS = { USD: 2, EUR: 2, GBP: 2, CNY: 2, AUD: 2, CAD: 2, JPY: 0, KRW: 0 };

/** Number of minor units in one major unit for a currency (default 2). */
export function exponent(currency) {
  assertCurrency(currency);
  return currency in EXPONENTS ? EXPONENTS[currency] : 2;
}

function assertCurrency(currency) {
  if (typeof currency !== "string" || !/^[A-Z]{3}$/.test(currency)) {
    throw new TypeError(`Invalid currency code: ${JSON.stringify(currency)}`);
  }
}

function assertInteger(amount) {
  if (!Number.isInteger(amount)) {
    throw new TypeError(`Money amount must be an integer minor-unit value, got ${amount}`);
  }
}

/** Construct a Money from an integer minor-unit amount. */
export function money(amount, currency) {
  assertInteger(amount);
  assertCurrency(currency);
  return { amount, currency };
}

/** Parse a decimal major-unit string ("10.00") into Money, exactly (no float). */
export function fromDecimalString(value, currency) {
  assertCurrency(currency);
  const exp = exponent(currency);
  const m = /^(-)?(\d+)(?:\.(\d+))?$/.exec(String(value).trim());
  if (!m) throw new TypeError(`Cannot parse money value: ${JSON.stringify(value)}`);
  const sign = m[1] ? -1 : 1;
  const whole = m[2];
  const frac = (m[3] || "").padEnd(exp, "0");
  if (frac.length > exp) {
    throw new RangeError(`Value ${value} has more precision than ${currency} allows (${exp} dp)`);
  }
  const minor = Number(whole) * 10 ** exp + (exp ? Number(frac) : 0);
  return money(sign * minor, currency);
}

function same(a, b) {
  if (a.currency !== b.currency) {
    throw new Error(`Currency mismatch: ${a.currency} vs ${b.currency}`);
  }
}

export function add(a, b) { same(a, b); return money(a.amount + b.amount, a.currency); }
export function subtract(a, b) { same(a, b); return money(a.amount - b.amount, a.currency); }
export function isZero(a) { return a.amount === 0; }
export function isNegative(a) { return a.amount < 0; }
export function compare(a, b) { same(a, b); return Math.sign(a.amount - b.amount); }

/**
 * Split an amount into n parts as evenly as possible with NO rounding loss:
 * the sum of the parts always equals the original amount (remainder cents are
 * distributed to the first parts). Useful for proration / invoice lines.
 */
export function allocate(a, n) {
  if (!Number.isInteger(n) || n <= 0) throw new RangeError(`allocate needs a positive integer, got ${n}`);
  const base = Math.trunc(a.amount / n);
  let remainder = a.amount - base * n;
  const step = remainder >= 0 ? 1 : -1;
  const parts = [];
  for (let i = 0; i < n; i++) {
    let part = base;
    if (remainder !== 0) { part += step; remainder -= step; }
    parts.push(money(part, a.currency));
  }
  return parts;
}

/** Format Money for display (major units). Presentation only — not for math. */
export function format(a, locale = "en-US") {
  const exp = exponent(a.currency);
  const major = a.amount / 10 ** exp;
  try {
    return new Intl.NumberFormat(locale, { style: "currency", currency: a.currency }).format(major);
  } catch {
    return `${major.toFixed(exp)} ${a.currency}`;
  }
}
