// =============================================================================
// CUSTOM-BOOKING.JS - Custom Book Request Form and Management
// =============================================================================

class CustomBookingManager {
  constructor() {
    this.bookings = [];
    this.currentBooking = null;
    this.formData = {};
  }

  async init() {
    if (window.location.pathname.includes('custom-book-booking.html')) {
      this.setupBookingForm();
    } else if (window.location.pathname.includes('booking-status.html')) {
      await this.loadBookingDetails();
    } else if (window.location.pathname.includes('my-bookings.html')) {
      await this.loadUserBookings();
    }
  }

  setupBookingForm() {
    const form = document.getElementById('custom-booking-form');
    if (!form) return;
    
    // Setup file upload preview
    this.setupFileUpload();
    
    // Setup word count display
    this.setupWordCountSlider();
    
    // Setup budget range
    this.setupBudgetSlider();
    
    // Setup deadline picker
    this.setupDeadlinePicker();
    
    form.addEventListener('submit', (e) => this.submitBooking(e));
  }

  setupFileUpload() {
    const fileInput = document.getElementById('attachments');
    const previewContainer = document.getElementById('file-preview');
    
    if (!fileInput || !previewContainer) return;
    
    fileInput.addEventListener('change', (e) => {
      previewContainer.innerHTML = '';
      const files = Array.from(e.target.files);
      
      files.forEach(file => {
        if (file.size > 10 * 1024 * 1024) {
          window.showToast(`${file.name} exceeds 10MB limit`, 'error');
          return;
        }
        
        const previewItem = document.createElement('div');
        previewItem.className = 'file-preview-item';
        previewItem.innerHTML = `
          <span class="file-name">${this.escapeHtml(file.name)}</span>
          <span class="file-size">${this.formatFileSize(file.size)}</span>
          <button type="button" class="remove-file" data-filename="${file.name}">×</button>
        `;
        previewContainer.appendChild(previewItem);
      });
      
      // Attach remove handlers
      document.querySelectorAll('.remove-file').forEach(btn => {
        btn.addEventListener('click', (e) => {
          const filename = btn.dataset.filename;
          const newFiles = Array.from(fileInput.files).filter(f => f.name !== filename);
          const dataTransfer = new DataTransfer();
          newFiles.forEach(f => dataTransfer.items.add(f));
          fileInput.files = dataTransfer.files;
          btn.closest('.file-preview-item').remove();
        });
      });
    });
  }

  setupWordCountSlider() {
    const slider = document.getElementById('word-count-slider');
    const display = document.getElementById('word-count-display');
    
    if (!slider || !display) return;
    
    slider.addEventListener('input', (e) => {
      const value = parseInt(e.target.value);
      display.textContent = this.formatWordCount(value);
    });
  }

  setupBudgetSlider() {
    const slider = document.getElementById('budget-slider');
    const display = document.getElementById('budget-display');
    
    if (!slider || !display) return;
    
    slider.addEventListener('input', (e) => {
      const value = parseInt(e.target.value);
      display.textContent = `$${value.toLocaleString()}`;
    });
  }

  setupDeadlinePicker() {
    const input = document.getElementById('deadline');
    if (!input) return;
    
    // Set min date to tomorrow
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    input.min = tomorrow.toISOString().split('T')[0];
    
    // Set max date to 6 months from now
    const maxDate = new Date();
    maxDate.setMonth(maxDate.getMonth() + 6);
    input.max = maxDate.toISOString().split('T')[0];
  }

  async submitBooking(event) {
    event.preventDefault();
    
    const token = localStorage.getItem('access_token');
    if (!token) {
      sessionStorage.setItem('redirect_after_login', window.location.pathname);
      window.location.href = '/login.html';
      return;
    }
    
    const submitBtn = document.querySelector('#custom-booking-form button[type="submit"]');
    const originalText = submitBtn?.textContent;
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.textContent = 'Submitting...';
    }
    
    try {
      const formData = new FormData(event.target);
      const bookingData = {
        title: formData.get('title'),
        description: formData.get('description'),
        genre: formData.get('genre'),
        word_count: parseInt(formData.get('word_count')) || null,
        deadline: formData.get('deadline'),
        budget: parseFloat(formData.get('budget')) || null,
        requirements: formData.get('requirements'),
        attachments: [] // Files would be uploaded separately
      };
      
      const response = await fetch('/api/v1/bookings', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(bookingData)
      });
      
      const data = await response.json();
      
      if (data.success) {
        window.showToast('Booking request submitted successfully!', 'success');
        setTimeout(() => {
          window.location.href = `/booking-status.html?id=${data.data.id}`;
        }, 2000);
      } else {
        window.showToast(data.message || 'Failed to submit booking', 'error');
      }
    } catch (error) {
      console.error('Failed to submit booking:', error);
      window.showToast('Failed to submit booking. Please try again.', 'error');
    } finally {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
      }
    }
  }

  async loadBookingDetails() {
    const params = new URLSearchParams(window.location.search);
    const bookingId = params.get('id');
    
    if (!bookingId) {
      window.location.href = '/my-bookings.html';
      return;
    }
    
    const token = localStorage.getItem('access_token');
    if (!token) {
      window.location.href = '/login.html';
      return;
    }
    
    try {
      const response = await fetch(`/api/v1/bookings/${bookingId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      
      if (data.success && data.data) {
        this.currentBooking = data.data;
        this.renderBookingDetails();
      } else {
        this.showError('Booking not found');
      }
    } catch (error) {
      console.error('Failed to load booking:', error);
      this.showError('Failed to load booking details');
    }
  }

  renderBookingDetails() {
    const container = document.getElementById('booking-details-container');
    if (!container) return;
    
    const statusConfig = {
      pending: { class: 'status-pending', text: 'Pending Review', icon: '⏳' },
      accepted: { class: 'status-accepted', text: 'Accepted', icon: '✓' },
      in_progress: { class: 'status-progress', text: 'In Progress', icon: '✍️' },
      completed: { class: 'status-completed', text: 'Completed', icon: '✅' },
      delivered: { class: 'status-delivered', text: 'Delivered', icon: '📦' },
      cancelled: { class: 'status-cancelled', text: 'Cancelled', icon: '❌' }
    };
    
    const status = statusConfig[this.currentBooking.status] || statusConfig.pending;
    
    container.innerHTML = `
      <div class="booking-header">
        <h1>${this.escapeHtml(this.currentBooking.title)}</h1>
        <div class="booking-status ${status.class}">
          <span class="status-icon">${status.icon}</span>
          <span>${status.text}</span>
        </div>
      </div>
      
      <div class="booking-details-grid">
        <div class="detail-card">
          <h3>Project Details</h3>
          <div class="detail-row">
            <span class="label">Genre:</span>
            <span>${this.escapeHtml(this.currentBooking.genre || 'Not specified')}</span>
          </div>
          <div class="detail-row">
            <span class="label">Word Count:</span>
            <span>${this.currentBooking.word_count ? this.formatWordCount(this.currentBooking.word_count) : 'To be determined'}</span>
          </div>
          <div class="detail-row">
            <span class="label">Deadline:</span>
            <span>${this.currentBooking.deadline ? new Date(this.currentBooking.deadline).toLocaleDateString() : 'To be agreed'}</span>
          </div>
          <div class="detail-row">
            <span class="label">Budget:</span>
            <span>$${this.currentBooking.budget ? this.currentBooking.budget.toLocaleString() : 'To be quoted'}</span>
          </div>
        </div>
        
        <div class="detail-card">
          <h3>Project Description</h3>
          <p>${this.escapeHtml(this.currentBooking.description || 'No description provided.')}</p>
          ${this.currentBooking.requirements ? `
            <h4>Requirements</h4>
            <p>${this.escapeHtml(this.currentBooking.requirements)}</p>
          ` : ''}
        </div>
        
        ${this.currentBooking.admin_notes ? `
          <div class="detail-card admin-notes">
            <h3>Admin Notes</h3>
            <p>${this.escapeHtml(this.currentBooking.admin_notes)}</p>
          </div>
        ` : ''}
        
        ${this.currentBooking.delivery_url ? `
          <div class="detail-card delivery-section">
            <h3>Delivery</h3>
            <a href="${this.currentBooking.delivery_url}" class="btn btn-primary" target="_blank">Download Your Book</a>
          </div>
        ` : ''}
      </div>
      
      <div class="booking-timeline">
        <h3>Timeline</h3>
        <div class="timeline">
          <div class="timeline-item">
            <div class="timeline-date">${new Date(this.currentBooking.created_at).toLocaleDateString()}</div>
            <div class="timeline-content">Booking submitted</div>
          </div>
          ${this.currentBooking.accepted_at ? `
            <div class="timeline-item">
              <div class="timeline-date">${new Date(this.currentBooking.accepted_at).toLocaleDateString()}</div>
              <div class="timeline-content">Booking accepted</div>
            </div>
          ` : ''}
          ${this.currentBooking.completed_at ? `
            <div class="timeline-item">
              <div class="timeline-date">${new Date(this.currentBooking.completed_at).toLocaleDateString()}</div>
              <div class="timeline-content">Work completed</div>
            </div>
          ` : ''}
          ${this.currentBooking.delivered_at ? `
            <div class="timeline-item">
              <div class="timeline-date">${new Date(this.currentBooking.delivered_at).toLocaleDateString()}</div>
              <div class="timeline-content">Book delivered</div>
            </div>
          ` : ''}
        </div>
      </div>
    `;
  }

  async loadUserBookings() {
    const token = localStorage.getItem('access_token');
    if (!token) {
      window.location.href = '/login.html';
      return;
    }
    
    try {
      const response = await fetch('/api/v1/bookings', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      
      if (data.success && data.data?.items) {
        this.bookings = data.data.items;
        this.renderBookingList();
      }
    } catch (error) {
      console.error('Failed to load bookings:', error);
      this.showError('Failed to load your bookings');
    }
  }

  renderBookingList() {
    const container = document.getElementById('bookings-list-container');
    if (!container) return;
    
    if (!this.bookings.length) {
      container.innerHTML = `
        <div class="empty-state">
          <p>You haven't submitted any custom book requests yet.</p>
          <a href="/custom-book-booking.html" class="btn btn-primary">Request a Custom Book</a>
        </div>
      `;
      return;
    }
    
    const statusConfig = {
      pending: 'Pending',
      accepted: 'Accepted',
      in_progress: 'In Progress',
      completed: 'Completed',
      delivered: 'Delivered',
      cancelled: 'Cancelled'
    };
    
    container.innerHTML = this.bookings.map(booking => `
      <div class="booking-list-item" data-booking-id="${booking.id}">
        <div class="booking-item-header">
          <h3>${this.escapeHtml(booking.title)}</h3>
          <span class="status-badge status-${booking.status}">${statusConfig[booking.status]}</span>
        </div>
        <div class="booking-item-details">
          <span>📅 ${new Date(booking.created_at).toLocaleDateString()}</span>
          ${booking.budget ? `<span>💰 $${booking.budget.toLocaleString()}</span>` : ''}
        </div>
        <button class="btn btn-outline view-booking-btn" data-booking-id="${booking.id}">View Details</button>
      </div>
    `).join('');
    
    // Attach view handlers
    document.querySelectorAll('.view-booking-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const bookingId = btn.dataset.bookingId;
        window.location.href = `/booking-status.html?id=${bookingId}`;
      });
    });
  }

  formatWordCount(count) {
    if (count >= 1000000) return `${(count / 1000000).toFixed(1)}M words`;
    if (count >= 1000) return `${(count / 1000).toFixed(1)}K words`;
    return `${count} words`;
  }

  formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  showError(message) {
    window.showToast(message, 'error');
  }

  escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
}

// Initialize custom booking manager
window.customBookingManager = new CustomBookingManager();

document.addEventListener('DOMContentLoaded', () => {
  window.customBookingManager.init();
});
