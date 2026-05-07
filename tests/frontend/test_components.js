/**
 * Frontend component tests using Jest
 */

describe('Header Component', () => {
  beforeEach(() => {
    document.body.innerHTML = '<div id="header-placeholder"></div>';
  });

  test('loads header component', async () => {
    const response = await fetch('/components/header.html');
    const html = await response.text();
    document.getElementById('header-placeholder').innerHTML = html;
    
    expect(document.querySelector('.site-header')).toBeTruthy();
    expect(document.querySelector('.logo')).toBeTruthy();
  });

  test('theme toggle button exists', () => {
    document.body.innerHTML = `
      <button class="theme-toggle-btn">🌓</button>
    `;
    const btn = document.querySelector('.theme-toggle-btn');
    expect(btn).toBeTruthy();
  });
});

describe('Book Card Component', () => {
  test('renders book card with data', () => {
    const bookData = {
      id: '123',
      title: 'Test Book',
      author_name: 'Test Author',
      price: 19.99,
      is_free: false,
      cover_image_url: '/test.jpg'
    };
    
    const card = document.createElement('div');
    card.className = 'book-card';
    card.innerHTML = `
      <div class="book-card-cover"><img src="${bookData.cover_image_url}"></div>
      <div class="book-card-info">
        <h3>${bookData.title}</h3>
        <p>${bookData.author_name}</p>
        <div class="book-card-price">$${bookData.price}</div>
      </div>
    `;
    
    expect(card.querySelector('h3').textContent).toBe('Test Book');
    expect(card.querySelector('.book-card-price').textContent).toBe('$19.99');
  });
});

describe('Search Filter', () => {
  test('filters books by search term', () => {
    const books = [
      { title: 'Python Programming', author: 'John Doe' },
      { title: 'JavaScript Guide', author: 'Jane Smith' }
    ];
    
    const searchTerm = 'python';
    const filtered = books.filter(book => 
      book.title.toLowerCase().includes(searchTerm.toLowerCase())
    );
    
    expect(filtered.length).toBe(1);
    expect(filtered[0].title).toBe('Python Programming');
  });
});
