// =============================================================================
// ANALYTICS.JS - User Behavior Tracking
// =============================================================================

class AnalyticsTracker {
  constructor() {
    this.sessionId = this.getOrCreateSessionId();
    this.trackingEnabled = true;
    this.eventsQueue = [];
    this.flushInterval = null;
  }

  init() {
    if (!this.trackingEnabled) return;
    
    // Start periodic flush
    this.flushInterval = setInterval(() => this.flushEvents(), 30000);
    
    // Track page view
    this.trackPageView();
    
    // Track page unload
    window.addEventListener('beforeunload', () => {
      this.flushEvents(true);
    });
    
    // Track visibility change
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        this.flushEvents();
      }
    });
    
    // Set up automatic event tracking
    this.setupAutoTracking();
  }

  // ===========================================================================
  // SECURE SESSION ID GENERATION - CRYPTOGRAPHICALLY SECURE
  // ===========================================================================

  getOrCreateSessionId() {
    let sessionId = sessionStorage.getItem('analytics_session_id');
    if (!sessionId) {
      sessionId = this.generateSecureSessionId();
      sessionStorage.setItem('analytics_session_id', sessionId);
    }
    return sessionId;
  }

  /**
   * Generates a cryptographically secure UUID v4-like identifier
   * Uses crypto.randomUUID() if available, falls back to crypto.getRandomValues()
   * @returns {string} Secure UUID v4-like string
   */
  generateSecureSessionId() {
    // Option 1: Use crypto.randomUUID() (modern browsers)
    if (window.crypto && window.crypto.randomUUID) {
      return crypto.randomUUID();
    }
    
    // Option 2: Fallback to crypto.getRandomValues() (all modern browsers)
    if (window.crypto && window.crypto.getRandomValues) {
      const array = new Uint8Array(16);
      crypto.getRandomValues(array);
      
      // Set version (4) and variant (8, 9, A, or B)
      array[6] = (array[6] & 0x0f) | 0x40;
      array[8] = (array[8] & 0x3f) | 0x80;
      
      // Convert to hex string in UUID format
      const hex = Array.from(array)
        .map(b => b.toString(16).padStart(2, '0'))
        .join('');
      
      return hex.substr(0, 8) + '-' + hex.substr(8, 4) + '-' + 
             hex.substr(12, 4) + '-' + hex.substr(16, 4) + '-' + 
             hex.substr(20, 12);
    }
    
    // Option 3: Last resort fallback (should never happen in modern browsers)
    console.warn('Crypto API not available for session ID generation');
    return this.generateFallbackId();
  }

  /**
   * Fallback ID generator - only used when crypto is unavailable
   * @returns {string} Fallback ID
   */
  generateFallbackId() {
    const timestamp = Date.now().toString(36);
    const random = Math.random().toString(36).substr(2, 9);
    return timestamp + '-' + random;
  }

  // ===========================================================================
  // EVENT TRACKING
  // ===========================================================================

  async trackEvent(eventType, eventData = {}) {
    if (!this.trackingEnabled) return;
    
    const event = {
      event_type: eventType,
      event_data: eventData,
      session_id: this.sessionId,
      timestamp: new Date().toISOString(),
      url: window.location.href,
      referrer: document.referrer,
      screen_size: `${window.innerWidth}x${window.innerHeight}`,
      user_agent: navigator.userAgent
    };
    
    this.eventsQueue.push(event);
    
    // Flush if queue is large
    if (this.eventsQueue.length >= 10) {
      this.flushEvents();
    }
  }

  trackPageView() {
    this.trackEvent('page_view', {
      page: window.location.pathname,
      title: document.title
    });
  }

  trackBookView(bookId, bookTitle) {
    this.trackEvent('book_view', {
      book_id: bookId,
      book_title: bookTitle
    });
  }

  trackSearch(query, resultsCount) {
    this.trackEvent('search', {
      query: query,
      results_count: resultsCount
    });
  }

  trackPurchase(bookId, amount, paymentMethod) {
    this.trackEvent('purchase', {
      book_id: bookId,
      amount: amount,
      payment_method: paymentMethod
    });
  }

  trackLogin(method) {
    this.trackEvent('login', { method: method });
  }

  trackSignup(method) {
    this.trackEvent('signup', { method: method });
  }

  trackSubscription(planId, planName) {
    this.trackEvent('subscription', {
      plan_id: planId,
      plan_name: planName
    });
  }

  trackCustomBooking(bookingId) {
    this.trackEvent('custom_booking', { booking_id: bookingId });
  }

  trackError(errorType, errorMessage) {
    this.trackEvent('error', {
      error_type: errorType,
      error_message: errorMessage
    });
  }

  trackOutboundLink(url) {
    this.trackEvent('outbound_link', { url: url });
  }

  trackDownload(fileUrl, fileType) {
    this.trackEvent('download', {
      file_url: fileUrl,
      file_type: fileType
    });
  }

  // ===========================================================================
  // EVENT FLUSHING
  // ===========================================================================

  async flushEvents(sync = false) {
    if (this.eventsQueue.length === 0) return;
    
    const events = [...this.eventsQueue];
    this.eventsQueue = [];
    
    const token = localStorage.getItem('access_token');
    
    const fetchOptions = {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ events: events })
    };
    
    if (token) {
      fetchOptions.headers['Authorization'] = `Bearer ${token}`;
    }
    
    try {
      if (sync) {
        // Use sendBeacon for page unload events
        const blob = new Blob([JSON.stringify({ events: events })], { 
          type: 'application/json' 
        });
        const sent = navigator.sendBeacon('/api/v1/analytics/batch', blob);
        if (!sent) {
          // If sendBeacon fails, fallback to fetch
          await fetch('/api/v1/analytics/batch', fetchOptions);
        }
      } else {
        const response = await fetch('/api/v1/analytics/batch', fetchOptions);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
      }
    } catch (error) {
      console.error('Failed to send analytics events:', error);
      // Re-add events to queue for retry (limit to prevent infinite growth)
      if (this.eventsQueue.length < 100) {
        this.eventsQueue.unshift(...events);
      } else {
        console.warn('Analytics queue overflow, dropping events');
      }
    }
  }

  // ===========================================================================
  // AUTO TRACKING
  // ===========================================================================

  setupAutoTracking() {
    // Track outbound links
    document.addEventListener('click', (e) => {
      const link = e.target.closest('a');
      if (link && link.href) {
        try {
          const url = new URL(link.href);
          if (url.hostname !== window.location.hostname) {
            this.trackOutboundLink(link.href);
          }
        } catch {
          // Invalid URL, skip
        }
      }
    });
    
    // Track downloads
    document.addEventListener('click', (e) => {
      const link = e.target.closest('a');
      if (link && link.href) {
        const fileExtensions = ['.pdf', '.epub', '.mobi', '.zip', '.csv', '.xlsx'];
        if (fileExtensions.some(ext => link.href.toLowerCase().endsWith(ext))) {
          const fileType = link.href.split('.').pop() || 'unknown';
          this.trackDownload(link.href, fileType);
        }
      }
    });
    
    // Track scroll depth
    let maxScrollDepth = 0;
    const scrollHandler = this.throttle(() => {
      const scrollHeight = document.documentElement.scrollHeight - window.innerHeight;
      if (scrollHeight <= 0) return;
      
      const scrollPercent = (window.scrollY / scrollHeight) * 100;
      if (scrollPercent > maxScrollDepth + 25) {
        maxScrollDepth = Math.floor(scrollPercent / 25) * 25;
        this.trackEvent('scroll_depth', { depth: maxScrollDepth });
      }
    }, 1000);
    
    window.addEventListener('scroll', scrollHandler);
    
    // Track time on page
    let startTime = Date.now();
    window.addEventListener('beforeunload', () => {
      const timeSpent = Math.round((Date.now() - startTime) / 1000);
      if (timeSpent > 5) {
        this.trackEvent('time_on_page', { seconds: timeSpent });
      }
    });
  }

  // ===========================================================================
  // UTILITY METHODS
  // ===========================================================================

  /**
   * Throttle function to limit event frequency
   * @param {Function} fn - Function to throttle
   * @param {number} delay - Throttle delay in milliseconds
   * @returns {Function} Throttled function
   */
  throttle(fn, delay) {
    let lastCall = 0;
    return function(...args) {
      const now = Date.now();
      if (now - lastCall >= delay) {
        lastCall = now;
        fn.apply(this, args);
      }
    };
  }

  async getUserCohort() {
    // Determine user cohort based on signup date
    const token = localStorage.getItem('access_token');
    if (!token) return null;
    
    try {
      const response = await fetch('/api/v1/users/me', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data.success && data.data?.created_at) {
        const signupDate = new Date(data.data.created_at);
        const cohort = signupDate.toISOString().slice(0, 7); // YYYY-MM
        return cohort;
      }
    } catch (error) {
      console.error('Failed to get user cohort:', error);
    }
    return null;
  }

  /**
   * Clean up resources when analytics is destroyed
   */
  destroy() {
    if (this.flushInterval) {
      clearInterval(this.flushInterval);
      this.flushInterval = null;
    }
    this.flushEvents(true);
  }
}

// Helper function to get file extension
function getFileExtension(url) {
  try {
    const parts = url.split('.');
    return parts.length > 1 ? parts.pop() || 'unknown' : 'unknown';
  } catch {
    return 'unknown';
  }
}

// Initialize analytics tracker
window.analytics = new AnalyticsTracker();

document.addEventListener('DOMContentLoaded', () => {
  window.analytics.init();
});
