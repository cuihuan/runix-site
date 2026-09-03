# Runix commerce & payment layer

> **2026-09-03: there is now a live payment backend.** `functions/api/airwallex/intent.js`
> is a Cloudflare Pages Function that mints real Airwallex payment intents against the
> production account. The paragraph below said no such thing existed; it was true when
> written and is kept only so the change is visible. See **Live integrations** at the
> bottom for what actually runs, where its credentials live, and what the accounts can
> and cannot do.

This folder is the **provider-agnostic commerce layer** for Runix. It was written when the
website was a **static site with no runtime backend**, so it contains what is safe to hold
without a server:

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

---

## Live integrations (as of 2026-09-03)

Two checkouts run on `/plans`, and they are **not interchangeable**. Both grant credits
**manually** today — no webhook is wired on either side.

### Stripe — subscriptions + one top-up link
- Four payment links carry the monthly plans; a fifth is the top-up. All are plain `<a href>`,
  so this is the only path that survives with **JavaScript disabled**.
- Accepts **UnionPay**, Visa, Mastercard, Diners Club, Cash App Pay, Apple Pay, Link
  (read off the live checkout at 4x zoom, not assumed).
- **Known defect:** the top-up link opens at its own configured default ($200) and a payment
  link **cannot** be pre-filled from the URL — `?amount=` was tested and ignored. Credits are
  therefore granted against **what was actually charged**, which is what the page copy promises.
  Fixing it properly needs either four fixed-amount links, or a secret key and Checkout Session.
- `assets/site-config.js` holds a **publishable** `pk_live_` key and a complete Stripe Buy Button
  integration that has never rendered (`buyButtonId` is null, awaiting a ONE-TIME price).
  No `sk_` secret key exists anywhere in this project.

### Airwallex — top-up only
- `functions/api/airwallex/intent.js` mints an intent server-side; the browser then loads the
  SDK from `checkout.airwallex.com` and calls `redirectToCheckout`. **Requires JavaScript.**
- Amount is carried accurately end to end, unlike the Stripe link.
- **Amounts are MAJOR units** (`10` = ten dollars), the opposite of Stripe. Pinned by
  `payments/airwallex-intent.test.js`; injecting a `* 100` makes 5 tests fail.

#### Account capability, measured against the live API — not assumed
| | Status |
|---|---|
| Card schemes | **Visa and Mastercard only** — no Amex, no UnionPay, no JCB, no Discover |
| Wallets / BNPL | Apple Pay, Google Pay, Afterpay, Klarna (US only) |
| Alipay / WeChat Pay | **Not enabled** — checked across four parameter combinations |
| Payment Links product | **Not enabled** — `configuration_error` on every currency and body shape |
| Payment Intents | Works (201) |

Amex is available from Airwallex but needs a separate application (KYB + card scheme request);
the published rollout named AU/HK/SG/UK, and this is a US entity, so it needs confirming.

**This is why Airwallex cannot replace Stripe here:** it has no UnionPay, and Runix sells to
Chinese companies operating abroad. It also has no billing engine for the four subscriptions.

#### Credentials
Never in this repo. Two places only:
- **Cloudflare Pages secrets** on project `runix-site`: `AIRWALLEX_CLIENT_ID`, `AIRWALLEX_API_KEY`
  (both show as "Value Encrypted"). This is what the Function reads.
- **macOS Keychain** on Cuihuan's machine, service `runix-airwallex`, accounts
  `airwallex-prod` (API key), `airwallex-prod-clientid`, `airwallex-prod-acctid` —
  used by local tooling and `wrangler pages dev`.

Rotating the key means updating **both**. The key in use is named `dev_for_ai` in the Airwallex
dashboard and was pasted in plaintext during setup, so it should be rotated.

⚠️ Airwallex offers IP allow-listing on API keys. **Do not enable it**: Cloudflare Workers egress
from arbitrary global addresses, so an allow-list would silently kill every checkout.

#### Still open
- No webhook either side → credits are granted by hand; `webhook.js` here is written and tested
  but not wired. Until it is, there is no order record binding a payment to an account.
- The intent endpoint is unauthenticated with no rate limit; the same-origin check is the only gate.
- `deploy.sh` verification does not exercise the Function at all.
