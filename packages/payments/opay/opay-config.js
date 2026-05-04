// =============================================================================
// OPAY PAYMENT CONFIGURATION
// =============================================================================
// OPay payment gateway configuration for Nigerian/African market
// =============================================================================

const opayConfig = {
  // API Configuration
  apiVersion: 'v1',
  apiUrl: process.env.OPAY_ENV === 'production' 
    ? 'https://api.opaycheckout.com'
    : 'https://sandboxapi.opaycheckout.com',
  
  merchantId: process.env.OPAY_MERCHANT_ID,
  publicKey: process.env.OPAY_PUBLIC_KEY,
  privateKey: process.env.OPAY_SECRET_KEY,
  
  // Business Settings
  business: {
    name: 'Abdulboy Ebook Empire',
    url: 'https://abdulboy-ebook.com',
    supportEmail: 'support@abdulboy-ebook.com',
    supportPhone: '+234 123 456 7890',
    countryCode: 'NG',
    currency: 'NGN',
  },
  
  // Payment Methods
  paymentMethods: {
    card: {
      enabled: true,
      providers: ['VISA', 'MASTERCARD', 'VERVE'],
    },
    bank: {
      enabled: true,
      methods: ['bank_account', 'bank_transfer'],
    },
    ussd: {
      enabled: true,
      codes: ['*777#', '*894#', '*737#'],
    },
    transfer: {
      enabled: true,
    },
    qr: {
      enabled: true,
    },
  },
  
  // Currency Settings
  currencies: {
    default: 'NGN',
    supported: ['NGN'],
    exchangeRates: {
      USD: 1480,
      EUR: 1600,
      GBP: 1850,
    },
  },
  
  // Webhook Configuration
  webhooks: {
    endpoint: '/api/v1/webhooks/opay',
    events: [
      'order.success',
      'order.failed',
      'order.pending',
      'refund.success',
    ],
    retryConfig: {
      maxAttempts: 5,
      initialDelay: 1000,
      backoffFactor: 2,
    },
  },
  
  // Order Configuration
  orders: {
    referencePrefix: 'ABE',
    referenceLength: 16,
    timeout: 3600, // 1 hour in seconds
    
    products: {
      books: {
        type: 'physical',
        category: 'Digital Goods',
      },
      subscriptions: {
        type: 'service',
        category: 'Subscriptions',
      },
      customBooks: {
        type: 'service',
        category: 'Custom Services',
      },
    },
  },
  
  // Customer Configuration
  customers: {
    required: {
      email: true,
      phone: true,
      name: true,
    },
    optional: {
      address: false,
      city: false,
      state: false,
    },
  },
  
  // Checkout Settings
  checkout: {
    successUrl: 'https://abdulboy-ebook.com/payment-success?reference={reference}',
    cancelUrl: 'https://abdulboy-ebook.com/payment-cancel',
    webhookUrl: 'https://api.abdulboy-ebook.com/api/v1/webhooks/opay',
    locale: 'en',
    theme: 'light',
  },
  
  // Refund Settings
  refunds: {
    enabled: true,
    allowedWithinDays: 30,
    processingFee: 0,
    reasonOptions: [
      'customer_request',
      'fraud',
      'duplicate',
      'product_unavailable',
    ],
  },
  
  // Validation Rules
  validation: {
    maxAmount: 10000000, // 10 million NGN
    minAmount: 100, // 100 NGN
    allowedCountries: ['NG'],
  },
  
  // Error Messages
  errors: {
    insufficientFunds: 'Insufficient funds in your account. Please try another payment method.',
    invalidCard: 'The card information provided is invalid. Please check and try again.',
    expiredCard: 'Your card has expired. Please use a different card.',
    bankUnavailable: 'The selected bank is currently unavailable. Please try another bank.',
    ussdFailed: 'USSD payment failed. Please try again or use another payment method.',
    timeout: 'Payment timeout. Please try again.',
    processingError: 'An error occurred processing your payment. Please try again.',
  },
  
  // Testing (Development)
  test: {
    cards: {
      success: '5123450000000008',
      insufficientFunds: '5123450000000006',
      expired: '5123450000000005',
      invalid: '5123450000000000',
    },
    banks: {
      success: '058', // First Bank
      unavailable: '011', // Wema Bank
    },
    ussd: {
      success: '*777*1234567890#',
      failed: '*777*0000000000#',
    },
    testMode: process.env.OPAY_ENV !== 'production',
  },
  
  // Dictionary
  banks: [
    { code: '000', name: 'Access Bank' },
    { code: '001', name: 'Zenith Bank' },
    { code: '002', name: 'First Bank' },
    { code: '003', name: 'GTBank' },
    { code: '004', name: 'UBA' },
    { code: '005', name: 'FCMB' },
    { code: '006', name: 'Stanbic IBTC' },
    { code: '007', name: 'Union Bank' },
    { code: '008', name: 'Fidelity Bank' },
    { code: '009', name: 'Keystone Bank' },
    { code: '010', name: 'Polaris Bank' },
    { code: '011', name: 'Wema Bank' },
    { code: '012', name: 'Heritage Bank' },
    { code: '013', name: 'Unity Bank' },
    { code: '014', name: 'Jaiz Bank' },
    { code: '015', name: 'Taj Bank' },
    { code: '016', name: 'Suntrust Bank' },
    { code: '017', name: 'Providus Bank' },
  ],
};

// Export configuration
if (typeof module !== 'undefined' && module.exports) {
  module.exports = opayConfig;
}

if (typeof window !== 'undefined') {
  window.opayConfig = opayConfig;
}

// Helper: Generate order reference
function generateOrderReference() {
  const prefix = opayConfig.orders.referencePrefix;
  const timestamp = Date.now().toString(36).toUpperCase();
  const random = Math.random().toString(36).substring(2, 8).toUpperCase();
  return `${prefix}${timestamp}${random}`;
}

// Helper: Validate amount
function isValidAmount(amount) {
  return amount >= opayConfig.validation.minAmount && amount <= opayConfig.validation.maxAmount;
}

// Helper: Get bank name by code
function getBankName(code) {
  const bank = opayConfig.banks.find(b => b.code === code);
  return bank ? bank.name : null;
}

module.exports.generateOrderReference = generateOrderReference;
module.exports.isValidAmount = isValidAmount;
module.exports.getBankName = getBankName;
