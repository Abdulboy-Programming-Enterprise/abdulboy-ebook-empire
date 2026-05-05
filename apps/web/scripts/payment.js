// =============================================================================
// PAYMENT.JS - Payment Processing and Checkout
// =============================================================================

class PaymentProcessor {
  constructor() {
    this.stripe = null;
    this.stripeElements = null;
    this.currentPaymentIntent = null;
  }
  
  async init() {
    await this.loadStripe();
    this.setupCheckoutForm();
    this.setupPaymentMethods();
  }
  
  async loadStripe() {
    if (typeof Stripe !== 'undefined') {
      const stripeKey = window.siteConfig?.payments?.stripe?.publicKey || '';
      this.stripe = Stripe(stripeKey);
    }
  }
  
  setupCheckoutForm() {
    const checkoutForm = document.getElementById('checkout-form');
    if (!checkoutForm) return;
    
    checkoutForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      await this.processCheckout();
    });
  }
  
  setupPaymentMethods() {
    const paymentMethods = document.querySelectorAll('.payment-method-input');
    paymentMethods.forEach(method => {
      method.addEventListener('change', (e) => {
        this.selectedPaymentMethod = e.target.value;
        this.updatePaymentUI();
      });
    });
  }
  
  async processCheckout() {
    const loadingBtn = document.querySelector('#checkout-submit');
    const originalText = loadingBtn?.textContent;
    
    if (loadingBtn) {
      loadingBtn.disabled = true;
      loadingBtn.textContent = 'Processing...';
    }
    
    try {
      // Get cart/checkout data
      const bookId = new URLSearchParams(window.location.search).get('book_id');
      const planId = new URLSearchParams(window.location.search).get('plan_id');
      
      let amount = 0;
      let itemType = '';
      let itemId = '';
      
      if (bookId) {
        // Fetch book details
        const bookResponse = await fetch(`/api/v1/books/${bookId}`);
        const bookData = await bookResponse.json();
        if (bookData.success) {
          amount = bookData.data.price;
          itemType = 'book';
          itemId = bookId;
        }
      } else if (planId) {
        // Fetch plan details
        const planResponse = await fetch(`/api/v1/subscriptions/plans/${planId}`);
        const planData = await planResponse.json();
        if (planData.success) {
          amount = planData.data.price;
          itemType = 'subscription';
          itemId = planId;
        }
      }
      
      // Create payment intent
      const response = await fetch('/api/v1/payments/create-intent', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({
          amount,
          currency: 'usd',
          payment_method: this.selectedPaymentMethod || 'stripe',
          item_type: itemType,
          item_id: itemId,
          success_url: window.location.origin + '/payment-success.html',
          cancel_url: window.location.origin + '/payment-cancel.html'
        })
      });
      
      const data = await response.json();
      
      if (data.success && data.data) {
        this.currentPaymentIntent = data.data;
        
        if (data.data.client_secret) {
          // Stripe payment
          await this.handleStripePayment(data.data.client_secret);
        } else if (data.data.checkout_url) {
          // OPay or redirect payment
          window.location.href = data.data.checkout_url;
        } else if (data.data.redirect_url) {
          window.location.href = data.data.redirect_url;
        }
      } else {
        window.showToast(data.message || 'Payment initialization failed', 'error');
      }
    } catch (error) {
      console.error('Checkout error:', error);
      window.showToast('Payment processing failed. Please try again.', 'error');
    } finally {
      if (loadingBtn) {
        loadingBtn.disabled = false;
        loadingBtn.textContent = originalText;
      }
    }
  }
  
  async handleStripePayment(clientSecret) {
    if (!this.stripe) {
      window.showToast('Payment system not ready', 'error');
      return;
    }
    
    const elements = this.stripe.elements();
    const cardElement = elements.create('card');
    cardElement.mount('#card-element');
    
    const result = await this.stripe.confirmCardPayment(clientSecret, {
      payment_method: {
        card: cardElement
      }
    });
    
    if (result.error) {
      window.showToast(result.error.message, 'error');
    } else if (result.paymentIntent.status === 'succeeded') {
      window.showToast('Payment successful!', 'success');
      await this.verifyPayment(result.paymentIntent.id);
    }
  }
  
  async verifyPayment(paymentIntentId) {
    try {
      const response = await fetch('/api/v1/payments/verify', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({
          payment_id: this.currentPaymentIntent.payment_id,
          transaction_id: paymentIntentId
        })
      });
      
      const data = await response.json();
      
      if (data.success && data.data?.status === 'completed') {
        window.location.href = '/payment-success.html?payment_id=' + this.currentPaymentIntent.payment_id;
      } else {
        window.location.href = '/payment-failed.html';
      }
    } catch (error) {
      console.error('Payment verification error:', error);
      window.location.href = '/payment-failed.html';
    }
  }
  
  updatePaymentUI() {
    const stripeFields = document.getElementById('stripe-fields');
    const opayFields = document.getElementById('opay-fields');
    
    if (this.selectedPaymentMethod === 'stripe') {
      if (stripeFields) stripeFields.style.display = 'block';
      if (opayFields) opayFields.style.display = 'none';
    } else if (this.selectedPaymentMethod === 'opay') {
      if (stripeFields) stripeFields.style.display = 'none';
      if (opayFields) opayFields.style.display = 'block';
    }
  }
  
  async handlePaymentSuccess(paymentId) {
    // Update UI to show success
    const successContainer = document.getElementById('payment-success-container');
    if (successContainer) {
      successContainer.style.display = 'block';
    }
    
    // Load order details
    try {
      const response = await fetch(`/api/v1/payments/${paymentId}`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
      });
      const data = await response.json();
      
      if (data.success && data.data) {
        this.displayOrderDetails(data.data);
      }
    } catch (error) {
      console.error('Failed to load order details:', error);
    }
  }
  
  displayOrderDetails(payment) {
    const container = document.getElementById('order-details');
    if (!container) return;
    
    container.innerHTML = `
      <div class="order-summary">
        <h3>Order #${payment.id.slice(0, 8)}</h3>
        <p>Date: ${new Date(payment.created_at).toLocaleString()}</p>
        <p>Amount: $${payment.amount.toFixed(2)}</p>
        <p>Status: ${payment.status}</p>
        <p>Payment Method: ${payment.payment_method}</p>
      </div>
    `;
  }
}

// Initialize payment processor
window.paymentProcessor = new PaymentProcessor();

document.addEventListener('DOMContentLoaded', () => {
  window.paymentProcessor.init();
});
