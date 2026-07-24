// Webhook + idempotency helpers for the Runix commerce layer.
//
// Payment providers notify us of events (payment succeeded, refunded, dispute
// opened, ...) via webhooks. Two things must ALWAYS hold before we act on one:
//   1. Signature is verified  -> the event really came from the provider.
//   2. Delivery is idempotent  -> re-delivering the same event does not grant
//      an entitlement or credit twice.
//
// Pure/standard-lib only (node:crypto). No secrets are stored here — the secret
// is passed in by the caller from server-side configuration.

import crypto from "node:crypto";

/** Compute the hex HMAC-SHA256 of a raw payload. */
export function computeSignature(rawPayload, secret) {
  if (typeof secret !== "string" || secret.length === 0) {
    throw new TypeError("webhook secret must be a non-empty string");
  }
  return crypto.createHmac("sha256", secret).update(rawPayload).digest("hex");
}

/**
 * Constant-time verification of a provider-supplied signature.
 * Returns false (never throws) for any mismatch, tampering, or malformed input.
 */
export function verifySignature(rawPayload, providedHex, secret) {
  let expected, provided;
  try {
    expected = Buffer.from(computeSignature(rawPayload, secret), "hex");
    provided = Buffer.from(String(providedHex), "hex");
  } catch {
    return false;
  }
  if (expected.length === 0 || expected.length !== provided.length) return false;
  return crypto.timingSafeEqual(expected, provided);
}

/**
 * Reference in-memory idempotency store. Records which webhook event ids have
 * already been processed. NOTE: this is for tests/reference only — a real
 * deployment must back this with a durable, atomic store (e.g. a unique DB
 * constraint on event id) so concurrent deliveries cannot both win.
 */
export class MemoryIdempotencyStore {
  #seen = new Set();
  /** True the first time an id is seen ("process it"); false on every replay. */
  firstSeen(eventId) {
    if (this.#seen.has(eventId)) return false;
    this.#seen.add(eventId);
    return true;
  }
  has(eventId) { return this.#seen.has(eventId); }
}
