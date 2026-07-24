// Commerce domain types + the provider-agnostic payment interface.
//
// These are the INTERNAL objects Runix owns. Payment providers (Stripe,
// Airwallex, PayPal, bank transfer, future providers) are adapters behind the
// PaymentProvider interface; they move money. Runix owns order status,
// entitlements, quota/credit balance, subscription state, invoices, refunds,
// and reconciliation — never derived solely from a provider's UI.
//
// JSDoc typedefs (no build step). All money fields are integer minor units +
// a currency (see money.js). This file has no runtime behavior beyond the
// abstract base class, which exists so a real adapter must implement every
// method rather than silently no-op.

/** @typedef {import("./money.js").Money} Money */

/** @typedef {"draft"|"open"|"paid"|"canceled"|"refunded"|"disputed"} OrderStatus */
/** @typedef {"requires_payment"|"processing"|"succeeded"|"failed"|"canceled"} PaymentStatus */
/** @typedef {"active"|"past_due"|"canceled"|"paused"} SubscriptionStatus */
/** @typedef {"usage"|"subscription"|"prepaid"|"one_time"} PriceModel */

/** @typedef {{ id: string, email: string, name?: string, companyName?: string, taxId?: string, provider?: string, providerCustomerId?: string }} Customer */
/** @typedef {{ id: string, name: string, kind: "gateway"|"data_pipelines"|"solutions", active: boolean }} Product */
/** @typedef {{ id: string, productId: string, model: PriceModel, unitAmount?: Money, unit?: string, currency: string, interval?: "month"|"year" }} Price */
/** @typedef {{ id: string, customerId: string, items: {priceId: string, quantity: number}[], amount: Money, tax?: Money, status: OrderStatus, createdAt: string }} Order */
/** @typedef {{ id: string, orderId: string, provider: string, url?: string, status: "open"|"complete"|"expired", returnUrl?: string }} CheckoutSession */
/** @typedef {{ id: string, orderId: string, provider: string, providerPaymentId: string, amount: Money, status: PaymentStatus, statementDescriptor?: string }} Payment */
/** @typedef {{ id: string, paymentId: string, amount: Money, reason?: string, status: "pending"|"succeeded"|"failed", createdAt: string }} Refund */
/** @typedef {{ id: string, customerId: string, priceId: string, status: SubscriptionStatus, currentPeriodEnd: string, cancelAtPeriodEnd: boolean }} Subscription */
/** @typedef {{ id: string, customerId: string, balance: Money, autoRecharge?: {enabled: boolean, thresholdAmount: Money, topupAmount: Money} }} CreditBalance */
/** @typedef {{ id: string, customerId: string, number: string, amount: Money, tax?: Money, status: "draft"|"open"|"paid"|"void", lines: {description: string, amount: Money}[], issuedAt?: string }} Invoice */
/** @typedef {{ id: string, customerId: string, provider: string, brand?: string, last4?: string, expMonth?: number, expYear?: number }} PaymentMethod */
/** @typedef {{ id: string, provider: string, type: string, receivedAt: string, verified: boolean, payload: unknown }} WebhookEvent */
/** @typedef {{ id: string, customerId: string, productKind: Product["kind"], grantedBy: string, grantedAt: string, revokedAt?: string }} Entitlement */

/**
 * Provider-agnostic payment interface. A concrete adapter (StripeProvider,
 * AirwallexProvider, PayPalProvider, BankTransferProvider, ...) implements
 * these. Prefer HOSTED checkout to keep card data out of Runix (PCI scope).
 *
 * @abstract
 */
export class PaymentProvider {
  /** Stable adapter name, e.g. "stripe". @returns {string} */
  get name() { throw new Error("PaymentProvider.name not implemented"); }
  /** Create (or fetch) the provider-side customer. @returns {Promise<Customer>} */
  async ensureCustomer(_customer) { throw new Error(`${this.constructor.name}.ensureCustomer not implemented`); }
  /** Start a hosted checkout for an order. @returns {Promise<CheckoutSession>} */
  async createCheckoutSession(_order, _opts) { throw new Error(`${this.constructor.name}.createCheckoutSession not implemented`); }
  /** Verify a raw webhook and return a normalized event. @returns {Promise<WebhookEvent>} */
  async parseWebhook(_rawBody, _headers, _secret) { throw new Error(`${this.constructor.name}.parseWebhook not implemented`); }
  /** Refund a payment (full or partial). @returns {Promise<Refund>} */
  async refund(_payment, _amount) { throw new Error(`${this.constructor.name}.refund not implemented`); }
}
