/**
 * Pins the server-side amount guard for Airwallex top-ups.
 *
 * The picker on /plans is a convenience; the shopper can edit it, replay the
 * request, or call the endpoint directly. parseAmount is therefore the only
 * place the floor and ceiling are actually enforced, which is why it is tested
 * here rather than trusted.
 *
 * Note the unit: Airwallex takes MAJOR units (verified against the live API —
 * amount 0.5 was accepted and echoed back as 0.5), the opposite of Stripe. So
 * "10" here means ten dollars, not ten cents, and the guard must not rescale.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { parseAmount, MIN_USD, MAX_USD, CREDIT_MULTIPLE } from "../functions/api/airwallex/intent.js";

test("accepts amounts inside the configured range", () => {
  assert.equal(parseAmount(10), 10);
  assert.equal(parseAmount(1000), 1000);
  assert.equal(parseAmount(10000), 10000);
  assert.equal(parseAmount("250"), 250);
});

test("accepts up to two decimal places and normalises them", () => {
  assert.equal(parseAmount("10.00"), 10);
  assert.equal(parseAmount("19.99"), 19.99);
  assert.equal(parseAmount(19.5), 19.5);
});

test("rejects anything below the floor or above the ceiling", () => {
  assert.equal(parseAmount(9.99), null);
  assert.equal(parseAmount(0), null);
  assert.equal(parseAmount(1), null);
  assert.equal(parseAmount(10000.01), null);
  assert.equal(parseAmount(9000000), null);
});

test("rejects negatives, which must not slip through as a credit", () => {
  assert.equal(parseAmount(-100), null);
  assert.equal(parseAmount("-100"), null);
});

test("rejects shapes that are not a plain decimal amount", () => {
  assert.equal(parseAmount("1e4"), null);       // exponent notation
  assert.equal(parseAmount("10.999"), null);    // sub-cent precision
  assert.equal(parseAmount("0x64"), null);
  assert.equal(parseAmount(" 100 "), 100);      // surrounding space is trimmed
  assert.equal(parseAmount("100abc"), null);
  assert.equal(parseAmount(""), null);
  assert.equal(parseAmount(null), null);
  assert.equal(parseAmount(undefined), null);
  assert.equal(parseAmount({}), null);
  assert.equal(parseAmount([]), null);
  assert.equal(parseAmount(NaN), null);
  assert.equal(parseAmount(Infinity), null);
});

test("returns MAJOR units — the 100x trap that would double-charge or under-charge", () => {
  // Airwallex takes major units; Stripe takes minor. Anyone "helpfully"
  // converting to cents to match the other provider turns $10 into 1000, which
  // Airwallex reads as one thousand dollars. This is the assertion that fails
  // if that conversion ever gets added, in either direction.
  assert.equal(parseAmount(10), 10);
  assert.notEqual(parseAmount(10), 1000);
  assert.equal(parseAmount(MAX_USD), 10000);
  assert.notEqual(parseAmount(MAX_USD), 1000000);
  // A sub-dollar value must stay sub-dollar, not become a dollar figure.
  assert.equal(parseAmount(MIN_USD), 10);
});

test("credit rate matches what /plans states in words", () => {
  // "credits are worth twice what you pay" appears in the copy, in the equiv
  // box arithmetic, and in the metadata sent for manual reconciliation.
  assert.equal(CREDIT_MULTIPLE, 2);
  assert.equal(parseAmount(250) * CREDIT_MULTIPLE, 500);
});

test("bounds are the ones the /plans copy promises", () => {
  // plans.html states "Anything from $10 to $10,000" and the Stripe link is
  // configured to the same range. If one moves, this test should fail and the
  // other two get moved with it.
  assert.equal(MIN_USD, 10);
  assert.equal(MAX_USD, 10000);
});
