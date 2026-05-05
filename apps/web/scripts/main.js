// =============================================================================
// MAIN.JS - Core Application Entry Point
// =============================================================================

import '../styles/main.css';
import '../styles/dark-mode.css';
import '../styles/responsive.css';
import '../styles/animations.css';
import './utils.js';
import './auth.js';
import './payment.js';
import './chatbot.js';
import './search-filter.js';
import './suggestion-system.js';
import './analytics.js';

// Global app state
window.App = {
  initialized: false,
  user: null,
  config: window.siteConfig || {},
  components: {},
  
  async init() {
    if (this.initialized) return;
    
    console.log('Initializing Abdulboy Ebook Empire...');
    
    // Load user session
    await this.loadUserSession();
    
    // Initialize components
    this.initComponents();
    
    // Setup event listeners
    this.setupEventListeners();
    
    // Load page-specific data
    await this.loadPageData();
    
    this.initialized = true;
    console.log('Application initialized');
  },
  
  async loadUserSession() {
    const token = localStorage.getItem('access_token');
    if (!token) return;
    
    try {
      const response = await fetch('/api/v1/users/me', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        this.user = await response.json();
        this.updateUIForLoggedInUser();
      } else {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
      }
    } catch (error) {
      console.error('Failed to load user session:', error);
    }
  },
  
  updateUIForLoggedInUser() {
    // Update navigation to show user menu
    const authButtons = document.getElementById('auth-buttons');
    const userMenu = document.getElementById('user-menu');
    const userNameSpan = document.getElementById('user-name');
    
    if (authButtons && userMenu) {
      authButtons.style.display = 'none';
      userMenu.style.display = 'block';
    }
    
    if (userNameSpan && this.user) {
      userNameSpan.textContent = this.user.full_name || this.user.email.split('@')[0];
    }
    
    // Dispatch event for other components
    document.dispatchEvent(new CustomEvent('user-logged-in', { detail: this.user }));
  },
  
  initComponents() {
    // Initialize header scroll effect
    this.initHeaderScroll();
    
    // Initialize mobile menu
    this.initMobileMenu();
    
    // Initialize lazy loading
    this.initLazyLoading();
    
    // Initialize form validation
    this.initFormValidation();
  },
  
  initHeaderScroll() {
    const header = document.querySelector('.site-header');
    if (!header) return;
    
    let lastScroll = 0;
    window.addEventListener('scroll', () => {
      const currentScroll = window.pageYOffset;
      
      if (currentScroll > 100) {
        header.classList.add('scrolled');
        if (currentScroll > lastScroll && currentScroll > 300) {
          header.style.transform = 'translateY(-100%)';
        } else {
          header.style.transform = 'translateY(0)';
        }
      } else {
        header.classList.remove('scrolled');
        header.style.transform = 'translateY(0)';
      }
      
      lastScroll = currentScroll;
    });
  },
  
  initMobileMenu() {
    const toggle = document.getElementById('mobile-menu-toggle');
    const mobileNav = document.getElementById('mobile-nav');
    
    if (toggle && mobileNav) {
      toggle.addEventListener('click', () => {
        const isOpen = mobileNav.classList.contains('open');
        mobileNav.classList.toggle('open');
        document.body.style.overflow = isOpen ? 'auto' : 'hidden';
      });
    }
  },
  
  initLazyLoading() {
    if ('IntersectionObserver' in window) {
      const lazyImages = document.querySelectorAll('img[data-src]');
      
      const imageObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            const img = entry.target;
            img.src = img.dataset.src;
            img.removeAttribute('data-src');
            imageObserver.unobserve(img);
          }
        });
      });
      
      lazyImages.forEach(img => imageObserver.observe(img));
    }
  },
  
  initFormValidation() {
    const forms = document.querySelectorAll('form[data-validate]');
    forms.forEach(form => {
      form.addEventListener('submit', (e) => {
        if (!this.validateForm(form)) {
          e.preventDefault();
        }
      });
    });
  },
  
  validateForm(form) {
    let isValid = true;
    const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
    
    inputs.forEach(input => {
      if (!input.value.trim()) {
        this.showFieldError(input, 'This field is required');
        isValid = false;
      } else {
        this.clearFieldError(input);
      }
      
      // Email validation
      if (input.type === 'email' && input.value) {
        const emailRegex = /^[^\s@]+@([^\s@.,]+\.)+[^\s@.,]{2,}$/;
        if (!emailRegex.test(input.value)) {
          this.showFieldError(input, 'Please enter a valid email address');
          isValid = false;
        }
      }
      
      // Password confirmation
      if (input.name === 'confirm_password') {
        const password = form.querySelector('input[name="password"]');
        if (password && input.value !== password.value) {
          this.showFieldError(input, 'Passwords do not match');
          isValid = false;
        }
      }
    });
    
    return isValid;
  },
  
  showFieldError(input, message) {
    const formGroup = input.closest('.form-group');
    if (!formGroup) return;
    
    let errorSpan = formGroup.querySelector('.form-error');
    if (!errorSpan) {
      errorSpan = document.createElement('span');
      errorSpan.className = 'form-error';
      formGroup.appendChild(errorSpan);
    }
    
    errorSpan.textContent = message;
    input.classList.add('error');
  },
  
  clearFieldError(input) {
    const formGroup = input.closest('.form-group');
    if (!formGroup) return;
    
    const errorSpan = formGroup.querySelector('.form-error');
    if (errorSpan) errorSpan.remove();
    input.classList.remove('error');
  },
  
  async loadPageData() {
    const path = window.location.pathname;
    
    if (path === '/' || path === '/index.html') {
      await this.loadHomePageData();
    } else if (path === '/ebook-site.html') {
      await this.loadBooksPageData();
    } else if (path === '/book-preview.html') {
      await this.loadBookPreviewData();
    }
  },
  
  async loadHomePageData() {
    // Load featured books
    try {
      const response = await fetch('/api/v1/books?limit=6&sort=popular');
      const data = await response.json();
      
      if (data.success && data.data.items) {
        this.renderFeaturedBooks(data.data.items);
      }
    } catch (error) {
      console.error('Failed to load featured books:', error);
    }
  },
  
  async loadBooksPageData() {
    // Load books with filters
    const params = new URLSearchParams(window.location.search);
    const category = params.get('category') || '';
    const search = params.get('search') || '';
    
    try {
      let url = '/api/v1/books?limit=20';
      if (category) url += `&category=${category}`;
      if (search) url += `&search=${search}`;
      
      const response = await fetch(url);
      const data = await response.json();
      
      if (data.success && data.data.items) {
        this.renderBooksList(data.data.items);
        this.renderPagination(data.data);
      }
    } catch (error) {
      console.error('Failed to load books:', error);
    }
  },
  
  async loadBookPreviewData() {
    const params = new URLSearchParams(window.location.search);
    const bookId = params.get('id');
    
    if (bookId) {
      try {
        const response = await fetch(`/api/v1/books/${bookId}`);
        const data = await response.json();
        
        if (data.success && data.data) {
          this.renderBookDetail(data.data);
        }
      } catch (error) {
        console.error('Failed to load book details:', error);
      }
    }
  },
  
  renderFeaturedBooks(books) {
    const container = document.getElementById('featured-books-container');
    if (!container) return;
    
    container.innerHTML = books.map(book => `
      <div class="book-card">
        <div class="book-card-inner">
          <div class="book-cover">
            <img src="${book.cover_image_url || '/images/default-book-cover.jpg'}" alt="${this.escapeHtml(book.title)}">
          </div>
          <div class="book-info">
            <h3 class="book-title">${this.escapeHtml(book.title)}</h3>
            <p class="book-author">by ${this.escapeHtml(book.author_name)}</p>
            <div class="book-price">${book.is_free ? 'FREE' : `$${book.price.toFixed(2)}`}</div>
            <a href="/book-preview.html?id=${book.id}" class="btn btn-outline btn-sm">Preview</a>
          </div>
        </div>
      </div>
    `).join('');
  },
  
  renderBooksList(books) {
    const container = document.getElementById('books-list-container');
    if (!container) return;
    
    container.innerHTML = books.map(book => `
      <div class="book-card">
        <div class="book-card-inner">
          <div class="book-cover">
            <img src="${book.cover_image_url || '/images/default-book-cover.jpg'}" alt="${this.escapeHtml(book.title)}">
          </div>
          <div class="book-info">
            <h3 class="book-title">${this.escapeHtml(book.title)}</h3>
            <p class="book-author">by ${this.escapeHtml(book.author_name)}</p>
            <div class="book-price">${book.is_free ? 'FREE' : `$${book.price.toFixed(2)}`}</div>
            <div class="book-actions">
              <a href="/book-preview.html?id=${book.id}" class="btn btn-outline btn-sm">Preview</a>
              <button class="btn btn-primary btn-sm buy-btn" data-book-id="${book.id}">Buy Now</button>
            </div>
          </div>
        </div>
      </div>
    `).join('');
    
    // Attach buy button handlers
    document.querySelectorAll('.buy-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const bookId = btn.dataset.bookId;
        window.location.href = `/checkout.html?book_id=${bookId}`;
      });
    });
  },
  
  renderBookDetail(book) {
    const container = document.getElementById('book-detail-container');
    if (!container) return;
    
    container.innerHTML = `
      <div class="book-detail-grid">
        <div class="book-cover-large">
          <img src="${book.cover_image_url || '/images/default-book-cover.jpg'}" alt="${this.escapeHtml(book.title)}">
        </div>
        <div class="book-info">
          <h1>${this.escapeHtml(book.title)}</h1>
          <p class="book-author">by ${this.escapeHtml(book.author_name)}</p>
          <div class="book-rating">
            <div class="stars">${this.renderStars(book.average_rating || 0)}</div>
            <span>${book.review_count || 0} reviews</span>
          </div>
          <p class="book-description">${this.escapeHtml(book.description || 'No description available.')}</p>
          <div class="book-meta">
            <div><strong>Pages:</strong> ${book.total_pages}</div>
            <div><strong>Language:</strong> ${book.language.toUpperCase()}</div>
            <div><strong>Published:</strong> ${new Date(book.published_at).toLocaleDateString()}</div>
          </div>
          <div class="book-price">${book.is_free ? 'FREE' : `$${book.price.toFixed(2)}`}</div>
          <div class="book-actions">
            <button class="btn btn-primary buy-now-btn" data-book-id="${book.id}">${book.is_free ? 'Read Now' : 'Buy Now'}</button>
            <button class="btn btn-outline preview-btn" data-book-id="${book.id}">Preview Sample</button>
          </div>
        </div>
      </div>
    `;
    
    // Attach handlers
    document.querySelector('.buy-now-btn')?.addEventListener('click', () => {
      if (book.is_free) {
        window.location.href = `/reader.html?book_id=${book.id}`;
      } else {
        window.location.href = `/checkout.html?book_id=${book.id}`;
      }
    });
  },
  
  renderStars(rating) {
    const fullStars = Math.floor(rating);
    const hasHalf = rating % 1 >= 0.5;
    let stars = '';
    
    for (let i = 0; i < fullStars; i++) stars += '★';
    if (hasHalf) stars += '½';
    for (let i = stars.length; i < 5; i++) stars += '☆';
    
    return stars;
  },
  
  renderPagination(data) {
    const container = document.getElementById('pagination-container');
    if (!container || data.total_pages <= 1) return;
    
    let html = '<div class="pagination">';
    for (let i = 1; i <= data.total_pages; i++) {
      html += `<button class="pagination-btn ${i === data.page ? 'active' : ''}" data-page="${i}">${i}</button>`;
    }
    html += '</div>';
    
    container.innerHTML = html;
    
    document.querySelectorAll('.pagination-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const page = btn.dataset.page;
        const url = new URL(window.location.href);
        url.searchParams.set('page', page);
        window.location.href = url.toString();
      });
    });
  },
  
  setupEventListeners() {
    // Cart button
    const cartBtn = document.getElementById('cart-btn');
    if (cartBtn) {
      cartBtn.addEventListener('click', () => {
        window.location.href = '/cart.html';
      });
    }
    
    // Search form
    const searchForm = document.querySelector('.search-form');
    if (searchForm) {
      searchForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const input = searchForm.querySelector('input[name="q"]');
        if (input && input.value.trim()) {
          window.location.href = `/ebook-site.html?search=${encodeURIComponent(input.value.trim())}`;
        }
      });
    }
    
    // Currency selector
    const currencySelect = document.getElementById('currency-select');
    if (currencySelect) {
      currencySelect.addEventListener('change', (e) => {
        localStorage.setItem('preferred_currency', e.target.value);
        window.location.reload();
      });
    }
  },
  
  escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
};

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  window.App.init();
});

// Service Worker registration
if ('serviceWorker' in navigator && window.location.hostname !== 'localhost') {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js')
      .then(registration => {
        console.log('ServiceWorker registered:', registration.scope);
      })
      .catch(error => {
        console.error('ServiceWorker registration failed:', error);
      });
  });
}
