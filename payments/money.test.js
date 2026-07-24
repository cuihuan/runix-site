import { test } from "node:test";
import assert from "node:assert/strict";
import { money, fromDecimalString, add, subtract, allocate, compare, isZero, isNegative, exponent, format } from "./money.js";

test("money() requires integer minor units and valid currency", () => {
  assert.deepEqual(money(1000, "USD"), { amount: 1000, currency: "USD" });
  assert.throws(() => money(10.5, "USD"), TypeError);
  assert.throws(() => money(100, "usd"), TypeError);
  assert.throws(() => money(100, "US"), TypeError);
});

test("exponent() knows zero-decimal currencies", () => {
  assert.equal(exponent("USD"), 2);
  assert.equal(exponent("JPY"), 0);
  assert.equal(exponent("XYZ"), 2); // default
});

test("fromDecimalString parses exactly without float error", () => {
  assert.deepEqual(fromDecimalString("10.00", "USD"), { amount: 1000, currency: "USD" });
  assert.deepEqual(fromDecimalString("0.1", "USD"), { amount: 10, currency: "USD" });
  assert.deepEqual(fromDecimalString("19.99", "USD"), { amount: 1999, currency: "USD" });
  assert.deepEqual(fromDecimalString("-5", "USD"), { amount: -500, currency: "USD" });
  assert.deepEqual(fromDecimalString("500", "JPY"), { amount: 500, currency: "JPY" });
  // classic float trap: 0.1 + 0.2 must be exact in minor units
  assert.deepEqual(add(fromDecimalString("0.1", "USD"), fromDecimalString("0.2", "USD")),
    { amount: 30, currency: "USD" });
});

test("fromDecimalString rejects over-precise input", () => {
  assert.throws(() => fromDecimalString("1.999", "USD"), RangeError);
  assert.throws(() => fromDecimalString("1.5", "JPY"), RangeError);
});

test("add/subtract enforce same currency", () => {
  assert.deepEqual(add(money(100, "USD"), money(250, "USD")), { amount: 350, currency: "USD" });
  assert.deepEqual(subtract(money(100, "USD"), money(40, "USD")), { amount: 60, currency: "USD" });
  assert.throws(() => add(money(100, "USD"), money(100, "EUR")), /Currency mismatch/);
});

test("allocate never loses or invents money", () => {
  const parts = allocate(money(1000, "USD"), 3); // 3-way split of $10.00
  assert.equal(parts.length, 3);
  const sum = parts.reduce((acc, p) => acc + p.amount, 0);
  assert.equal(sum, 1000);
  assert.deepEqual(parts.map(p => p.amount), [334, 333, 333]);
  // negative amounts (e.g. a refund split) also conserve total
  const neg = allocate(money(-1000, "USD"), 3);
  assert.equal(neg.reduce((a, p) => a + p.amount, 0), -1000);
});

test("predicates and compare", () => {
  assert.ok(isZero(money(0, "USD")));
  assert.ok(isNegative(money(-1, "USD")));
  assert.equal(compare(money(100, "USD"), money(200, "USD")), -1);
  assert.equal(compare(money(200, "USD"), money(200, "USD")), 0);
});

test("format renders major units", () => {
  assert.equal(format(money(1999, "USD")), "$19.99");
});
