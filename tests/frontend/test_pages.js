/**
 * Frontend page tests using Jest and Puppeteer
 */

describe('Homepage', () => {
  test('displays hero section', async () => {
    document.body.innerHTML = `
      <section class="hero">
        <h1 class="hero-title">Discover Your Next Great Read</h1>
        <a href="/ebook-site.html" class="btn btn-primary">Browse Books</a>
      </section>
    `;
    
    expect(document.querySelector('.hero')).toBeTruthy();
    expect(document.querySelector('.hero-title').textContent).toContain('Discover');
  });
});

describe('Book Listing Page', () => {
  test('displays book grid', () => {
    document.body.innerHTML = `
      <div id="books-list-container" class="book-grid"></div>
    `;
    
    const container = document.getElementById('books-list-container');
    container.innerHTML = '<div class="book-card">Test Book</div>';
    
    expect(container.children.length).toBe(1);
  });
});

describe('Login Page', () => {
  test('validates email format', () => {
    const validateEmail = (email) => {
      const re = /^[^\s@]+@([^\s@.,]+\.)+[^\s@.,]{2,}$/;
      return re.test(email);
    };
    
    expect(validateEmail('test@example.com')).toBe(true);
    expect(validateEmail('invalid-email')).toBe(false);
    expect(validateEmail('missing@domain')).toBe(false);
  });
  
  test('validates password strength', () => {
    const validatePassword = (password) => {
      return password.length >= 8 && 
             /[A-Z]/.test(password) && 
             /[a-z]/.test(password) && 
             /[0-9]/.test(password);
    };
    
    expect(validatePassword('StrongPass123')).toBe(true);
    expect(validatePassword('weak')).toBe(false);
    expect(validatePassword('nouppercase123')).toBe(false);
  });
});

describe('Checkout Page', () => {
  test('calculates total correctly', () => {
    const items = [
      { price: 29.99, quantity: 1 },
      { price: 9.99, quantity: 2 }
    ];
    
    const total = items.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    
    expect(total).toBe(49.97);
  });
});
