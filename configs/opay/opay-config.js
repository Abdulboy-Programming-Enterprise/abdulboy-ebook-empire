// =============================================================================
// OPAY CONFIGURATION (Production)
// =============================================================================

module.exports = {
  apiVersion: 'v1',
  
  // API Endpoints
  apiUrl: process.env.OPAY_ENV === 'production'
    ? 'https://api.opaycheckout.com'
    : 'https://sandboxapi.opaycheckout.com',
  
  // Credentials
  merchantId: process.env.OPAY_MERCHANT_ID,
  publicKey: process.env.OPAY_PUBLIC_KEY,
  privateKey: process.env.OPAY_SECRET_KEY,
  
  // Webhook Configuration
  webhook: {
    endpoint: '/api/v1/webhooks/opay',
    events: ['order.success', 'order.failed', 'order.pending', 'refund.success'],
  },
  
  // Business Settings
  business: {
    name: 'Abdulboy Ebook Empire',
    url: 'https://abdulboy-ebook.com',
    supportEmail: 'support@abdulboy-ebook.com',
    supportPhone: '+234 123 456 7890',
    countryCode: 'NG',
    currency: 'NGN',
  },
  
  // Order Settings
  order: {
    referencePrefix: 'ABE',
    timeout: 3600, // seconds
  },
  
  // Payment Methods
  paymentMethods: {
    card: true,
    bank: true,
    ussd: true,
    transfer: true,
    qr: true,
  },
  
  // Nigerian Banks
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
  ],
  
  // Test Cards (Development)
  testCards: {
    success: '5123450000000008',
    insufficientFunds: '5123450000000006',
    expired: '5123450000000005',
  },
};
