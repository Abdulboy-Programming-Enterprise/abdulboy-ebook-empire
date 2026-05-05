// =============================================================================
// AUTH.JS - Authentication and User Management
// =============================================================================

class AuthManager {
  constructor() {
    this.token = localStorage.getItem('access_token');
    this.refreshToken = localStorage.getItem('refresh_token');
    this.user = null;
    this.isAuthenticated = !!this.token;
  }
  
  async init() {
    if (this.token) {
      await this.loadUser();
      this.startTokenRefreshTimer();
    }
    
    this.setupAuthForms();
    this.setupProtectedRoutes();
  }
  
  async loadUser() {
    try {
      const response = await fetch('/api/v1/users/me', {
        headers: { 'Authorization': `Bearer ${this.token}` }
      });
      
      if (response.ok) {
        this.user = await response.json();
        this.isAuthenticated = true;
        document.dispatchEvent(new CustomEvent('auth:user-loaded', { detail: this.user }));
      } else {
        this.logout();
      }
    } catch (error) {
      console.error('Failed to load user:', error);
      this.logout();
    }
  }
  
  async login(email, password) {
    try {
      const response = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      
      const data = await response.json();
      
      if (response.ok && data.success) {
        this.token = data.data.access_token;
        this.refreshToken = data.data.refresh_token;
        localStorage.setItem('access_token', this.token);
        localStorage.setItem('refresh_token', this.refreshToken);
        
        await this.loadUser();
        this.startTokenRefreshTimer();
        
        window.showToast('Login successful!', 'success');
        
        // Redirect to previous page or dashboard
        const redirect = sessionStorage.getItem('redirect_after_login') || '/user-dashboard.html';
        sessionStorage.removeItem('redirect_after_login');
        window.location.href = redirect;
        
        return true;
      } else {
        window.showToast(data.message || 'Login failed', 'error');
        return false;
      }
    } catch (error) {
      console.error('Login error:', error);
      window.showToast('Login failed. Please try again.', 'error');
      return false;
    }
  }
  
  async register(userData) {
    try {
      const response = await fetch('/api/v1/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(userData)
      });
      
      const data = await response.json();
      
      if (response.ok && data.success) {
        window.showToast('Registration successful! Please check your email to verify your account.', 'success');
        
        // Auto-login after registration
        await this.login(userData.email, userData.password);
        return true;
      } else {
        window.showToast(data.message || 'Registration failed', 'error');
        return false;
      }
    } catch (error) {
      console.error('Registration error:', error);
      window.showToast('Registration failed. Please try again.', 'error');
      return false;
    }
  }
  
  async logout() {
    try {
      await fetch('/api/v1/auth/logout', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${this.token}` }
      });
    } catch (error) {
      console.error('Logout error:', error);
    }
    
    this.token = null;
    this.refreshToken = null;
    this.user = null;
    this.isAuthenticated = false;
    
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    
    window.showToast('Logged out successfully', 'info');
    window.location.href = '/';
  }
  
  async refreshToken() {
    if (!this.refreshToken) return false;
    
    try {
      const response = await fetch('/api/v1/auth/refresh', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: this.refreshToken })
      });
      
      const data = await response.json();
      
      if (response.ok && data.success) {
        this.token = data.data.access_token;
        this.refreshToken = data.data.refresh_token;
        localStorage.setItem('access_token', this.token);
        localStorage.setItem('refresh_token', this.refreshToken);
        return true;
      } else {
        this.logout();
        return false;
      }
    } catch (error) {
      console.error('Token refresh failed:', error);
      this.logout();
      return false;
    }
  }
  
  startTokenRefreshTimer() {
    // Refresh token every 25 minutes (access token expires in 30)
    setInterval(async () => {
      if (this.isAuthenticated) {
        await this.refreshToken();
      }
    }, 25 * 60 * 1000);
  }
  
  setupAuthForms() {
    // Login form
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
      loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = loginForm.querySelector('#email').value;
        const password = loginForm.querySelector('#password').value;
        await this.login(email, password);
      });
    }
    
    // Register form
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
      registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const userData = {
          email: registerForm.querySelector('#email').value,
          password: registerForm.querySelector('#password').value,
          confirm_password: registerForm.querySelector('#confirm_password').value,
          full_name: registerForm.querySelector('#full_name').value
        };
        
        if (userData.password !== userData.confirm_password) {
          window.showToast('Passwords do not match', 'error');
          return;
        }
        
        await this.register(userData);
      });
    }
    
    // Forgot password form
    const forgotForm = document.getElementById('forgot-password-form');
    if (forgotForm) {
      forgotForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = forgotForm.querySelector('#email').value;
        
        try {
          const response = await fetch('/api/v1/auth/forgot-password', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email })
          });
          
          const data = await response.json();
          window.showToast(data.message || 'If an account exists, you will receive a reset link', 'info');
          forgotForm.reset();
        } catch (error) {
          console.error('Forgot password error:', error);
          window.showToast('Something went wrong. Please try again.', 'error');
        }
      });
    }
    
    // Reset password form
    const resetForm = document.getElementById('reset-password-form');
    if (resetForm) {
      resetForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const token = new URLSearchParams(window.location.search).get('token');
        const newPassword = resetForm.querySelector('#new_password').value;
        const confirmPassword = resetForm.querySelector('#confirm_password').value;
        
        if (newPassword !== confirmPassword) {
          window.showToast('Passwords do not match', 'error');
          return;
        }
        
        try {
          const response = await fetch('/api/v1/auth/reset-password', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token, new_password: newPassword, confirm_password: confirmPassword })
          });
          
          const data = await response.json();
          
          if (response.ok && data.success) {
            window.showToast('Password reset successful! Please login.', 'success');
            setTimeout(() => {
              window.location.href = '/login.html';
            }, 2000);
          } else {
            window.showToast(data.message || 'Password reset failed', 'error');
          }
        } catch (error) {
          console.error('Reset password error:', error);
          window.showToast('Something went wrong. Please try again.', 'error');
        }
      });
    }
  }
  
  setupProtectedRoutes() {
    // Check if current page requires authentication
    const protectedPages = ['/user-dashboard.html', '/checkout.html', '/cart.html'];
    const currentPath = window.location.pathname;
    
    if (protectedPages.includes(currentPath) && !this.isAuthenticated) {
      sessionStorage.setItem('redirect_after_login', currentPath);
      window.location.href = '/login.html';
    }
  }
  
  getAuthHeaders() {
    return {
      'Authorization': `Bearer ${this.token}`,
      'Content-Type': 'application/json'
    };
  }
}

// Initialize auth manager
window.authManager = new AuthManager();

document.addEventListener('DOMContentLoaded', () => {
  window.authManager.init();
});
