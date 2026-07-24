import { test } from "node:test";
import assert from "node:assert/strict";
import { computeSignature, verifySignature, MemoryIdempotencyStore } from "./webhook.js";

const SECRET = "whsec_test_example_not_a_real_key";
const payload = JSON.stringify({ id: "evt_1", type: "payment.succeeded" });

test("verifySignature accepts a correct signature", () => {
  const sig = computeSignature(payload, SECRET);
  assert.equal(verifySignature(payload, sig, SECRET), true);
});

test("verifySignature rejects wrong secret, tampered payload, and garbage", () => {
  const sig = computeSignature(payload, SECRET);
  assert.equal(verifySignature(payload, sig, "wrong_secret"), false);
  assert.equal(verifySignature(payload + "x", sig, SECRET), false);
  assert.equal(verifySignature(payload, "not-hex-zz", SECRET), false);
  assert.equal(verifySignature(payload, "", SECRET), false);
});

test("computeSignature requires a real secret", () => {
  assert.throws(() => computeSignature(payload, ""), TypeError);
});

test("idempotency store processes an event once, replays are ignored", () => {
  const store = new MemoryIdempotencyStore();
  assert.equal(store.firstSeen("evt_1"), true);   // process
  assert.equal(store.firstSeen("evt_1"), false);  // replay -> skip (no double grant)
  assert.equal(store.firstSeen("evt_2"), true);
  assert.equal(store.has("evt_1"), true);
});
