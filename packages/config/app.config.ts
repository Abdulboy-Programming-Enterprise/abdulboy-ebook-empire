// =============================================================================
// APPLICATION CONFIGURATION - TypeScript Definitions
// =============================================================================

export interface AppConfig {
  site: SiteConfig;
  api: ApiConfig;
  auth: AuthConfig;
  features: FeatureFlags;
  pagination: PaginationConfig;
  upload: UploadConfig;
  payments: PaymentConfig;
}

export interface SiteConfig {
  name: string;
  shortName: string;
  tagline: string;
  description: string;
  url: string;
  apiUrl: string;
  adminUrl: string;
}

export interface ApiConfig {
  baseUrl: string;
  timeout: number;
  retries: number;
  endpoints: {
    auth: AuthEndpoints;
    books: BookEndpoints;
    payments: PaymentEndpoints;
    subscriptions: SubscriptionEndpoints;
    bookings: BookingEndpoints;
    users: UserEndpoints;
  };
}

export interface AuthEndpoints {
  login: string;
  register: string;
  logout: string;
  refresh: string;
  me: string;
}

export interface BookEndpoints {
  list: string;
  search: string;
  details: string;
  preview: string;
  download: string;
}

export interface PaymentEndpoints {
  create: string;
  verify: string;
  webhook: string;
}

export interface SubscriptionEndpoints {
  plans: string;
  subscribe: string;
  cancel: string;
  webhook: string;
}

export interface BookingEndpoints {
  create: string;
  list: string;
  details: string;
  update: string;
}

export interface UserEndpoints {
  profile: string;
  update: string;
  wishlist: string;
  readingProgress: string;
  notifications: string;
}

export interface AuthConfig {
  tokenKey: string;
  refreshTokenKey: string;
  userKey: string;
  loginRedirect: string;
  logoutRedirect: string;
  sessionTimeout: number;
}

export interface FeatureFlags {
  enableGamification: boolean;
  enableWatermarking: boolean;
  enableOptimization: boolean;
  enableChatbot: boolean;
  enableOfflineReading: boolean;
  enablePushNotifications: boolean;
  enableAffiliate: boolean;
}

export interface PaginationConfig {
  defaultPageSize: number;
  maxPageSize: number;
  pageSizes: number[];
}

export interface UploadConfig {
  maxSize: number;
  allowedTypes: string[];
  maxFiles: number;
}

export interface PaymentConfig {
  stripe: StripeConfig;
  opay: OPayConfig;
}

export interface StripeConfig {
  enabled: boolean;
  publicKey: string;
  currency: string;
}

export interface OPayConfig {
  enabled: boolean;
  merchantId: string;
  currency: string;
}

// Default configuration
export const defaultConfig: AppConfig = {
  site: {
    name: 'Abdulboy Ebook Empire',
    shortName: 'ABE',
    tagline: 'Empowering African Authors, One Ebook at a Time',
    description: 'World-class ebook platform with AI recommendations.',
    url: 'http://localhost:3000',
    apiUrl: 'http://localhost:8000',
    adminUrl: 'http://localhost:3000/admin'
  },
  api: {
    baseUrl: 'http://localhost:8000',
    timeout: 30000,
    retries: 3,
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
        cancel: '/api/v1/subscriptions/cancel',
        webhook: '/api/v1/webhooks/stripe'
      },
      bookings: {
        create: '/api/v1/bookings',
        list: '/api/v1/bookings',
        details: '/api/v1/bookings/:id',
        update: '/api/v1/bookings/:id'
      },
      users: {
        profile: '/api/v1/users/me',
        update: '/api/v1/users/me',
        wishlist: '/api/v1/users/wishlist',
        readingProgress: '/api/v1/users/reading-progress',
        notifications: '/api/v1/users/notifications'
      }
    }
  },
  auth: {
    tokenKey: 'access_token',
    refreshTokenKey: 'refresh_token',
    userKey: 'user',
    loginRedirect: '/user-dashboard.html',
    logoutRedirect: '/',
    sessionTimeout: 30 * 60 * 1000
  },
  features: {
    enableGamification: true,
    enableWatermarking: true,
    enableOptimization: true,
    enableChatbot: true,
    enableOfflineReading: true,
    enablePushNotifications: true,
    enableAffiliate: false
  },
  pagination: {
    defaultPageSize: 20,
    maxPageSize: 100,
    pageSizes: [10, 20, 50, 100]
  },
  upload: {
    maxSize: 50 * 1024 * 1024,
    allowedTypes: ['image/jpeg', 'image/png', 'image/webp', 'application/pdf'],
    maxFiles: 5
  },
  payments: {
    stripe: {
      enabled: true,
      publicKey: '',
      currency: 'usd'
    },
    opay: {
      enabled: true,
      merchantId: '',
      currency: 'ngn'
    }
  }
};

// Environment-specific overrides
if (process.env.NODE_ENV === 'production') {
  defaultConfig.site.url = 'https://abdulboy-ebook.com';
  defaultConfig.site.apiUrl = 'https://api.abdulboy-ebook.com';
  defaultConfig.site.adminUrl = 'https://admin.abdulboy-ebook.com';
  defaultConfig.api.baseUrl = 'https://api.abdulboy-ebook.com';
}
