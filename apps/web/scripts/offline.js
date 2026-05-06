// =============================================================================
// OFFLINE.JS - PWA Offline Support and Sync
// =============================================================================

class OfflineManager {
  constructor() {
    this.isOnline = navigator.onLine;
    this.pendingSync = [];
    this.db = null;
    this.ready = false;
  }

  async init() {
    await this.initDatabase();
    await this.loadPendingSync();
    this.setupEventListeners();
    this.ready = true;
    
    // Attempt to sync if online
    if (this.isOnline) {
      this.syncPending();
    }
  }

  async initDatabase() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open('AbdulboyEbookOffline', 1);
      
      request.onerror = () => reject(request.error);
      
      request.onsuccess = () => {
        this.db = request.result;
        resolve();
      };
      
      request.onupgradeneeded = (event) => {
        const db = event.target.result;
        
        // Store for pending operations
        if (!db.objectStoreNames.contains('pendingOperations')) {
          const store = db.createObjectStore('pendingOperations', { 
            keyPath: 'id', 
            autoIncrement: true 
          });
          store.createIndex('type', 'type', { unique: false });
          store.createIndex('timestamp', 'timestamp', { unique: false });
        }
        
        // Store for offline reading
        if (!db.objectStoreNames.contains('offlineBooks')) {
          const bookStore = db.createObjectStore('offlineBooks', { 
            keyPath: 'bookId' 
          });
          bookStore.createIndex('downloadedAt', 'downloadedAt', { unique: false });
        }
        
        // Store for reading progress
        if (!db.objectStoreNames.contains('readingProgress')) {
          db.createObjectStore('readingProgress', { 
            keyPath: 'bookId' 
          });
        }
      };
    });
  }

  setupEventListeners() {
    window.addEventListener('online', () => {
      this.isOnline = true;
      this.showNotification('Back online!', 'Your connection has been restored.');
      this.syncPending();
    });
    
    window.addEventListener('offline', () => {
      this.isOnline = false;
      this.showNotification('You are offline', 'Some features may be limited.', 'warning');
    });
  }

  async loadPendingSync() {
    if (!this.db) return;
    
    const transaction = this.db.transaction(['pendingOperations'], 'readonly');
    const store = transaction.objectStore('pendingOperations');
    const request = store.getAll();
    
    return new Promise((resolve) => {
      request.onsuccess = () => {
        this.pendingSync = request.result;
        resolve();
      };
      request.onerror = () => {
        this.pendingSync = [];
        resolve();
      };
    });
  }

  async addPendingOperation(type, data) {
    if (!this.db) return;
    
    const operation = {
      type: type,
      data: data,
      timestamp: Date.now(),
      retries: 0
    };
    
    const transaction = this.db.transaction(['pendingOperations'], 'readwrite');
    const store = transaction.objectStore('pendingOperations');
    store.add(operation);
    
    this.pendingSync.push(operation);
    
    // If online, try to sync immediately
    if (this.isOnline) {
      this.syncPending();
    }
  }

  async syncPending() {
    if (!this.isOnline || this.pendingSync.length === 0) return;
    
    const operations = [...this.pendingSync];
    const token = localStorage.getItem('access_token');
    
    for (const operation of operations) {
      try {
        let success = false;
        
        switch (operation.type) {
          case 'reading_progress':
            success = await this.syncReadingProgress(operation.data, token);
            break;
          case 'purchase':
            success = await this.syncPurchase(operation.data, token);
            break;
          case 'review':
            success = await this.syncReview(operation.data, token);
            break;
          case 'booking':
            success = await this.syncBooking(operation.data, token);
            break;
        }
        
        if (success) {
          await this.removePendingOperation(operation.id);
          this.pendingSync = this.pendingSync.filter(op => op.id !== operation.id);
        } else if (operation.retries >= 3) {
          // Remove after max retries
          await this.removePendingOperation(operation.id);
          this.pendingSync = this.pendingSync.filter(op => op.id !== operation.id);
          console.error(`Failed to sync operation after ${operation.retries} retries:`, operation);
        } else {
          // Update retry count
          operation.retries++;
          await this.updatePendingOperation(operation);
        }
      } catch (error) {
        console.error('Sync error:', error);
      }
    }
  }

  async syncReadingProgress(data, token) {
    try {
      const response = await fetch('/api/v1/users/reading-progress', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(data)
      });
      return response.ok;
    } catch (error) {
      return false;
    }
  }

  async syncPurchase(data, token) {
    try {
      const response = await fetch('/api/v1/payments/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(data)
      });
      return response.ok;
    } catch (error) {
      return false;
    }
  }

  async syncReview(data, token) {
    try {
      const response = await fetch('/api/v1/books/reviews', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(data)
      });
      return response.ok;
    } catch (error) {
      return false;
    }
  }

  async syncBooking(data, token) {
    try {
      const response = await fetch('/api/v1/bookings', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(data)
      });
      return response.ok;
    } catch (error) {
      return false;
    }
  }

  async removePendingOperation(id) {
    if (!this.db) return;
    
    const transaction = this.db.transaction(['pendingOperations'], 'readwrite');
    const store = transaction.objectStore('pendingOperations');
    store.delete(id);
  }

  async updatePendingOperation(operation) {
    if (!this.db) return;
    
    const transaction = this.db.transaction(['pendingOperations'], 'readwrite');
    const store = transaction.objectStore('pendingOperations');
    store.put(operation);
  }

  async saveOfflineBook(bookId, bookData, content) {
    if (!this.db) return;
    
    const transaction = this.db.transaction(['offlineBooks'], 'readwrite');
    const store = transaction.objectStore('offlineBooks');
    
    const offlineBook = {
      bookId: bookId,
      title: bookData.title,
      author: bookData.author_name,
      coverImage: bookData.cover_image_url,
      content: content,
      downloadedAt: Date.now(),
      size: content.length
    };
    
    store.put(offlineBook);
    
    this.showNotification('Book saved offline', `${bookData.title} is now available offline.`, 'success');
  }

  async getOfflineBook(bookId) {
    if (!this.db) return null;
    
    const transaction = this.db.transaction(['offlineBooks'], 'readonly');
    const store = transaction.objectStore('offlineBooks');
    
    return new Promise((resolve) => {
      const request = store.get(bookId);
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => resolve(null);
    });
  }

  async removeOfflineBook(bookId) {
    if (!this.db) return;
    
    const transaction = this.db.transaction(['offlineBooks'], 'readwrite');
    const store = transaction.objectStore('offlineBooks');
    store.delete(bookId);
  }

  async getOfflineBooks() {
    if (!this.db) return [];
    
    const transaction = this.db.transaction(['offlineBooks'], 'readonly');
    const store = transaction.objectStore('offlineBooks');
    
    return new Promise((resolve) => {
      const request = store.getAll();
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => resolve([]);
    });
  }

  saveReadingProgressOffline(bookId, position) {
    if (!this.db) return;
    
    const transaction = this.db.transaction(['readingProgress'], 'readwrite');
    const store = transaction.objectStore('readingProgress');
    
    store.put({
      bookId: bookId,
      position: position,
      updatedAt: Date.now()
    });
    
    // Queue for sync when online
    this.addPendingOperation('reading_progress', {
      book_id: bookId,
      position: position
    });
  }

  async getReadingProgressOffline(bookId) {
    if (!this.db) return null;
    
    const transaction = this.db.transaction(['readingProgress'], 'readonly');
    const store = transaction.objectStore('readingProgress');
    
    return new Promise((resolve) => {
      const request = store.get(bookId);
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => resolve(null);
    });
  }

  showNotification(title, message, type = 'info') {
    // Use toast notification
    if (window.showToast) {
      window.showToast(message, type);
    }
    
    // Also try push notification if permitted
    if (this.isOnline && 'Notification' in window && Notification.permission === 'granted') {
      new Notification(title, { body: message, icon: '/images/logo/logo-icon.svg' });
    }
  }

  requestNotificationPermission() {
    if ('Notification' in window && Notification.permission !== 'granted') {
      Notification.requestPermission();
    }
  }
}

// Initialize offline manager
window.offlineManager = new OfflineManager();

document.addEventListener('DOMContentLoaded', () => {
  window.offlineManager.init();
});
