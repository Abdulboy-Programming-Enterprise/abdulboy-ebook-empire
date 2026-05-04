// =============================================================================
// EMAIL CONFIGURATION
// =============================================================================

module.exports = {
  // Email Provider (sendgrid, smtp, mailgun)
  provider: process.env.EMAIL_PROVIDER || 'sendgrid',
  
  // SMTP Configuration (fallback)
  smtp: {
    host: process.env.SMTP_HOST || 'smtp.gmail.com',
    port: parseInt(process.env.SMTP_PORT) || 587,
    secure: process.env.SMTP_SECURE === 'true',
    auth: {
      user: process.env.SMTP_USER,
      pass: process.env.SMTP_PASSWORD,
    },
  },
  
  // SendGrid Configuration
  sendgrid: {
    apiKey: process.env.SENDGRID_API_KEY,
  },
  
  // Mailgun Configuration
  mailgun: {
    apiKey: process.env.MAILGUN_API_KEY,
    domain: process.env.MAILGUN_DOMAIN,
    region: process.env.MAILGUN_REGION || 'us',
  },
  
  // Default Sender
  from: {
    email: process.env.EMAIL_FROM || 'noreply@abdulboy-ebook.com',
    name: process.env.EMAIL_FROM_NAME || 'Abdulboy Ebook Empire',
  },
  
  // Reply To
  replyTo: {
    email: 'support@abdulboy-ebook.com',
    name: 'Abdulboy Support',
  },
  
  // Email Templates Directory
  templates: {
    dir: './configs/email/templates',
    engine: 'handlebars',
  },
  
  // Queue Configuration
  queue: {
    enabled: true,
    concurrency: 5,
    retryAttempts: 3,
    retryDelay: 5000, // milliseconds
  },
  
  // Rate Limiting
  rateLimit: {
    enabled: true,
    maxPerMinute: 100,
    maxPerHour: 1000,
    maxPerDay: 10000,
  },
  
  // Email Categories
  categories: {
    transactional: {
      priority: 'high',
      trackOpens: true,
      trackClicks: true,
    },
    marketing: {
      priority: 'low',
      trackOpens: true,
      trackClicks: true,
      unsubscribeLink: true,
    },
    notification: {
      priority: 'medium',
      trackOpens: false,
      trackClicks: true,
    },
  },
  
  // Template Mapping
  templates: {
    welcome: {
      subject: 'Welcome to Abdulboy Ebook Empire!',
      category: 'transactional',
    },
    'purchase-confirmation': {
      subject: 'Your Purchase Confirmation - Order #{orderId}',
      category: 'transactional',
    },
    'booking-received': {
      subject: 'Custom Book Request Received - #{bookingId}',
      category: 'transactional',
    },
    'password-reset': {
      subject: 'Reset Your Password',
      category: 'transactional',
    },
    'payment-success': {
      subject: 'Payment Successful - Thank You!',
      category: 'transactional',
    },
    'payment-failed': {
      subject: 'Payment Failed - Action Required',
      category: 'transactional',
    },
    'subscription-activated': {
      subject: 'Your Subscription is Active!',
      category: 'transactional',
    },
    'subscription-expiring': {
      subject: 'Your Subscription Expires Soon',
      category: 'transactional',
    },
    'subscription-expired': {
      subject: 'Your Subscription Has Expired',
      category: 'transactional',
    },
    'new-book-available': {
      subject: 'New Book Available: {bookTitle}',
      category: 'marketing',
    },
    'weekly-digest': {
      subject: 'Your Weekly Reading Digest',
      category: 'marketing',
    },
    'custom-booking-update': {
      subject: 'Custom Book Update - #{bookingId}',
      category: 'notification',
    },
  },
};
