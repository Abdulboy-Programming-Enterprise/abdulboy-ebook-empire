// =============================================================================
// ADMIN.JS - Admin Panel Functionality
// =============================================================================

class AdminPanel {
  constructor() {
    this.isAdmin = false;
    this.currentUser = null;
    this.charts = {};
  }

  async init() {
    await this.checkAdminAccess();
    if (!this.isAdmin) return;
    
    this.setupEventListeners();
    await this.loadDashboardStats();
    this.loadCharts();
    this.setupDataTables();
  }

  async checkAdminAccess() {
    const token = localStorage.getItem('access_token');
    if (!token) {
      window.location.href = '/login.html?redirect=/admin/dashboard.html';
      return;
    }

    try {
      const response = await fetch('/api/v1/users/me', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      
      if (data.success && data.data.account_type === 'admin') {
        this.isAdmin = true;
        this.currentUser = data.data;
      } else {
        window.location.href = '/';
      }
    } catch (error) {
      console.error('Failed to verify admin access:', error);
      window.location.href = '/';
    }
  }

  async loadDashboardStats() {
    try {
      const response = await fetch('/api/v1/admin/dashboard/stats', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
      });
      const data = await response.json();
      
      if (data.success && data.data) {
        this.updateStatsUI(data.data);
      }
    } catch (error) {
      console.error('Failed to load dashboard stats:', error);
    }
  }

  updateStatsUI(stats) {
    // Update user stats
    const totalUsersEl = document.getElementById('stat-total-users');
    const newUsersEl = document.getElementById('stat-new-users');
    const activeSubscriptionsEl = document.getElementById('stat-active-subscriptions');
    
    if (totalUsersEl) totalUsersEl.textContent = stats.users?.total || 0;
    if (newUsersEl) newUsersEl.textContent = stats.users?.new_today || 0;
    if (activeSubscriptionsEl) activeSubscriptionsEl.textContent = stats.users?.active_subscriptions || 0;
    
    // Update book stats
    const totalBooksEl = document.getElementById('stat-total-books');
    const newBooksEl = document.getElementById('stat-new-books');
    
    if (totalBooksEl) totalBooksEl.textContent = stats.books?.total || 0;
    if (newBooksEl) newBooksEl.textContent = stats.books?.new_this_month || 0;
    
    // Update revenue stats
    const totalRevenueEl = document.getElementById('stat-total-revenue');
    const monthlyRevenueEl = document.getElementById('stat-monthly-revenue');
    
    if (totalRevenueEl) totalRevenueEl.textContent = `$${(stats.revenue?.total || 0).toFixed(2)}`;
    if (monthlyRevenueEl) monthlyRevenueEl.textContent = `$${(stats.revenue?.this_month || 0).toFixed(2)}`;
    
    // Update payment stats
    const pendingPaymentsEl = document.getElementById('stat-pending-payments');
    if (pendingPaymentsEl) pendingPaymentsEl.textContent = stats.payments?.pending || 0;
    
    // Update booking stats
    const pendingBookingsEl = document.getElementById('stat-pending-bookings');
    if (pendingBookingsEl) pendingBookingsEl.textContent = stats.bookings?.pending || 0;
  }

  loadCharts() {
    this.loadRevenueChart();
    this.loadUserGrowthChart();
    this.loadBookStatsChart();
  }

  async loadRevenueChart() {
    const canvas = document.getElementById('revenue-chart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    try {
      const response = await fetch('/api/v1/admin/charts/revenue', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
      });
      const data = await response.json();
      
      if (data.success && data.data) {
        this.charts.revenue = new Chart(ctx, {
          type: 'line',
          data: {
            labels: data.data.labels,
            datasets: [{
              label: 'Revenue ($)',
              data: data.data.values,
              borderColor: '#6366f1',
              backgroundColor: 'rgba(99, 102, 241, 0.1)',
              fill: true,
              tension: 0.4
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { position: 'top' },
              tooltip: { callbacks: { label: (ctx) => `$${ctx.raw.toFixed(2)}` } }
            }
          }
        });
      }
    } catch (error) {
      console.error('Failed to load revenue chart:', error);
    }
  }

  async loadUserGrowthChart() {
    const canvas = document.getElementById('user-growth-chart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    try {
      const response = await fetch('/api/v1/admin/charts/user-growth', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
      });
      const data = await response.json();
      
      if (data.success && data.data) {
        this.charts.userGrowth = new Chart(ctx, {
          type: 'bar',
          data: {
            labels: data.data.labels,
            datasets: [{
              label: 'New Users',
              data: data.data.values,
              backgroundColor: '#10b981',
              borderRadius: 8
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { position: 'top' } }
          }
        });
      }
    } catch (error) {
      console.error('Failed to load user growth chart:', error);
    }
  }

  async loadBookStatsChart() {
    const canvas = document.getElementById('book-stats-chart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    try {
      const response = await fetch('/api/v1/admin/charts/book-stats', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
      });
      const data = await response.json();
      
      if (data.success && data.data) {
        this.charts.bookStats = new Chart(ctx, {
          type: 'doughnut',
          data: {
            labels: data.data.labels,
            datasets: [{
              data: data.data.values,
              backgroundColor: ['#6366f1', '#8b5cf6', '#ec4899', '#10b981'],
              borderWidth: 0
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { position: 'bottom' } }
          }
        });
      }
    } catch (error) {
      console.error('Failed to load book stats chart:', error);
    }
  }

  setupDataTables() {
    // Users table
    const usersTable = document.getElementById('users-table');
    if (usersTable) {
      this.initUsersTable();
    }
    
    // Books table
    const booksTable = document.getElementById('books-table');
    if (booksTable) {
      this.initBooksTable();
    }
    
    // Payments table
    const paymentsTable = document.getElementById('payments-table');
    if (paymentsTable) {
      this.initPaymentsTable();
    }
  }

  async initUsersTable() {
    const tbody = document.querySelector('#users-table tbody');
    if (!tbody) return;
    
    try {
      const response = await fetch('/api/v1/admin/users?limit=50', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
      });
      const data = await response.json();
      
      if (data.success && data.data?.items) {
        tbody.innerHTML = data.data.items.map(user => `
          <tr>
            <td>${this.escapeHtml(user.email)}</td>
            <td>${this.escapeHtml(user.full_name)}</td>
            <td><span class="badge badge-${user.account_type}">${user.account_type}</span></td>
            <td><span class="badge badge-${user.subscription_status}">${user.subscription_status}</span></td>
            <td>${new Date(user.created_at).toLocaleDateString()}</td>
            <td>
              <button class="btn-icon edit-user" data-user-id="${user.id}">✏️</button>
              <button class="btn-icon delete-user" data-user-id="${user.id}">🗑️</button>
            </td>
          </tr>
        `).join('');
        
        // Attach event listeners
        document.querySelectorAll('.edit-user').forEach(btn => {
          btn.addEventListener('click', () => this.editUser(btn.dataset.userId));
        });
        document.querySelectorAll('.delete-user').forEach(btn => {
          btn.addEventListener('click', () => this.deleteUser(btn.dataset.userId));
        });
      }
    } catch (error) {
      console.error('Failed to load users:', error);
    }
  }

  async initBooksTable() {
    const tbody = document.querySelector('#books-table tbody');
    if (!tbody) return;
    
    try {
      const response = await fetch('/api/v1/books?limit=50&status=all', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
      });
      const data = await response.json();
      
      if (data.success && data.data?.items) {
        tbody.innerHTML = data.data.items.map(book => `
          <tr>
            <td>${this.escapeHtml(book.title)}</td>
            <td>${this.escapeHtml(book.author_name)}</td>
            <td>$${book.price.toFixed(2)}</td>
            <td><span class="badge badge-${book.status}">${book.status}</span></td>
            <td>${book.downloads_count || 0}</td>
            <td>
              <button class="btn-icon edit-book" data-book-id="${book.id}">✏️</button>
              <button class="btn-icon delete-book" data-book-id="${book.id}">🗑️</button>
              ${book.status !== 'published' ? `<button class="btn-icon publish-book" data-book-id="${book.id}">📢</button>` : ''}
            </td>
          </tr>
        `).join('');
        
        document.querySelectorAll('.edit-book').forEach(btn => {
          btn.addEventListener('click', () => this.editBook(btn.dataset.bookId));
        });
        document.querySelectorAll('.delete-book').forEach(btn => {
          btn.addEventListener('click', () => this.deleteBook(btn.dataset.bookId));
        });
        document.querySelectorAll('.publish-book').forEach(btn => {
          btn.addEventListener('click', () => this.publishBook(btn.dataset.bookId));
        });
      }
    } catch (error) {
      console.error('Failed to load books:', error);
    }
  }

  async initPaymentsTable() {
    const tbody = document.querySelector('#payments-table tbody');
    if (!tbody) return;
    
    try {
      const response = await fetch('/api/v1/admin/payments?limit=50', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
      });
      const data = await response.json();
      
      if (data.success && data.data?.items) {
        tbody.innerHTML = data.data.items.map(payment => `
          <tr>
            <td>${payment.id.slice(0, 8)}</td>
            <td>${payment.user_email || 'N/A'}</td>
            <td>$${payment.amount.toFixed(2)}</td>
            <td>${payment.payment_method}</td>
            <td><span class="badge badge-${payment.status}">${payment.status}</span></td>
            <td>${new Date(payment.created_at).toLocaleDateString()}</td>
            <td>
              <button class="btn-icon view-payment" data-payment-id="${payment.id}">👁️</button>
              ${payment.status === 'completed' ? `<button class="btn-icon refund-payment" data-payment-id="${payment.id}">↩️</button>` : ''}
            </td>
          </tr>
        `).join('');
      }
    } catch (error) {
      console.error('Failed to load payments:', error);
    }
  }

  setupEventListeners() {
    // Sidebar toggle for mobile
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.querySelector('.admin-sidebar');
    
    if (sidebarToggle && sidebar) {
      sidebarToggle.addEventListener('click', () => {
        sidebar.classList.toggle('open');
      });
    }
    
    // Navigation
    const navItems = document.querySelectorAll('.admin-nav-item');
    navItems.forEach(item => {
      item.addEventListener('click', (e) => {
        navItems.forEach(nav => nav.classList.remove('active'));
        item.classList.add('active');
      });
    });
    
    // Quick actions
    const addBookBtn = document.getElementById('add-book-btn');
    if (addBookBtn) {
      addBookBtn.addEventListener('click', () => this.showAddBookModal());
    }
    
    const createSpecialUserBtn = document.getElementById('create-special-user-btn');
    if (createSpecialUserBtn) {
      createSpecialUserBtn.addEventListener('click', () => this.showCreateSpecialUserModal());
    }
    
    const backupBtn = document.getElementById('backup-btn');
    if (backupBtn) {
      backupBtn.addEventListener('click', () => this.triggerBackup());
    }
  }

  async editUser(userId) {
    // Show edit user modal
    window.showToast('Edit user functionality coming soon', 'info');
  }

  async deleteUser(userId) {
    if (!confirm('Are you sure you want to delete this user?')) return;
    
    try {
      const response = await fetch(`/api/v1/admin/users/${userId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
      });
      
      if (response.ok) {
        window.showToast('User deleted successfully', 'success');
        this.initUsersTable();
      } else {
        window.showToast('Failed to delete user', 'error');
      }
    } catch (error) {
      console.error('Failed to delete user:', error);
      window.showToast('Failed to delete user', 'error');
    }
  }

  async editBook(bookId) {
    window.location.href = `/admin/edit-book.html?id=${bookId}`;
  }

  async deleteBook(bookId) {
    if (!confirm('Are you sure you want to delete this book?')) return;
    
    try {
      const response = await fetch(`/api/v1/admin/books/${bookId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
      });
      
      if (response.ok) {
        window.showToast('Book deleted successfully', 'success');
        this.initBooksTable();
      } else {
        window.showToast('Failed to delete book', 'error');
      }
    } catch (error) {
      console.error('Failed to delete book:', error);
      window.showToast('Failed to delete book', 'error');
    }
  }

  async publishBook(bookId) {
    try {
      const response = await fetch(`/api/v1/admin/books/${bookId}/publish`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
      });
      
      if (response.ok) {
        window.showToast('Book published successfully', 'success');
        this.initBooksTable();
      } else {
        window.showToast('Failed to publish book', 'error');
      }
    } catch (error) {
      console.error('Failed to publish book:', error);
      window.showToast('Failed to publish book', 'error');
    }
  }

  async triggerBackup() {
    try {
      const response = await fetch('/api/v1/admin/backup', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
      });
      
      if (response.ok) {
        window.showToast('Backup initiated successfully', 'success');
      } else {
        window.showToast('Failed to start backup', 'error');
      }
    } catch (error) {
      console.error('Failed to trigger backup:', error);
      window.showToast('Failed to start backup', 'error');
    }
  }

  escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
}

// Initialize admin panel
window.adminPanel = new AdminPanel();

document.addEventListener('DOMContentLoaded', () => {
  if (document.querySelector('.admin-container')) {
    window.adminPanel.init();
  }
});
