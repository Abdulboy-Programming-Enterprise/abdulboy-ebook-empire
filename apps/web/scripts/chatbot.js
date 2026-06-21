// =============================================================================
// CHATBOT.JS - AI Chatbot Widget
// =============================================================================

class ChatbotWidget {
  constructor() {
    this.isOpen = false;
    this.sessionId = localStorage.getItem('chat_session_id') || this.generateSessionId();
    this.messageHistory = [];
    this.typingTimeout = null;
    this.unreadCount = 0;
  }
  
  init() {
    this.setupEventListeners();
    this.loadChatHistory();
    this.updateUnreadCount();
  }
  
  // ===========================================================================
  // SECURE SESSION ID GENERATION - CRYPTOGRAPHICALLY SECURE
  // ===========================================================================
  
  /**
   * Generates a cryptographically secure session ID
   * Uses crypto.randomUUID() if available, falls back to crypto.getRandomValues()
   * @returns {string} Secure session ID
   */
  generateSessionId() {
    let sessionId;
    
    // Option 1: Use crypto.randomUUID() (modern browsers, Node.js 14+)
    if (window.crypto && window.crypto.randomUUID) {
      sessionId = 'chat_' + crypto.randomUUID();
    } 
    // Option 2: Fallback to crypto.getRandomValues() (all modern browsers)
    else if (window.crypto && window.crypto.getRandomValues) {
      const array = new Uint8Array(16);
      crypto.getRandomValues(array);
      sessionId = 'chat_' + Array.from(array)
        .map(b => b.toString(16).padStart(2, '0'))
        .join('');
    } 
    // Option 3: Last resort fallback (should never happen in modern browsers)
    else {
      // Use a combination of timestamp and random (less secure but better than nothing)
      sessionId = 'chat_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
      console.warn('Crypto API not available, using fallback RNG');
    }
    
    localStorage.setItem('chat_session_id', sessionId);
    return sessionId;
  }
  
  // ===========================================================================
  // EVENT SETUP
  // ===========================================================================
  
  setupEventListeners() {
    const toggleBtn = document.getElementById('chat-toggle-btn');
    const closeBtn = document.getElementById('chat-minimize-btn');
    const sendBtn = document.getElementById('chat-send-btn');
    const input = document.getElementById('chat-input');
    const quickReplies = document.querySelectorAll('.quick-reply');
    
    if (toggleBtn) {
      toggleBtn.addEventListener('click', () => this.toggleChat());
    }
    
    if (closeBtn) {
      closeBtn.addEventListener('click', () => this.closeChat());
    }
    
    if (sendBtn) {
      sendBtn.addEventListener('click', () => this.sendMessage());
    }
    
    if (input) {
      input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          this.sendMessage();
        }
      });
      
      input.addEventListener('input', () => this.autoResizeTextarea());
    }
    
    quickReplies.forEach(btn => {
      btn.addEventListener('click', () => {
        const query = btn.dataset.query;
        if (query) this.sendMessage(query);
      });
    });
  }
  
  // ===========================================================================
  // CHAT UI CONTROLS
  // ===========================================================================
  
  toggleChat() {
    this.isOpen = !this.isOpen;
    const chatWindow = document.getElementById('chat-window');
    const chatIcon = document.querySelector('.chat-icon');
    const closeIcon = document.querySelector('.close-icon');
    const notificationBadge = document.getElementById('chat-notification');
    
    if (chatWindow) {
      chatWindow.style.display = this.isOpen ? 'flex' : 'none';
    }
    
    if (chatIcon && closeIcon) {
      chatIcon.style.display = this.isOpen ? 'none' : 'block';
      closeIcon.style.display = this.isOpen ? 'block' : 'none';
    }
    
    if (this.isOpen) {
      if (notificationBadge) notificationBadge.style.display = 'none';
      this.updateUnreadCount(0);
      this.scrollToBottom();
    }
  }
  
  closeChat() {
    this.isOpen = false;
    const chatWindow = document.getElementById('chat-window');
    const chatIcon = document.querySelector('.chat-icon');
    const closeIcon = document.querySelector('.close-icon');
    
    if (chatWindow) chatWindow.style.display = 'none';
    if (chatIcon) chatIcon.style.display = 'block';
    if (closeIcon) closeIcon.style.display = 'none';
  }
  
  // ===========================================================================
  // MESSAGE SENDING
  // ===========================================================================
  
  async sendMessage(message = null) {
    const input = document.getElementById('chat-input');
    const messageText = message || input?.value.trim();
    
    if (!messageText) return;
    
    // Clear input
    if (input) input.value = '';
    this.autoResizeTextarea();
    
    // Add user message to UI
    this.addMessage(messageText, 'user');
    
    // Show typing indicator
    this.showTyping();
    
    try {
      const response = await fetch('/api/v1/chatbot/message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: messageText,
          session_id: this.sessionId
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      // Hide typing indicator
      this.hideTyping();
      
      // Add bot response
      if (data.reply) {
        this.addMessage(data.reply, 'bot');
        
        // Update session ID if provided
        if (data.session_id) {
          this.sessionId = data.session_id;
          localStorage.setItem('chat_session_id', this.sessionId);
        }
      } else {
        this.addMessage("I'm sorry, I didn't understand that. Can you please rephrase?", 'bot');
      }
    } catch (error) {
      console.error('Chatbot error:', error);
      this.hideTyping();
      this.addMessage("I'm having trouble connecting right now. Please try again later.", 'bot');
    }
  }
  
  // ===========================================================================
  // MESSAGE RENDERING - WITH XSS PROTECTION
  // ===========================================================================
  
  /**
   * Adds a message to the chat UI
   * @param {string} text - Message text
   * @param {string} sender - 'user' or 'bot'
   * @param {boolean} save - Whether to save to history
   */
  addMessage(text, sender, save = true) {
    const messagesContainer = document.getElementById('chat-messages');
    if (!messagesContainer) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender === 'user' ? 'user-message' : 'bot-message'}`;
    
    const avatarHtml = sender === 'bot' 
      ? `<div class="message-avatar"><img src="/images/logo/logo-icon.svg" alt="Bot"></div>`
      : `<div class="message-avatar"><img src="/images/default-avatar.png" alt="User"></div>`;
    
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    // Use escapeHtml for safety - prevents XSS
    messageDiv.innerHTML = `
      ${avatarHtml}
      <div class="message-content">
        <p>${this.escapeHtml(text)}</p>
      </div>
      <div class="message-time">${this.escapeHtml(time)}</div>
    `;
    
    messagesContainer.appendChild(messageDiv);
    this.scrollToBottom();
    
    // Save to history
    if (save) {
      this.messageHistory.push({ text, sender, time });
      this.saveChatHistory();
    }
  }
  
  // ===========================================================================
  // TYPING INDICATOR
  // ===========================================================================
  
  showTyping() {
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) {
      typingIndicator.style.display = 'flex';
      this.scrollToBottom();
    }
  }
  
  hideTyping() {
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) {
      typingIndicator.style.display = 'none';
    }
  }
  
  // ===========================================================================
  // UTILITY METHODS
  // ===========================================================================
  
  scrollToBottom() {
    const messagesContainer = document.getElementById('chat-messages');
    if (messagesContainer) {
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
  }
  
  autoResizeTextarea() {
    const textarea = document.getElementById('chat-input');
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = Math.min(textarea.scrollHeight, 100) + 'px';
    }
  }
  
  // ===========================================================================
  // HISTORY MANAGEMENT
  // ===========================================================================
  
  saveChatHistory() {
    try {
      // Keep last 50 messages
      const historyToSave = this.messageHistory.slice(-50);
      localStorage.setItem('chat_history', JSON.stringify(historyToSave));
    } catch (e) {
      console.error('Failed to save chat history:', e);
    }
  }
  
  loadChatHistory() {
    try {
      const savedHistory = localStorage.getItem('chat_history');
      if (savedHistory) {
        const history = JSON.parse(savedHistory);
        history.forEach(msg => {
          this.addMessage(msg.text, msg.sender, false);
        });
        this.messageHistory = history;
      }
    } catch (e) {
      console.error('Failed to load chat history:', e);
    }
  }
  
  // ===========================================================================
  // NOTIFICATION MANAGEMENT
  // ===========================================================================
  
  updateUnreadCount(count = null) {
    if (count !== null) {
      this.unreadCount = count;
    } else {
      // Count messages in history that are from bot and not seen
      this.unreadCount = this.messageHistory.filter(m => m.sender === 'bot' && !m.seen).length;
    }
    
    const badge = document.getElementById('chat-notification');
    if (badge) {
      if (this.unreadCount > 0 && !this.isOpen) {
        badge.style.display = 'flex';
        badge.textContent = this.unreadCount > 99 ? '99+' : this.unreadCount;
      } else {
        badge.style.display = 'none';
      }
    }
  }
  
  // ===========================================================================
  // XSS PREVENTION - HTML ESCAPING
  // ===========================================================================
  
  /**
   * Safely escapes HTML content to prevent XSS attacks
   * @param {string} text - Text to escape
   * @returns {string} Escaped HTML-safe text
   */
  escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
}

// Initialize chatbot
window.chatbot = new ChatbotWidget();

document.addEventListener('DOMContentLoaded', () => {
  window.chatbot.init();
});
