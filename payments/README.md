# Runix commerce & payment layer (reserved)

This folder is the **provider-agnostic commerce layer** for Runix. Today the
website is a **static site with no runtime backend**, so this folder contains
only what is safe to have without a server:

- **Types & interface boundaries** (`types.js`) — the internal objects Runix
  owns, and the `PaymentProvider` interface every provider adapter implements.
- **Money-safety utilities** (`money.js`) — integer minor-unit money math, so
  amounts never suffer float rounding. Fully unit-tested.
- **Webhook safety** (`webhook.js`) — signature verification + an idempotency
  guard so replayed events can't double-grant. Unit-tested.

There is **no live payment backend here, and there are no secrets**. We did not
build a fake payment server "to look complete" — a real integration will live
in a proper backend service and connect real providers under explicit approval.

## Design principles

1. **Providers move money; Runix owns the truth.** Order status, entitlements,
   credit balance, subscription state, invoices, refunds, and reconciliation are
   Runix-owned and are never derived solely from a provider dashboard.
2. **Don't bind business logic to one provider.** Stripe, Airwallex, PayPal,
   bank transfer, and future providers are adapters behind `PaymentProvider`.
3. **Prefer hosted checkout.** Keeps card data out of Runix and minimizes PCI
   scope. Runix never stores full card numbers.
4. **Money is integer minor units + currency.** Never floats. Cross-currency
   math throws. See `money.js`.
5. **Secrets stay server-side.** Provider API keys / webhook secrets live only
   in server environment configuration — never in the browser or this repo.

## Money-safety checklist (must hold in the real backend)

- [ ] Verify every webhook signature before acting on it (`webhook.verifySignature`).
- [ ] Idempotent event handling backed by a **durable, atomic** store (a unique
      DB constraint on provider event id) — the in-memory store here is reference only.
- [ ] Replay protection (reject stale/duplicate events).
- [ ] Guard the "paid but provisioning failed" case: entitlement grant and
      payment record committed together (or reconciled), never one without the other.
- [ ] Refund reclaims the corresponding credits/entitlement.
- [ ] Handle chargebacks/disputes (suspend, investigate) distinctly from refunds.
- [ ] Multi-currency amounts stored as minor units; display formatting is separate.
- [ ] Tax computed/collected per jurisdiction at checkout or on invoice.
- [ ] Logs are masked — no card data, no secrets, no full PII.

## Business model (for payment-processor review)

Runix sells **its own** AI infrastructure and software (AI Gateway, Data
Pipelines, AI Solutions) to its customers. Runix is **not** a payment platform,
financial institution, escrow service, or third-party marketplace, and does not
collect funds on behalf of other sellers. If a marketplace / third-party seller
model is ever introduced, it must be treated as a separate feature requiring its
own compliance review — not folded into this standard merchant flow.

## Tests

```
npm test        # runs node --test over payments/
```
