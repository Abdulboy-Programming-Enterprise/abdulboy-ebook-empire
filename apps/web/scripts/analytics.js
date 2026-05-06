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

  getOrCreateSessionId() {
    let sessionId = sessionStorage.getItem('analytics_session_id');
    if (!sessionId) {
      sessionId = this.generateUUID();
      sessionStorage.setItem('analytics_session_id', sessionId);
    }
    return sessionId;
  }

  generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      const r = Math.random() * 16 | 0;
      const v = c === 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  }

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
        const blob = new Blob([JSON.stringify({ events: events })], { type: 'application/json' });
        navigator.sendBeacon('/api/v1/analytics/batch', blob);
      } else {
        await fetch('/api/v1/analytics/batch', fetchOptions);
      }
    } catch (error) {
      console.error('Failed to send analytics events:', error);
      // Re-add events to queue for retry
      this.eventsQueue.unshift(...events);
    }
  }

  setupAutoTracking() {
    // Track outbound links
    document.addEventListener('click', (e) => {
      const link = e.target.closest('a');
      if (link && link.href) {
        const url = new URL(link.href);
        if (url.hostname !== window.location.hostname) {
          this.trackOutboundLink(link.href);
        }
      }
    });
    
    // Track downloads
    document.addEventListener('click', (e) => {
      const link = e.target.closest('a');
      if (link && link.href) {
        const fileExtensions = ['.pdf', '.epub', '.mobi', '.zip', '.csv', '.xlsx'];
        if (fileExtensions.some(ext => link.href.toLowerCase().endsWith(ext))) {
          this.trackDownload(link.href, getFileExtension(link.href));
        }
      }
    });
    
    // Track scroll depth
    let maxScrollDepth = 0;
    const scrollHandler = throttle(() => {
      const scrollPercent = (window.scrollY / (document.documentElement.scrollHeight - window.innerHeight)) * 100;
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

  async getUserCohort() {
    // Determine user cohort based on signup date
    const token = localStorage.getItem('access_token');
    if (!token) return null;
    
    try {
      const response = await fetch('/api/v1/users/me', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
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
}

// Initialize analytics tracker
window.analytics = new AnalyticsTracker();

document.addEventListener('DOMContentLoaded', () => {
  window.analytics.init();
});
