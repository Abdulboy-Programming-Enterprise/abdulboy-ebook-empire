// =============================================================================
// SITE CONFIGURATION - Abdulboy Ebook Empire
// =============================================================================
// Central configuration for the entire application
// =============================================================================

const siteConfig = {
  // ---------------------------------------------------------------------------
  // Basic Site Information
  // ---------------------------------------------------------------------------
  site: {
    name: 'Abdulboy Ebook Empire',
    tagline: 'Empowering African Authors, One Ebook at a Time',
    description: 'World-class ebook platform with AI recommendations, multi-payment integration, and subscription services.',
    domain: 'abdulboy-ebook.com',
    url: process.env.NODE_ENV === 'production' 
      ? 'https://abdulboy-ebook.com' 
      : 'http://localhost:3000',
    apiUrl: process.env.NODE_ENV === 'production'
      ? 'https://api.abdulboy-ebook.com'
      : 'http://localhost:8000',
    adminUrl: process.env.NODE_ENV === 'production'
      ? 'https://admin.abdulboy-ebook.com'
      : 'http://localhost:3000/admin',
  },

  // ---------------------------------------------------------------------------
  // Branding
  // ---------------------------------------------------------------------------
  branding: {
    logo: {
      light: '/images/logo/logo-light.svg',
      dark: '/images/logo/logo-dark.svg',
      icon: '/images/logo/logo-icon.svg',
      favicon: '/images/logo/favicon.ico',
    },
    colors: {
      primary: '#6366f1',
      secondary: '#8b5cf6',
      accent: '#ec4899',
      success: '#10b981',
      warning: '#f59e0b',
      error: '#ef4444',
      dark: '#1f2937',
      light: '#f9fafb',
    },
    fonts: {
      heading: 'Playfair Display, serif',
      body: 'Inter, sans-serif',
      mono: 'JetBrains Mono, monospace',
    },
  },

  // ---------------------------------------------------------------------------
  // Feature Flags
  // ---------------------------------------------------------------------------
  features: {
    enableGamification: true,
    enableWatermarking: true,
    enableOptimization: true,
    enableAffiliate: false,
    enableSocialLogin: false,
    enableBookPreview: true,
    enablePDFCompression: true,
    enablePushNotifications: true,
    enableOfflineReading: true,
    enableAudioBooks: false,
    enableAuthorPortal: true,
  },

  // ---------------------------------------------------------------------------
  // Subscription Plans
  // ---------------------------------------------------------------------------
  subscriptions: {
    plans: [
      {
        id: 'free',
        name: 'Free',
        price: 0,
        currency: 'USD',
        interval: 'month',
        features: [
          'Access to free books only',
          'Limited previews (first 10 pages)',
          'Basic support',
          '3 books per month maximum',
        ],
        limits: {
          booksPerMonth: 3,
          downloadsPerMonth: 3,
          canDownload: false,
          canReadOffline: false,
        },
        isPopular: false,
      },
      {
        id: 'basic',
        name: 'Basic',
        price: 9.99,
        currency: 'USD',
        interval: 'month',
        features: [
          'Access to all books',
          '10 books per month',
          'Download up to 5 books',
          'Email support',
          'Bookmark synchronization',
        ],
        limits: {
          booksPerMonth: 10,
          downloadsPerMonth: 5,
          canDownload: true,
          canReadOffline: true,
        },
        isPopular: false,
      },
      {
        id: 'premium',
        name: 'Premium',
        price: 19.99,
        currency: 'USD',
        interval: 'month',
        features: [
          'Unlimited books',
          'Unlimited downloads',
          'Offline reading',
          'Priority support',
          'Early access to new releases',
          'Ad-free experience',
          'Exclusive author events',
        ],
        limits: {
          booksPerMonth: null,
          downloadsPerMonth: null,
          canDownload: true,
          canReadOffline: true,
        },
        isPopular: true,
      },
    ],
    annualDiscount: 0.16, // 16% discount on annual plans
    trialDays: 7,
  },

  // ---------------------------------------------------------------------------
  // Payment Configuration
  // ---------------------------------------------------------------------------
  payments: {
    providers: {
      stripe: {
        enabled: true,
        publicKey: process.env.STRIPE_PUBLIC_KEY,
        currency: 'usd',
        supportedCards: ['visa', 'mastercard', 'amex'],
      },
      opay: {
        enabled: true,
        merchantId: process.env.OPAY_MERCHANT_ID,
        currency: 'ngn',
        supportedMethods: ['card', 'bank', 'ussd', 'transfer'],
      },
      paypal: {
        enabled: false,
        currency: 'usd',
      },
      flutterwave: {
        enabled: false,
        currency: 'ngn',
      },
    },
    defaultProvider: 'stripe',
    testMode: process.env.NODE_ENV !== 'production',
  },

  // ---------------------------------------------------------------------------
  // Book Configuration
  // ---------------------------------------------------------------------------
  books: {
    maxUploadSize: 50 * 1024 * 1024, // 50MB
    allowedFormats: ['pdf', 'epub', 'mobi'],
    previewPages: {
      free: 10,
      basic: 30,
      premium: null, // Unlimited preview for premium
      nonSubscriber: 5,
    },
    enableWatermarkByDefault: true,
    maxTagsPerBook: 10,
    coverImage: {
      sizes: {
        thumb: { width: 100, height: 150 },
        medium: { width: 200, height: 300 },
        large: { width: 400, height: 600 },
      },
      formats: ['jpg', 'png', 'webp'],
      maxSize: 5 * 1024 * 1024, // 5MB
    },
  },

  // ---------------------------------------------------------------------------
  // UI/UX Configuration
  // ---------------------------------------------------------------------------
  ui: {
    theme: {
      default: 'light',
      options: ['light', 'dark', 'system'],
      localStorageKey: 'abdulboy-theme',
    },
    textSize: {
      default: 100,
      min: 75,
      max: 150,
      step: 5,
      localStorageKey: 'abdulboy-text-size',
    },
    animations: {
      enabled: true,
      duration: 300,
      reduceMotion: false,
    },
    pagination: {
      defaultPageSize: 20,
      options: [10, 20, 50, 100],
    },
    toasts: {
      duration: 5000,
      position: 'bottom-right',
    },
  },

  // ---------------------------------------------------------------------------
  // SEO & Analytics
  // ---------------------------------------------------------------------------
  seo: {
    defaultTitle: 'Abdulboy Ebook Empire - World-Class Ebook Platform',
    defaultDescription: 'Buy, read, and discover thousands of ebooks from African authors. Subscription plans available.',
    defaultKeywords: 'ebooks, digital books, African authors, online reading, book subscription',
    twitterHandle: '@AbdulboyEbook',
    facebookAppId: '',
    googleAnalyticsId: process.env.GA_TRACKING_ID,
    sentryDsn: process.env.SENTRY_DSN,
  },

  // ---------------------------------------------------------------------------
  // Security
  // ---------------------------------------------------------------------------
  security: {
    rateLimits: {
      api: { window: 60, max: 100 },
      auth: { window: 60, max: 5 },
      payment: { window: 60, max: 20 },
      upload: { window: 3600, max: 50 },
    },
    sessionTimeout: 30 * 60 * 1000, // 30 minutes
    passwordRequirements: {
      minLength: 8,
      requireUppercase: true,
      requireLowercase: true,
      requireNumbers: true,
      requireSpecialChars: true,
    },
    jwtExpiry: {
      access: '30m',
      refresh: '7d',
      reset: '1h',
    },
  },

  // ---------------------------------------------------------------------------
  // Caching
  // ---------------------------------------------------------------------------
  cache: {
    ttl: {
      books: 3600, // 1 hour
      categories: 86400, // 24 hours
      search: 300, // 5 minutes
      userProfile: 1800, // 30 minutes
    },
    invalidationEvents: ['book.published', 'book.updated', 'user.subscription.changed'],
  },

  // ---------------------------------------------------------------------------
  // CDN
  // ---------------------------------------------------------------------------
  cdn: {
    enabled: process.env.NODE_ENV === 'production',
    url: process.env.CDN_URL || '',
    imageOptimization: {
      quality: 80,
      format: 'webp',
    },
  },

  // ---------------------------------------------------------------------------
  // Social Links
  // ---------------------------------------------------------------------------
  social: {
    twitter: 'https://twitter.com/AbdulboyEbook',
    facebook: 'https://facebook.com/AbdulboyEbook',
    instagram: 'https://instagram.com/AbdulboyEbook',
    linkedin: 'https://linkedin.com/company/abdulboy-ebook',
    github: 'https://github.com/abdulboy/abdulboy-ebook-empire',
  },

  // ---------------------------------------------------------------------------
  // Support Contact
  // ---------------------------------------------------------------------------
  support: {
    email: 'support@abdulboy-ebook.com',
    phone: '+234 123 456 7890',
    whatsapp: '+234 123 456 7890',
    hours: 'Mon-Fri, 9 AM - 6 PM WAT',
  },

  // ---------------------------------------------------------------------------
  // Legal
  // ---------------------------------------------------------------------------
  legal: {
    company: 'Abdulboy Programming Enterprise',
    address: 'Lagos, Nigeria',
    copyrightYear: 2026,
    copyrightHolder: 'Abdulboy Programming Enterprise',
    termsUrl: '/terms',
    privacyUrl: '/privacy',
    cookiePolicyUrl: '/cookies',
  },

  // ---------------------------------------------------------------------------
  // PWA Configuration
  // ---------------------------------------------------------------------------
  pwa: {
    enabled: true,
    cacheName: 'abdulboy-ebook-v1',
    offlinePage: '/offline.html',
    assetsToCache: [
      '/',
      '/index.html',
      '/styles/main.css',
      '/scripts/main.js',
      '/images/logo/logo-icon.svg',
    ],
    apiCacheStrategy: 'network-first',
    staticCacheStrategy: 'cache-first',
  },
};

// -----------------------------------------------------------------------------
// Environment-specific overrides
// -----------------------------------------------------------------------------
if (process.env.NODE_ENV === 'development') {
  siteConfig.cache.ttl.books = 60; // 1 minute for development
  siteConfig.payments.testMode = true;
  siteConfig.security.rateLimits.api.max = 1000; // Higher limit for dev
}

if (process.env.NODE_ENV === 'production') {
  siteConfig.cdn.enabled = true;
  siteConfig.payments.testMode = false;
}

// -----------------------------------------------------------------------------
// Export configuration
// -----------------------------------------------------------------------------
if (typeof module !== 'undefined' && module.exports) {
  module.exports = siteConfig;
}

if (typeof window !== 'undefined') {
  window.siteConfig = siteConfig;
}
