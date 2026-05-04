// =============================================================================
// SITE CONFIGURATION - Shared Configuration
// =============================================================================

const siteConfig = {
  // Site Information
  site: {
    name: 'Abdulboy Ebook Empire',
    shortName: 'ABE',
    tagline: 'Empowering African Authors, One Ebook at a Time',
    description: 'World-class ebook platform with AI recommendations, multi-payment integration, and subscription services.',
    url: process.env.NODE_ENV === 'production' 
      ? 'https://abdulboy-ebook.com' 
      : 'http://localhost:3000',
    apiUrl: process.env.NODE_ENV === 'production'
      ? 'https://api.abdulboy-ebook.com'
      : 'http://localhost:8000',
    adminUrl: process.env.NODE_ENV === 'production'
      ? 'https://admin.abdulboy-ebook.com'
      : 'http://localhost:3000/admin'
  },
  
  // Branding
  branding: {
    colors: {
      primary: '#6366f1',
      secondary: '#8b5cf6',
      accent: '#ec4899',
      success: '#10b981',
      warning: '#f59e0b',
      error: '#ef4444',
      dark: '#1f2937',
      light: '#f9fafb'
    }
  },
  
  // API Endpoints
  api: {
    endpoints: {
      auth: {
        login: '/api/v1/auth/login',
        register: '/api/v1/auth/register',
        logout: '/api/v1/auth/logout',
        refresh: '/api/v1/auth/refresh',
        me: '/api/v1/users/me'
      },
      books: {
        list: '/api/v1/books',
        search: '/api/v1/books/search',
        details: '/api/v1/books/:id',
        preview: '/api/v1/books/:id/preview',
        download: '/api/v1/books/:id/download'
      },
      payments: {
        create: '/api/v1/payments/create',
        verify: '/api/v1/payments/verify',
        webhook: '/api/v1/webhooks/:provider'
      },
      subscriptions: {
        plans: '/api/v1/subscriptions/plans',
        subscribe: '/api/v1/subscriptions/subscribe',
        cancel: '/api/v1/subscriptions/cancel'
      },
      bookings: {
        create: '/api/v1/bookings',
        list: '/api/v1/bookings',
        details: '/api/v1/bookings/:id'
      }
    },
    timeout: 30000,
    retries: 3
  },
  
  // Pagination
  pagination: {
    defaultPageSize: 20,
    maxPageSize: 100,
    pageSizes: [10, 20, 50, 100]
  },
  
  // File Upload
  upload: {
    maxSize: 50 * 1024 * 1024, // 50MB
    allowedTypes: ['image/jpeg', 'image/png', 'image/webp', 'application/pdf'],
    maxFiles: 5
  },
  
  // Authentication
  auth: {
    tokenKey: 'access_token',
    refreshTokenKey: 'refresh_token',
    userKey: 'user',
    loginRedirect: '/user-dashboard.html',
    logoutRedirect: '/'
  },
  
  // Features
  features: {
    enableGamification: true,
    enableWatermarking: true,
    enableOptimization: true,
    enableChatbot: true,
    enableOfflineReading: true
  },
  
  // Payment Providers
  payments: {
    stripe: {
      enabled: true,
      publicKey: process.env.STRIPE_PUBLIC_KEY || ''
    },
    opay: {
      enabled: true,
      merchantId: process.env.OPAY_MERCHANT_ID || ''
    }
  },
  
  // Social Links
  social: {
    twitter: 'https://twitter.com/AbdulboyEbook',
    facebook: 'https://facebook.com/AbdulboyEbook',
    instagram: 'https://instagram.com/AbdulboyEbook',
    linkedin: 'https://linkedin.com/company/abdulboy-ebook',
    github: 'https://github.com/abdulboy/abdulboy-ebook-empire'
  },
  
  // Support
  support: {
    email: 'support@abdulboy-ebook.com',
    phone: '+234 123 456 7890',
    whatsapp: '+234 123 456 7890'
  },
  
  // Legal
  legal: {
    company: 'Abdulboy Programming Enterprise',
    address: 'Lagos, Nigeria',
    copyrightYear: 2026,
    copyrightHolder: 'Abdulboy Programming Enterprise'
  }
};

// Export for different environments
if (typeof module !== 'undefined' && module.exports) {
  module.exports = siteConfig;
}

if (typeof window !== 'undefined') {
  window.siteConfig = siteConfig;
}
