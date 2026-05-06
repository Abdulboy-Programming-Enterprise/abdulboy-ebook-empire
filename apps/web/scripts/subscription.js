// =============================================================================
// SUBSCRIPTION.JS - Subscription Plan Management
// =============================================================================

class SubscriptionManager {
  constructor() {
    this.plans = [];
    this.currentSubscription = null;
    this.user = null;
  }

  async init() {
    await this.loadPlans();
    await this.loadCurrentSubscription();
    this.setupEventListeners();
    this.renderPlans();
  }

  async loadPlans() {
    try {
      const response = await fetch('/api/v1/subscriptions/plans');
      const data = await response.json();
      
      if (data.success) {
        this.plans = data.data;
      }
    } catch (error) {
      console.error('Failed to load subscription plans:', error);
    }
  }

  async loadCurrentSubscription() {
    const token = localStorage.getItem('access_token');
    if (!token) return;
    
    try {
      const response = await fetch('/api/v1/subscriptions/my-subscription', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      
      if (data.success) {
        this.currentSubscription = data.data;
      }
    } catch (error) {
      console.error('Failed to load current subscription:', error);
    }
  }

  renderPlans() {
    const container = document.getElementById('pricing-container');
    if (!container || !this.plans.length) return;
    
    const plansHtml = this.plans.map(plan => `
      <div class="pricing-card ${plan.is_popular ? 'popular' : ''}">
        <div class="pricing-card-inner">
          ${plan.is_popular ? '<div class="popular-badge">Most Popular</div>' : ''}
          <div class="pricing-header">
            <h3 class="plan-name">${this.escapeHtml(plan.name)}</h3>
            <p class="plan-description">${this.escapeHtml(plan.description || '')}</p>
          </div>
          <div class="pricing-price">
            <span class="currency">${plan.currency === 'NGN' ? '₦' : '$'}</span>
            <span class="amount">${plan.price}</span>
            <span class="period">/${plan.interval || 'month'}</span>
          </div>
          <ul class="pricing-features">
            ${plan.features.map(feature => `<li>${this.escapeHtml(feature)}</li>`).join('')}
          </ul>
          <div class="pricing-action">
            ${this.renderPlanButton(plan)}
          </div>
        </div>
      </div>
    `).join('');
    
    container.innerHTML = plansHtml;
    
    // Attach subscribe handlers
    document.querySelectorAll('.subscribe-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const planId = btn.dataset.planId;
        this.subscribeToPlan(planId);
      });
    });
  }

  renderPlanButton(plan) {
    if (this.currentSubscription && this.currentSubscription.is_active) {
      if (this.currentSubscription.plan_name === plan.name) {
        return `<button class="btn btn-secondary" disabled>Current Plan</button>`;
      }
      return `<button class="subscribe-btn" data-plan-id="${plan.id}">Upgrade</button>`;
    }
    return `<button class="subscribe-btn" data-plan-id="${plan.id}">Get Started</button>`;
  }

  async subscribeToPlan(planId) {
    const token = localStorage.getItem('access_token');
    
    if (!token) {
      sessionStorage.setItem('redirect_after_login', '/subscription-plans.html');
      window.location.href = '/login.html';
      return;
    }
    
    const plan = this.plans.find(p => p.id === planId);
    if (!plan) return;
    
    try {
      // Create checkout session
      const response = await fetch('/api/v1/subscriptions/create-checkout', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          plan_id: planId,
          success_url: window.location.origin + '/subscription-success.html',
          cancel_url: window.location.origin + '/subscription-plans.html'
        })
      });
      
      const data = await response.json();
      
      if (data.success && data.data?.checkout_url) {
        window.location.href = data.data.checkout_url;
      } else {
        this.showError('Failed to start subscription process');
      }
    } catch (error) {
      console.error('Failed to subscribe:', error);
      this.showError('Failed to subscribe. Please try again.');
    }
  }

  async cancelSubscription() {
    const token = localStorage.getItem('access_token');
    if (!token) return;
    
    if (!confirm('Are you sure you want to cancel your subscription? You will lose access at the end of your billing period.')) {
      return;
    }
    
    try {
      const response = await fetch('/api/v1/subscriptions/cancel', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      });
      
      const data = await response.json();
      
      if (data.success) {
        window.showToast('Subscription cancelled successfully', 'success');
        this.loadCurrentSubscription();
        this.renderPlans();
      } else {
        this.showError('Failed to cancel subscription');
