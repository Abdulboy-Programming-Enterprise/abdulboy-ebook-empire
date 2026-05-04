// =============================================================================
// STRIPE PAYMENT CONFIGURATION
// =============================================================================
// Stripe payment gateway configuration for Abdulboy Ebook Empire
// =============================================================================

const stripeConfig = {
  // API Configuration
  apiVersion: '2023-10-16',
  apiKey: process.env.STRIPE_SECRET_KEY,
  publishableKey: process.env.STRIPE_PUBLIC_KEY,
  webhookSecret: process.env.STRIPE_WEBHOOK_SECRET,
  
  // Business Settings
  business: {
    name: 'Abdulboy Ebook Empire',
    url: 'https://abdulboy-ebook.com',
    supportEmail: 'support@abdulboy-ebook.com',
    supportPhone: '+234 123 456 7890',
    statementDescriptor: 'ABDULBOY EBOOKS',
    country: 'US',
  },
  
  // Payment Methods
  paymentMethods: {
    card: {
      enabled: true,
      networks: ['visa', 'mastercard', 'amex', 'discover'],
    },
    applePay: {
      enabled: true,
      merchantId: 'merchant.abdulboy-ebook.com',
    },
    googlePay: {
      enabled: true,
      merchantId: 'BCR2DN4T5XQ2L5J6',
    },
    link: {
      enabled: true,
    },
    usBankAccount: {
      enabled: false,
    },
  },
  
  // Currency Settings
  currencies: {
    default: 'usd',
    supported: ['usd', 'eur', 'gbp', 'ngn'],
    exchangeRates: {
      eur: 0.92,
      gbp: 0.79,
      ngn: 1480,
    },
  },
  
  // Webhook Configuration
  webhooks: {
    endpoint: '/api/v1/webhooks/stripe',
    events: [
      'payment_intent.succeeded',
      'payment_intent.payment_failed',
      'payment_intent.canceled',
      'charge.refunded',
      'customer.subscription.created',
      'customer.subscription.updated',
      'customer.subscription.deleted',
      'invoice.payment_succeeded',
      'invoice.payment_failed',
    ],
    retryConfig: {
      maxAttempts: 5,
      initialDelay: 1000,
      backoffFactor: 2,
    },
  },
  
  // Product Configuration
  products: {
    books: {
      type: 'one_time',
      statementDescriptor: 'BOOK PURCHASE',
    },
    subscriptions: {
      type: 'recurring',
      statementDescriptor: 'MONTHLY SUBSCRIPTION',
      trialPeriodDays: 7,
    },
    customBooks: {
      type: 'one_time',
      statementDescriptor: 'CUSTOM BOOK',
    },
  },
  
  // Customer Configuration
  customers: {
    createAutomatically: true,
    sendInvoice: true,
    taxIdCollection: {
      enabled: false,
      required: false,
    },
  },
  
  // Checkout Settings
  checkout: {
    successUrl: 'https://abdulboy-ebook.com/payment-success?session_id={CHECKOUT_SESSION_ID}',
    cancelUrl: 'https://abdulboy-ebook.com/payment-cancel',
    allowPromotionCodes: true,
    collectShippingAddress: false,
    collectBillingAddress: true,
    paymentMethodTypes: ['card'],
    locale: 'auto',
  },
  
  // Invoice Settings
  invoice: {
    enabled: true,
    daysUntilDue: 30,
    defaultPaymentTerms: '自动',
    footer: 'Thank you for shopping with Abdulboy Ebook Empire!',
  },
  
  // Email Receipts
  emailReceipts: {
    enabled: true,
    fromName: 'Abdulboy Ebook Empire',
    fromEmail: 'receipts@abdulboy-ebook.com',
    subject: 'Your Abdulboy Ebook Empire Receipt',
  },
  
  // Refund Settings
  refunds: {
    enabled: true,
    allowedWithinDays: 30,
    restockingFee: 0,
    reasonOptions: [
      'duplicate',
      'fraudulent',
      'requested_by_customer',
      'product_unavailable',
    ],
  },
  
  // Metadata Mapping
  metadata: {
    bookId: 'book_id',
    userId: 'user_id',
    orderId: 'order_id',
    subscriptionId: 'subscription_id',
    paymentType: 'payment_type',
  },
  
  // Error Messages
  errors: {
    cardDeclined: 'Your card was declined. Please try a different card.',
    insufficientFunds: 'Insufficient funds. Please use a different payment method.',
    expiredCard: 'Your card has expired. Please update your card information.',
    incorrectCvc: 'Incorrect security code. Please check and try again.',
    processingError: 'An error occurred processing your payment. Please try again.',
    authenticationRequired: 'Additional authentication is required. Please complete 3D Secure.',
  },
  
  // Testing (Development)
  test: {
    cards: {
      success: '4242 4242 4242 4242',
      requiresAuth: '4000 0025 0000 3155',
      declined: '4000 0000 0000 0002',
      insufficientFunds: '4000 0000 0000 9995',
      lostCard: '4000 0000 0000 9987',
    },
    testMode: process.env.NODE_ENV !== 'production',
  },
};

// Export configuration
if (typeof module !== 'undefined' && module.exports) {
  module.exports = stripeConfig;
}

if (typeof window !== 'undefined') {
  window.stripeConfig = stripeConfig;
}
