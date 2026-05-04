// =============================================================================
// STRIPE PRODUCTS CONFIGURATION
// =============================================================================

module.exports = {
  // Subscription Products
  subscriptions: {
    basic: {
      name: 'Basic Subscription',
      description: 'Access to our basic library with 10 books per month',
      price: 999, // $9.99 in cents
      interval: 'month',
      trialPeriodDays: 7,
      features: [
        'Access to all books',
        '10 books per month',
        'Download up to 5 books',
        'Email support',
      ],
    },
    
    premium: {
      name: 'Premium Subscription',
      description: 'Unlimited access to all books with premium features',
      price: 1999, // $19.99 in cents
      interval: 'month',
      trialPeriodDays: 7,
      features: [
        'Unlimited books',
        'Unlimited downloads',
        'Offline reading',
        'Priority support',
        'Early access',
        'Ad-free experience',
      ],
    },
    
    premiumAnnual: {
      name: 'Premium Annual Subscription',
      description: 'Unlimited access for one year at a discounted rate',
      price: 19999, // $199.99 in cents
      interval: 'year',
      trialPeriodDays: 7,
      features: [
        'All Premium features',
        'Save 16% vs monthly',
        'Annual billing',
      ],
    },
  },
  
  // One-time Products
  oneTime: {
    giftCard: {
      name: 'Gift Card',
      description: 'Give the gift of reading',
      denominations: [1000, 2500, 5000, 10000], // in cents
    },
  },
};
