// =============================================================================
// SEARCH WORKER - Offloads search indexing to background thread
// =============================================================================

// Search index store
let searchIndex = [];
let bookIndex = new Map();
let isReady = false;

// Listen for messages from main thread
self.addEventListener('message', (event) => {
  const { type, payload } = event.data;
  
  switch (type) {
    case 'init':
      initializeIndex(payload);
      break;
    case 'search':
      performSearch(payload);
      break;
    case 'indexBook':
      indexBook(payload);
      break;
    case 'bulkIndex':
      bulkIndex(payload);
      break;
    case 'clear':
      clearIndex();
      break;
    case 'getStatus':
      sendStatus();
      break;
    default:
      self.postMessage({ type: 'error', payload: 'Unknown command' });
  }
});

/**
 * Initialize search index with book data
 */
function initializeIndex(books) {
  try {
    bookIndex.clear();
    searchIndex = [];
    
    books.forEach(book => {
      indexBook(book);
    });
    
    isReady = true;
    self.postMessage({ 
      type: 'ready', 
      payload: { count: searchIndex.length, isReady: true }
    });
  } catch (error) {
    self.postMessage({ type: 'error', payload: error.message });
  }
}

/**
 * Index a single book
 */
function indexBook(book) {
  const tokens = tokenize(book);
  const docId = book.id;
  
  bookIndex.set(docId, book);
  
  tokens.forEach(token => {
    if (!searchIndex[token]) {
      searchIndex[token] = [];
    }
    if (!searchIndex[token].includes(docId)) {
      searchIndex[token].push(docId);
    }
  });
}

/**
 * Bulk index multiple books
 */
function bulkIndex(books) {
  books.forEach(book => indexBook(book));
  self.postMessage({ 
    type: 'indexComplete', 
    payload: { count: books.length, total: searchIndex.length }
  });
}

/**
 * Clear search index
 */
function clearIndex() {
  searchIndex = [];
  bookIndex.clear();
  isReady = false;
  self.postMessage({ type: 'cleared', payload: true });
}

/**
 * Tokenize book for indexing
 */
function tokenize(book) {
  const text = `${book.title} ${book.author_name} ${book.description || ''} ${book.tags?.join(' ') || ''}`.toLowerCase();
  const words = text.match(/\b\w+\b/g) || [];
  
  // Remove common stop words
  const stopWords = new Set([
    'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from', 'has', 'he',
    'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the', 'to', 'was', 'were',
    'will', 'with', 'the', 'this', 'that', 'these', 'those', 'but', 'or', 'so',
    'for', 'nor', 'yet', 'the', 'and', 'of', 'to', 'in', 'for', 'on', 'with'
  ]);
  
  return words.filter(word => word.length > 2 && !stopWords.has(word));
}

/**
 * Perform search query
 */
function performSearch(query) {
  if (!isReady) {
    self.postMessage({ 
      type: 'searchResult', 
      payload: { results: [], total: 0, message: 'Index not ready' }
    });
    return;
  }
  
  const searchTerms = query.toLowerCase().match(/\b\w+\b/g) || [];
  const scores = new Map();
  
  searchTerms.forEach(term => {
    const matchingDocs = searchIndex[term] || [];
    matchingDocs.forEach(docId => {
      const currentScore = scores.get(docId) || 0;
      const book = bookIndex.get(docId);
      
      // Calculate relevance score
      let score = 1;
      if (book.title.toLowerCase().includes(term)) score += 5;
      if (book.author_name.toLowerCase().includes(term)) score += 3;
      if (book.description && book.description.toLowerCase().includes(term)) score += 1;
      
      scores.set(docId, currentScore + score);
    });
  });
  
  // Sort by score
  const results = Array.from(scores.entries())
    .sort((a, b) => b[1] - a[1])
    .map(([docId]) => bookIndex.get(docId));
  
  self.postMessage({ 
    type: 'searchResult', 
    payload: { 
      results: results.slice(0, 100),
      total: results.length,
      query: query,
      timestamp: Date.now()
    }
  });
}

/**
 * Send current status to main thread
 */
function sendStatus() {
  self.postMessage({
    type: 'status',
    payload: {
      isReady: isReady,
      documentCount: bookIndex.size,
      termCount: Object.keys(searchIndex).length
    }
  });
}
