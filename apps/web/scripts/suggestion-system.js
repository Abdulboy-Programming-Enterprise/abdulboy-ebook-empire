// =============================================================================
// SUGGESTION-SYSTEM.JS - AI-Powered Book Recommendations
// =============================================================================

class SuggestionSystem {
  constructor() {
    this.recommendations = [];
    this.userPreferences = this.loadUserPreferences();
    this.trackingEnabled = true;
    this.recommendationCache = new Map();
  }

  init() {
    this.setupEventListeners();
    this.loadRecommendations();
    this.trackUserBehavior();
  }

  loadUserPreferences() {
    const saved = localStorage.getItem('user_preferences');
    return saved ? JSON.parse(saved) : {
      favoriteGenres: [],
      favoriteAuthors: [],
      preferredPriceRange: { min: 0, max: 50 },
      recentlyViewed: [],
      purchasedBooks: []
    };
  }

  saveUserPreferences() {
    localStorage.setItem('user_preferences', JSON.stringify(this.userPreferences));
  }

  async loadRecommendations() {
    const token = localStorage.getItem('access_token');
    if (!token) {
      this.loadGuestRecommendations();
      return;
    }

    try {
      // Check cache
      const cacheKey = 'recommendations_' + token;
      const cached = localStorage.getItem(cacheKey);
      const cacheTime = localStorage.getItem(cacheKey + '_time');
      
      if (cached && cacheTime && (Date.now() - parseInt(cacheTime)) < 3600000) {
        this.recommendations = JSON.parse(cached);
        this.renderRecommendations();
        return;
      }

      const response = await fetch('/api/v1/suggestions/for-you', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();

      if (data.success && data.data?.suggestions) {
        this.recommendations = data.data.suggestions;
        localStorage.setItem(cacheKey, JSON.stringify(this.recommendations));
        localStorage.setItem(cacheKey + '_time', Date.now().toString());
        this.renderRecommendations();
      } else {
        this.loadPopularRecommendations();
      }
    } catch (error) {
      console.error('Failed to load recommendations:', error);
      this.loadPopularRecommendations();
    }
  }

  async loadGuestRecommendations() {
    try {
      const response = await fetch('/api/v1/suggestions/popular?limit=10');
      const data = await response.json();
      
      if (data.success && data.data?.popular_books) {
        this.recommendations = data.data.popular_books;
        this.renderRecommendations();
      }
    } catch (error) {
      console.error('Failed to load guest recommendations:', error);
    }
  }

  async loadPopularRecommendations() {
    try {
      const response = await fetch('/api/v1/suggestions/popular?limit=10');
      const data = await response.json();
      
      if (data.success && data.data?.popular_books) {
        this.recommendations = data.data.popular_books;
        this.renderRecommendations();
      }
    } catch (error) {
      console.error('Failed to load popular recommendations:', error);
    }
  }

  renderRecommendations() {
    const containers = document.querySelectorAll('.recommendations-container');
    if (containers.length === 0 || !this.recommendations.length) return;

    const recommendationsHtml = this.recommendations.map(book => `
      <div class="recommendation-card" data-book-id="${book.id}">
        <div class="rec-cover">
          <img src="${book.cover_image_url || '/images/default-book-cover.jpg'}" alt="${this.escapeHtml(book.title)}">
        </div>
        <div class="rec-info">
          <h4 class="rec-title">${this.escapeHtml(book.title)}</h4>
          <p class="rec-author">${this.escapeHtml(book.author_name)}</p>
          <div class="rec-price">${book.is_free ? 'FREE' : `$${book.price.toFixed(2)}`}</div>
          <button class="rec-view-btn" data-book-id="${book.id}">View Details</button>
        </div>
      </div>
    `).join('');

    containers.forEach(container => {
      container.innerHTML = `
        <div class="recommendations-header">
          <h3>Recommended for You</h3>
          <p>Based on your reading history</p>
        </div>
        <div class="recommendations-grid">
          ${recommendationsHtml}
        </div>
      `;
    });

    // Attach event listeners
    document.querySelectorAll('.rec-view-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const bookId = btn.dataset.bookId;
        window.location.href = `/book-preview.html?id=${bookId}`;
      });
    });
  }

  async trackUserBehavior() {
    if (!this.trackingEnabled) return;

    // Track page views
    this.trackEvent('page_view', {
      page: window.location.pathname,
      referrer: document.referrer
    });

    // Track time on page
    let startTime = Date.now();
    window.addEventListener('beforeunload', () => {
      const timeSpent = (Date.now() - startTime) / 1000;
      if (timeSpent > 5) {
        this.trackEvent('time_on_page', {
          page: window.location.pathname,
          seconds: timeSpent
        });
      }
    });
  }

  async trackEvent(eventType, eventData) {
    const token = localStorage.getItem('access_token');
    if (!token) return;

    try {
      await fetch('/api/v1/analytics/track', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          event_type: eventType,
          event_data: eventData
        })
      });
    } catch (error) {
      console.error('Failed to track event:', error);
    }
  }

  async trackBookView(bookId, bookTitle) {
    this.trackEvent('book_view', { book_id: bookId, book_title: bookTitle });
    
    // Update recently viewed
    this.userPreferences.recentlyViewed = [
      bookId,
      ...this.userPreferences.recentlyViewed.filter(id => id !== bookId)
    ].slice(0, 20);
    this.saveUserPreferences();
  }

  async trackSearch(query, resultsCount) {
    this.trackEvent('search', { query, results_count: resultsCount });
  }

  async trackPurchase(bookId, amount) {
    this.trackEvent('purchase', { book_id: bookId, amount });
    
    // Update purchased books
    if (!this.userPreferences.purchasedBooks.includes(bookId)) {
      this.userPreferences.purchasedBooks.push(bookId);
      this.saveUserPreferences();
    }
  }

  async updateSimilarityMatrix() {
    // Called periodically to update recommendation model
    try {
      await fetch('/api/v1/suggestions/update-model', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
      });
    } catch (error) {
      console.error('Failed to update similarity matrix:', error);
    }
  }

  setupEventListeners() {
    // Track book views when user navigates to book page
    if (window.location.pathname === '/book-preview.html') {
      const params = new URLSearchParams(window.location.search);
      const bookId = params.get('id');
      const bookTitle = params.get('title');
      if (bookId) {
        this.trackBookView(bookId, bookTitle);
      }
    }
  }

  escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
}

// Initialize suggestion system
window.suggestionSystem = new SuggestionSystem();

document.addEventListener('DOMContentLoaded', () => {
  window.suggestionSystem.init();
});
