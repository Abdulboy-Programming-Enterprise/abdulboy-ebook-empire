// =============================================================================
// BOOK-READER.JS - PDF/EPUB Reader with Progress Tracking
// =============================================================================

class BookReader {
  constructor() {
    this.bookId = null;
    this.bookData = null;
    this.currentPage = 1;
    this.totalPages = 0;
    this.pdfDoc = null;
    this.scale = 1.5;
    this.renderer = null;
    this.preferences = this.loadPreferences();
  }

  async init() {
    const params = new URLSearchParams(window.location.search);
    this.bookId = params.get('id');
    
    if (!this.bookId) {
      window.location.href = '/ebook-site.html';
      return;
    }
    
    await this.loadBook();
    this.setupEventListeners();
    this.setupKeyboardNavigation();
    this.loadReadingProgress();
  }

  async loadBook() {
    const token = localStorage.getItem('access_token');
    
    try {
      const response = await fetch(`/api/v1/books/${this.bookId}`, {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      });
      const data = await response.json();
      
      if (data.success && data.data) {
        this.bookData = data.data;
        this.totalPages = this.bookData.total_pages;
        this.updateUI();
        
        if (this.bookData.pdf_url) {
          await this.loadPDF(this.bookData.pdf_url);
        } else {
          this.showErrorMessage('Book content not available');
        }
      } else {
        this.showErrorMessage('Book not found');
      }
    } catch (error) {
      console.error('Failed to load book:', error);
      this.showErrorMessage('Failed to load book');
    }
  }

  async loadPDF(url) {
    const loadingIndicator = document.getElementById('reader-loading');
    const container = document.getElementById('pdf-viewer');
    
    if (loadingIndicator) loadingIndicator.style.display = 'flex';
    
    try {
      const pdfjsLib = window.pdfjsLib;
      pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
      
      this.pdfDoc = await pdfjsLib.getDocument(url).promise;
      this.totalPages = this.pdfDoc.numPages;
      
      this.renderer = new PDFRenderer(this.pdfDoc, container, {
        scale: this.scale,
        onPageChange: (page) => this.onPageChange(page)
      });
      
      await this.renderer.render();
      
      if (loadingIndicator) loadingIndicator.style.display = 'none';
      
      this.updatePageInfo();
    } catch (error) {
      console.error('Failed to load PDF:', error);
      if (loadingIndicator) loadingIndicator.style.display = 'none';
      this.showErrorMessage('Failed to load book content');
    }
  }

  updateUI() {
    document.getElementById('book-title').textContent = this.bookData.title;
    document.getElementById('book-author').textContent = `by ${this.bookData.author_name}`;
    document.getElementById('total-pages').textContent = this.totalPages;
  }

  updatePageInfo() {
    document.getElementById('current-page').textContent = this.currentPage;
    document.getElementById('total-pages').textContent = this.totalPages;
    
    const progress = (this.currentPage / this.totalPages) * 100;
    const progressBar = document.getElementById('reading-progress-bar');
    if (progressBar) {
      progressBar.style.width = `${progress}%`;
    }
  }

  async goToPage(page) {
    if (page < 1) page = 1;
    if (page > this.totalPages) page = this.totalPages;
    
    this.currentPage = page;
    
    if (this.renderer) {
      await this.renderer.goToPage(page);
    }
    
    this.updatePageInfo();
    this.saveReadingProgress();
  }

  nextPage() {
    this.goToPage(this.currentPage + 1);
  }

  prevPage() {
    this.goToPage(this.currentPage - 1);
  }

  zoomIn() {
    this.scale = Math.min(this.scale + 0.25, 3);
    if (this.renderer) {
      this.renderer.setScale(this.scale);
    }
  }

  zoomOut() {
    this.scale = Math.max(this.scale - 0.25, 0.75);
    if (this.renderer) {
      this.renderer.setScale(this.scale);
    }
  }

  async saveReadingProgress() {
    const token = localStorage.getItem('access_token');
    if (!token) return;
    
    try {
      await fetch('/api/v1/users/reading-progress', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          book_id: this.bookId,
          position: this.currentPage
        })
      });
    } catch (error) {
      console.error('Failed to save reading progress:', error);
    }
  }

  async loadReadingProgress() {
    const token = localStorage.getItem('access_token');
    if (!token) return;
    
    try {
      const response = await fetch(`/api/v1/users/reading-progress/${this.bookId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      
      if (data.success && data.data?.position) {
        this.currentPage = data.data.position;
        if (this.renderer) {
          await this.renderer.goToPage(this.currentPage);
        }
        this.updatePageInfo();
      }
    } catch (error) {
      console.error('Failed to load reading progress:', error);
    }
  }

  onPageChange(page) {
    this.currentPage = page;
    this.updatePageInfo();
    this.saveReadingProgress();
  }

  setupEventListeners() {
    // Navigation buttons
    const prevBtn = document.getElementById('prev-page');
    const nextBtn = document.getElementById('next-page');
    const zoomInBtn = document.getElementById('zoom-in');
    const zoomOutBtn = document.getElementById('zoom-out');
    const fullscreenBtn = document.getElementById('fullscreen-mode');
    const themeToggle = document.getElementById('reader-theme-toggle');
    
    if (prevBtn) prevBtn.addEventListener('click', () => this.prevPage());
    if (nextBtn) nextBtn.addEventListener('click', () => this.nextPage());
    if (zoomInBtn) zoomInBtn.addEventListener('click', () => this.zoomIn());
    if (zoomOutBtn) zoomOutBtn.addEventListener('click', () => this.zoomOut());
    
    if (fullscreenBtn) {
      fullscreenBtn.addEventListener('click', () => this.toggleFullscreen());
    }
    
    if (themeToggle) {
      themeToggle.addEventListener('click', () => this.toggleTheme());
    }
    
    // Page jump
    const pageInput = document.getElementById('page-jump');
    if (pageInput) {
      pageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
          const page = parseInt(pageInput.value);
          if (!isNaN(page)) {
            this.goToPage(page);
            pageInput.value = '';
          }
        }
      });
    }
  }

  setupKeyboardNavigation() {
    document.addEventListener('keydown', (e) => {
      switch(e.key) {
        case 'ArrowLeft':
          this.prevPage();
          break;
        case 'ArrowRight':
          this.nextPage();
          break;
        case '+':
        case '=':
          this.zoomIn();
          break;
        case '-':
          this.zoomOut();
          break;
        case 'f':
        case 'F':
          this.toggleFullscreen();
          break;
        case 'Escape':
          this.exitFullscreen();
          break;
      }
    });
  }

  toggleFullscreen() {
    const container = document.getElementById('reader-container');
    if (!document.fullscreenElement) {
      container.requestFullscreen();
    } else {
      document.exitFullscreen();
    }
  }

  exitFullscreen() {
    if (document.fullscreenElement) {
      document.exitFullscreen();
    }
  }

  toggleTheme() {
    const body = document.body;
    const themes = ['reader-light', 'reader-dark', 'reader-sepia', 'reader-night'];
    const currentTheme = Array.from(body.classList).find(c => themes.includes(c)) || 'reader-light';
    const currentIndex = themes.indexOf(currentTheme);
    const nextIndex = (currentIndex + 1) % themes.length;
    
    themes.forEach(theme => body.classList.remove(theme));
    body.classList.add(themes[nextIndex]);
    
    localStorage.setItem('reader_theme', themes[nextIndex]);
  }

  loadPreferences() {
    const savedTheme = localStorage.getItem('reader_theme');
    if (savedTheme) {
      document.body.classList.add(savedTheme);
    }
    return {
      theme: savedTheme || 'reader-light'
    };
  }

  showErrorMessage(message) {
    const container = document.getElementById('reader-container');
    if (container) {
      container.innerHTML = `
        <div class="reader-error">
          <h2>Unable to Load Book</h2>
          <p>${message}</p>
          <a href="/ebook-site.html" class="btn btn-primary">Browse Books</a>
        </div>
      `;
    }
  }
}

// PDF Renderer Class
class PDFRenderer {
  constructor(pdfDoc, container, options) {
    this.pdfDoc = pdfDoc;
    this.container = container;
    this.scale = options.scale || 1.5;
    this.onPageChange = options.onPageChange;
    this.currentPageNum = 1;
    this.pagesRendered = new Map();
    this.canvasCache = new Map();
  }

  async render() {
    this.container.innerHTML = '';
    
    for (let i = 1; i <= this.pdfDoc.numPages; i++) {
      const pageContainer = document.createElement('div');
      pageContainer.className = 'pdf-page-container';
      pageContainer.dataset.pageNum = i;
      
      const canvas = document.createElement('canvas');
      pageContainer.appendChild(canvas);
      this.container.appendChild(pageContainer);
      
      await this.renderPage(i, canvas);
    }
    
    // Scroll to current page
    const currentPageEl = document.querySelector(`.pdf-page-container[data-page-num="${this.currentPageNum}"]`);
    if (currentPageEl) {
      currentPageEl.scrollIntoView({ behavior: 'smooth' });
    }
  }

  async renderPage(pageNum, canvas) {
    const page = await this.pdfDoc.getPage(pageNum);
    const viewport = page.getViewport({ scale: this.scale });
    
    canvas.width = viewport.width;
    canvas.height = viewport.height;
    
    const context = canvas.getContext('2d');
    const renderContext = {
      canvasContext: context,
      viewport: viewport
    };
    
    await page.render(renderContext).promise;
    
    this.canvasCache.set(pageNum, canvas);
  }

  async goToPage(pageNum) {
    this.currentPageNum = pageNum;
    const targetElement = document.querySelector(`.pdf-page-container[data-page-num="${pageNum}"]`);
    if (targetElement) {
      targetElement.scrollIntoView({ behavior: 'smooth' });
    }
    if (this.onPageChange) {
      this.onPageChange(pageNum);
    }
  }

  async setScale(newScale) {
    this.scale = newScale;
    this.canvasCache.clear();
    this.container.innerHTML = '';
    await this.render();
    await this.goToPage(this.currentPageNum);
  }
}

// Initialize book reader
window.bookReader = new BookReader();

document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('reader-container')) {
    window.bookReader.init();
  }
});
