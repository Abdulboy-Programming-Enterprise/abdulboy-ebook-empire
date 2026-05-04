// =============================================================================
// STRIPE CONFIGURATION (Production)
// =============================================================================

module.exports = {
  apiVersion: '2023-10-16',
  
  // API Keys (from environment)
  secretKey: process.env.STRIPE_SECRET_KEY,
  publishableKey: process.env.STRIPE_PUBLIC_KEY,
  webhookSecret: process.env.STRIPE_WEBHOOK_SECRET,
  
  // Webhook Settings
  webhook: {
    endpoint: '/api/v1/webhooks/stripe',
    events: [
      'payment_intent.succeeded',
      'payment_intent.payment_failed',
      'charge.refunded',
      'customer.subscription.created',
      'customer.subscription.updated',
      'customer.subscription.deleted',
      'invoice.payment_succeeded',
      'invoice.payment_failed',
    ],
  },
  
  // Business Settings
  business: {
    name: 'Abdulboy Ebook Empire',
    url: 'https://abdulboy-ebook.com',
    supportEmail: 'support@abdulboy-ebook.com',
    statementDescriptor: 'ABDULBOY EBOOKS',
  },
  
  // Product Configuration
  products: {
    book: {
      type: 'one_time',
      statementDescriptor: 'BOOK PURCHASE',
    },
    subscription: {
      type: 'recurring',
      statementDescriptor: 'MONTHLY SUBSCRIPTION',
      trialPeriodDays: 7,
    },
  },
  
  // Test Cards (Development)
  testCards: {
    success: '4242 4242 4242 4242',
    requiresAuth: '4000 0025 0000 3155',
    declined: '4000 0000 0000 0002',
    insufficientFunds: '4000 0000 0000 9995',
  },
};
