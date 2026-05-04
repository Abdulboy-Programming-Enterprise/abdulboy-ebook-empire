// =============================================================================
// STRIPE PRODUCTS & PRICES
// =============================================================================
// Product definitions for Stripe checkout
// =============================================================================

const stripeProducts = {
  // ---------------------------------------------------------------------------
  // One-time Book Purchases
  // ---------------------------------------------------------------------------
  bookPurchase: {
    name: 'Book Purchase',
    description: 'One-time purchase of a digital book',
    type: 'one_time',
    metadata: {
      category: 'book',
      platform: 'abdulboy-ebook',
    },
  },
  
  // ---------------------------------------------------------------------------
  // Subscription Plans
  // ---------------------------------------------------------------------------
  subscriptions: {
    basic: {
      name: 'Basic Subscription',
      description: 'Access to our basic library with 10 books per month',
      type: 'recurring',
      interval: 'month',
      intervalCount: 1,
      metadata: {
        plan_id: 'basic',
        plan_name: 'Basic',
        books_per_month: '10',
        download_limit: '5',
      },
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
      type: 'recurring',
      interval: 'month',
      intervalCount: 1,
      metadata: {
        plan_id: 'premium',
        plan_name: 'Premium',
        books_per_month: 'unlimited',
        download_limit: 'unlimited',
      },
      features: [
        'Unlimited books',
        'Unlimited downloads',
        'Offline reading',
        'Priority support',
        'Early access to new releases',
        'Ad-free experience',
        'Exclusive author events',
      ],
    },
    
    premiumAnnual: {
      name: 'Premium Annual Subscription',
      description: 'Unlimited access for one year at a discounted rate',
      type: 'recurring',
      interval: 'year',
      intervalCount: 1,
      metadata: {
        plan_id: 'premium_annual',
        plan_name: 'Premium Annual',
        books_per_month: 'unlimited',
        download_limit: 'unlimited',
      },
      features: [
        'Unlimited books',
        'Unlimited downloads',
        'Offline reading',
        'Priority support',
        'Early access to new releases',
        'Ad-free experience',
        'Exclusive author events',
        'Save 16% compared to monthly',
      ],
    },
  },
  
  // ---------------------------------------------------------------------------
  // Custom Book Service
  // ---------------------------------------------------------------------------
  customBook: {
    name: 'Custom Book Writing Service',
    description: 'Professional custom book writing service',
    type: 'one_time',
    metadata: {
      category: 'service',
      service_type: 'custom_book',
    },
  },
  
  // ---------------------------------------------------------------------------
  // Gift Cards
  // ---------------------------------------------------------------------------
  giftCards: {
    name: 'Gift Card',
    description: 'Give the gift of reading',
    type: 'one_time',
    metadata: {
      category: 'gift',
      type: 'gift_card',
    },
    denominations: [10, 25, 50, 100],
  },
  
  // ---------------------------------------------------------------------------
  // Price Configuration
  // ---------------------------------------------------------------------------
  prices: {
    // Book prices - dynamic based on book
    book: {
      currency: 'usd',
      unit_amount: null, // Set per book
      tax_behavior: 'exclusive',
    },
    
    // Basic monthly subscription
    basic_monthly: {
      currency: 'usd',
      unit_amount: 999, // $9.99 in cents
      recurring: {
        interval: 'month',
        interval_count: 1,
        trial_period_days: 7,
      },
      tax_behavior: 'exclusive',
    },
    
    // Premium monthly subscription
    premium_monthly: {
      currency: 'usd',
      unit_amount: 1999, // $19.99 in cents
      recurring: {
        interval: 'month',
        interval_count: 1,
        trial_period_days: 7,
      },
      tax_behavior: 'exclusive',
    },
    
    // Premium annual subscription (16% discount)
    premium_annual: {
      currency: 'usd',
      unit_amount: 19999, // $199.99 in cents
      recurring: {
        interval: 'year',
        interval_count: 1,
        trial_period_days: 7,
      },
      tax_behavior: 'exclusive',
    },
    
    // Custom book base price
    custom_book_base: {
      currency: 'usd',
      unit_amount: 19900, // $199.00 in cents
      tax_behavior: 'exclusive',
    },
    
    // Gift card denominations
    giftCard: {
      currency: 'usd',
      tax_behavior: 'exclusive',
    },
  },
  
  // ---------------------------------------------------------------------------
  // Product Creation Helper
  // ---------------------------------------------------------------------------
  async createOrUpdateProducts(stripe) {
    const results = [];
    
    // Create/update subscription products
    for (const [key, plan] of Object.entries(this.subscriptions)) {
      try {
        // Find or create product
        let product = await stripe.products.list({
          active: true,
          limit: 100,
        }).then(products => products.data.find(p => p.metadata?.plan_id === key));
        
        if (!product) {
          product = await stripe.products.create({
            name: plan.name,
            description: plan.description,
            metadata: plan.metadata,
          });
        }
        
        // Create price for product
        const priceConfig = this.prices[`${key}_monthly`] || this.prices[`${key}`];
        if (priceConfig) {
          const price = await stripe.prices.create({
            product: product.id,
            ...priceConfig,
            metadata: {
              plan_id: key,
              ...plan.metadata,
            },
          });
          
          results.push({
            product: key,
            productId: product.id,
            priceId: price.id,
          });
        }
      } catch (error) {
        console.error(`Error creating product ${key}:`, error);
      }
    }
    
    return results;
  },
  
  // ---------------------------------------------------------------------------
  // Get Price ID for Product (Helper)
  // ---------------------------------------------------------------------------
  getPriceId(productKey, isAnnual = false) {
    const priceMap = {
      basic: 'price_basic_monthly',
      premium: isAnnual ? 'price_premium_annual' : 'price_premium_monthly',
    };
    
    return priceMap[productKey];
  },
  
  // ---------------------------------------------------------------------------
  // Session Configuration
  // ---------------------------------------------------------------------------
  sessionConfig: {
    mode: 'payment', // or 'subscription' for recurring
    success_url: 'https://abdulboy-ebook.com/payment-success?session_id={CHECKOUT_SESSION_ID}',
    cancel_url: 'https://abdulboy-ebook.com/payment-cancel',
    payment_method_types: ['card'],
    billing_address_collection: 'auto',
    shipping_address_collection: null,
    allow_promotion_codes: true,
    tax_id_collection: {
      enabled: false,
    },
    automatic_tax: {
      enabled: true,
    },
    customer_update: {
      address: 'auto',
      name: 'auto',
    },
  },
};

module.exports = stripeProducts;
