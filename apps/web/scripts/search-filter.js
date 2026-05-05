// =============================================================================
// SEARCH-FILTER.JS - Book Search and Filtering
// =============================================================================

class SearchFilter {
  constructor() {
    this.currentFilters = {
      category: '',
      minPrice: '',
      maxPrice: '',
      sortBy: 'relevance',
      availability: 'all',
      page: 1,
      limit: 20
    };
    this.searchTimeout = null;
  }
  
  init() {
    this.loadFiltersFromURL();
    this.setupEventListeners();
    this.setupInfiniteScroll();
    this.loadCategories();
  }
  
  loadFiltersFromURL() {
    const params = new URLSearchParams(window.location.search);
    
    this.currentFilters.category = params.get('category') || '';
    this.currentFilters.search = params.get('search') || '';
    this.currentFilters.minPrice = params.get('min_price') || '';
    this.currentFilters.maxPrice = params.get('max_price') || '';
    this.currentFilters.sortBy = params.get('sort') || 'relevance';
    this.currentFilters.page = parseInt(params.get('page')) || 1;
    
    // Update UI with current filters
    this.updateFilterUI();
  }
  
  setupEventListeners() {
    // Category filter
    const categorySelect = document.getElementById('search-category');
    if (categorySelect) {
      categorySelect.addEventListener('change', (e) => {
        this.currentFilters.category = e.target.value;
        this.applyFilters();
      });
    }
    
    // Price range
    const minPrice = document.getElementById('min-price');
    const maxPrice = document.getElementById('max-price');
    if (minPrice) {
      minPrice.addEventListener('change', (e) => {
        this.currentFilters.minPrice = e.target.value;
        this.applyFilters();
      });
    }
    if (maxPrice) {
      maxPrice.addEventListener('change', (e) => {
        this.currentFilters.maxPrice = e.target.value;
        this.applyFilters();
      });
    }
    
    // Sort by
    const sortSelect = document.getElementById('search-sort');
    if (sortSelect) {
      sortSelect.addEventListener('change', (e) => {
        this.currentFilters.sortBy = e.target.value;
        this.applyFilters();
      });
    }
    
    // Availability
    const availabilitySelect = document.getElementById('search-availability');
    if (availabilitySelect) {
      availabilitySelect.addEventListener('change', (e) => {
        this.currentFilters.availability = e.target.value;
        this.applyFilters();
      });
    }
    
    // Search input with debounce
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        clearTimeout(this.searchTimeout);
        this.searchTimeout = setTimeout(() => {
          this.currentFilters.search = e.target.value;
          this.currentFilters.page = 1;
          this.applyFilters();
        }, 500);
      });
    }
    
    // Search button
    const searchBtn = document.getElementById('search-submit');
    if (searchBtn) {
      searchBtn.addEventListener('click', () => {
        const searchInput = document.getElementById('search-input');
        if (searchInput) {
          this.currentFilters.search = searchInput.value;
          this.currentFilters.page = 1;
          this.applyFilters();
        }
      });
    }
    
    // Clear filters
    const clearBtn = document.getElementById('clear-filters');
    if (clearBtn) {
      clearBtn.addEventListener('click', () => {
        this.resetFilters();
      });
    }
  }
  
  updateFilterUI() {
    // Update select elements
    const categorySelect = document.getElementById('search-category');
    if (categorySelect) categorySelect.value = this.currentFilters.category;
    
    const sortSelect = document.getElementById('search-sort');
    if (sortSelect) sortSelect.value = this.currentFilters.sortBy;
    
    const availabilitySelect = document.getElementById('search-availability');
    if (availabilitySelect) availabilitySelect.value = this.currentFilters.availability;
    
    // Update price inputs
    const minPrice = document.getElementById('min-price');
    const maxPrice = document.getElementById('max-price');
    if (minPrice) minPrice.value = this.currentFilters.minPrice;
    if (maxPrice) maxPrice.value = this.currentFilters.maxPrice;
    
    // Update search input
    const searchInput = document.getElementById('search-input');
    if (searchInput) searchInput.value = this.currentFilters.search || '';
  }
  
  applyFilters() {
    // Build URL with filters
    const params = new URLSearchParams();
    
    if (this.currentFilters.search) params.set('search', this.currentFilters.search);
    if (this.currentFilters.category) params.set('category', this.currentFilters.category);
    if (this.currentFilters.minPrice) params.set('min_price', this.currentFilters.minPrice);
    if (this.currentFilters.maxPrice) params.set('max_price', this.currentFilters.maxPrice);
    if (this.currentFilters.sortBy) params.set('sort', this.currentFilters.sortBy);
    if (this.currentFilters.availability !== 'all') params.set('availability', this.currentFilters.availability);
    if (this.currentFilters.page > 1) params.set('page', this.currentFilters.page);
    
    const newUrl = `${window.location.pathname}?${params.toString()}`;
    window.history.pushState({}, '', newUrl);
    
    // Reload books
    this.loadBooks();
  }
  
  resetFilters() {
    this.currentFilters = {
      category: '',
      search: '',
      minPrice: '',
      maxPrice: '',
      sortBy: 'relevance',
      availability: 'all',
      page: 1,
      limit: 20
    };
    
    this.updateFilterUI();
    this.applyFilters();
  }
  
  async loadBooks() {
    const container = document.getElementById('books-list-container');
    if (!container) return;
    
    // Show loading skeleton
    this.showLoadingSkeleton(container);
    
    try {
      const params = new URLSearchParams();
      params.set('page', this.currentFilters.page);
      params.set('limit', this.currentFilters.limit);
      if (this.currentFilters.search) params.set('q', this.currentFilters.search);
      if (this.currentFilters.category) params.set('category', this.currentFilters.category);
      if (this.currentFilters.minPrice) params.set('min_price', this.currentFilters.minPrice);
      if (this.currentFilters.maxPrice) params.set('max_price', this.currentFilters.maxPrice);
      if (this.currentFilters.sortBy) params.set('sort', this.currentFilters.sortBy);
      if (this.currentFilters.availability === 'free') params.set('is_free', 'true');
      if (this.currentFilters.availability === 'paid') params.set('is_free', 'false');
      
      const response = await fetch(`/api/v1/books/search?${params.toString()}`);
      const data = await response.json();
      
      if (data.success) {
        this.renderBooks(data.data.items);
        this.renderPagination(data.data);
      } else {
        container.innerHTML = '<p class="no-results">No books found. Try different filters.</p>';
      }
    } catch (error) {
      console.error('Failed to load books:', error);
      container.innerHTML = '<p class="error">Failed to load books. Please try again.</p>';
    }
  }
  
  renderBooks(books) {
    const container = document.getElementById('books-list-container');
    if (!container) return;
    
    if (!books || books.length === 0) {
      container.innerHTML = '<p class="no-results">No books found. Try different filters.</p>';
      return;
    }
    
    container.innerHTML = books.map(book => `
      <div class="book-card">
        <div class="book-card-inner">
          <div class="book-cover">
            <img src="${book.cover_image_url || '/images/default-book-cover.jpg'}" alt="${this.escapeHtml(book.title)}" loading="lazy">
            ${book.is_free ? '<span class="free-badge">FREE</span>' : ''}
          </div>
          <div class="book-info">
            <h3 class="book-title">${this.escapeHtml(book.title)}</h3>
            <p class="book-author">by ${this.escapeHtml(book.author_name)}</p>
            <div class="book-rating">
              <div class="stars">${this.renderStars(book.average_rating)}</div>
              <span class="review-count">(${book.review_count || 0})</span>
            </div>
            <div class="book-price">${book.is_free ? 'FREE' : `$${book.price.toFixed(2)}`}</div>
            <div class="book-actions">
              <a href="/book-preview.html?id=${book.id}" class="btn btn-outline btn-sm">Preview</a>
              <button class="btn btn-primary btn-sm buy-btn" data-book-id="${book.id}">Buy</button>
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
  }
  
  renderPagination(data) {
    const container = document.getElementById('pagination-container');
    if (!container || data.total_pages <= 1) {
      if (container) container.innerHTML = '';
      return;
    }
    
    let html = '<div class="pagination">';
    
    // Previous button
    if (data.page > 1) {
      html += `<button class="pagination-prev" data-page="${data.page - 1}">« Prev</button>`;
    }
    
    // Page numbers
    const startPage = Math.max(1, data.page - 2);
    const endPage = Math.min(data.total_pages, data.page + 2);
    
    if (startPage > 1) {
      html += `<button class="pagination-btn" data-page="1">1</button>`;
      if (startPage > 2) html += '<span>...</span>';
    }
    
    for (let i = startPage; i <= endPage; i++) {
      html += `<button class="pagination-btn ${i === data.page ? 'active' : ''}" data-page="${i}">${i}</button>`;
    }
    
    if (endPage < data.total_pages) {
      if (endPage < data.total_pages - 1) html += '<span>...</span>';
      html += `<button class="pagination-btn" data-page="${data.total_pages}">${data.total_pages}</button>`;
    }
    
    // Next button
    if (data.page < data.total_pages) {
      html += `<button class="pagination-next" data-page="${data.page + 1}">Next »</button>`;
    }
    
    html += '</div>';
    
    container.innerHTML = html;
    
    // Attach pagination handlers
    document.querySelectorAll('.pagination-btn, .pagination-prev, .pagination-next').forEach(btn => {
      btn.addEventListener('click', () => {
        const page = parseInt(btn.dataset.page);
        if (!isNaN(page)) {
          this.currentFilters.page = page;
          this.applyFilters();
          window.scrollTo({ top: 0, behavior: 'smooth' });
        }
      });
    });
  }
  
  async loadCategories() {
    try {
      const response = await fetch('/api/v1/books/categories');
      const data = await response.json();
      
      if (data.success && data.data) {
        const categorySelect = document.getElementById('search-category');
        if (categorySelect) {
          const categoriesHtml = data.data.map(cat => 
            `<option value="${cat.slug}">${cat.name}</option>`
          ).join('');
          categorySelect.innerHTML = '<option value="">All Categories</option>' + categoriesHtml;
        }
      }
    } catch (error) {
      console.error('Failed to load categories:', error);
    }
  }
  
  setupInfiniteScroll() {
    let loading = false;
    
    window.addEventListener('scroll', () => {
      if (loading) return;
      
      const scrollPosition = window.innerHeight + window.scrollY;
      const bottom = document.documentElement.scrollHeight - 200;
      
      if (scrollPosition >= bottom) {
        loading = true;
        this.currentFilters.page++;
        this.loadMoreBooks().finally(() => {
          loading = false;
        });
      }
    });
  }
  
  async loadMoreBooks() {
    // Implementation for infinite scroll
    const container = document.getElementById('books-list-container');
    if (!container) return;
    
    try {
      const params = new URLSearchParams();
      params.set('page', this.currentFilters.page);
      params.set('limit', this.currentFilters.limit);
      if (this.currentFilters.search) params.set('q', this.currentFilters.search);
      if (this.currentFilters.category) params.set('category', this.currentFilters.category);
      
      const response = await fetch(`/api/v1/books/search?${params.toString()}`);
      const data = await response.json();
      
      if (data.success && data.data.items) {
        const newBooksHtml = data.data.items.map(book => this.renderBookCardHtml(book)).join('');
        container.insertAdjacentHTML('beforeend', newBooksHtml);
      }
    } catch (error) {
      console.error('Failed to load more books:', error);
    }
  }
  
  showLoadingSkeleton(container) {
    const skeletonHtml = Array(6).fill(`
      <div class="book-card skeleton">
        <div class="book-card-inner">
          <div class="book-cover skeleton-box" style="height: 250px;"></div>
          <div class="book-info">
            <div class="skeleton-text" style="width: 80%; height: 20px;"></div>
            <div class="skeleton-text" style="width: 60%; height: 15px; margin-top: 8px;"></div>
            <div class="skeleton-text" style="width: 40%; height: 20px; margin-top: 12px;"></div>
          </div>
        </div>
      </div>
    `).join('');
    
    container.innerHTML = skeletonHtml;
  }
  
  renderStars(rating) {
    if (!rating) return '☆☆☆☆☆';
    const fullStars = Math.floor(rating);
    const hasHalf = rating % 1 >= 0.5;
    let stars = '';
    for (let i = 0; i < fullStars; i++) stars += '★';
    if (hasHalf) stars += '½';
    for (let i = stars.length; i < 5; i++) stars += '☆';
    return stars;
  }
  
  escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
}

// Initialize search filter
window.searchFilter = new SearchFilter();

document.addEventListener('DOMContentLoaded', () => {
  window.searchFilter.init();
});
