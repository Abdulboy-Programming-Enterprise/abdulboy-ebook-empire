// =============================================================================
// ENCRYPTION WORKER - Handles cryptographic operations in background
// =============================================================================

// Listen for messages from main thread
self.addEventListener('message', async (event) => {
  const { type, payload } = event.data;
  
  switch (type) {
    case 'encrypt':
      await encryptData(payload);
      break;
    case 'decrypt':
      await decryptData(payload);
      break;
    case 'hash':
      generateHash(payload);
      break;
    case 'verifyHash':
      verifyHash(payload);
      break;
    case 'generateKey':
      generateKey(payload);
      break;
    default:
      self.postMessage({ type: 'error', payload: 'Unknown encryption command' });
  }
});

/**
 * Encrypt data using Web Crypto API
 */
async function encryptData({ data, keyId, algorithm = 'AES-GCM' }) {
  try {
    // Get or generate encryption key
    let cryptoKey;
    if (keyId) {
      const storedKey = await getStoredKey(keyId);
      if (storedKey) {
        cryptoKey = storedKey;
      } else {
        cryptoKey = await generateCryptoKey();
        await storeKey(keyId, cryptoKey);
      }
    } else {
      cryptoKey = await generateCryptoKey();
    }
    
    // Encode the data
    const encoder = new TextEncoder();
    const encodedData = encoder.encode(JSON.stringify(data));
    
    // Generate random IV
    const iv = crypto.getRandomValues(new Uint8Array(12));
    
    // Encrypt
    const encrypted = await crypto.subtle.encrypt(
      { name: algorithm, iv },
      cryptoKey,
      encodedData
    );
    
    // Combine IV and encrypted data
    const result = new Uint8Array(iv.length + encrypted.byteLength);
    result.set(iv);
    result.set(new Uint8Array(encrypted), iv.length);
    
    self.postMessage({
      type: 'encrypted',
      payload: {
        data: arrayBufferToBase64(result),
        keyId: keyId,
        algorithm
      }
    });
  } catch (error) {
    self.postMessage({ type: 'error', payload: `Encryption failed: ${error.message}` });
  }
}

/**
 * Decrypt data using Web Crypto API
 */
async function decryptData({ encryptedData, keyId, algorithm = 'AES-GCM' }) {
  try {
    // Get encryption key
    const cryptoKey = await getStoredKey(keyId);
    if (!cryptoKey) {
      throw new Error('Encryption key not found');
    }
    
    // Decode the encrypted data
    const encryptedBytes = base64ToArrayBuffer(encryptedData);
    
    // Extract IV (first 12 bytes)
    const iv = encryptedBytes.slice(0, 12);
    const data = encryptedBytes.slice(12);
    
    // Decrypt
    const decrypted = await crypto.subtle.decrypt(
      { name: algorithm, iv },
      cryptoKey,
      data
    );
    
    // Decode the result
    const decoder = new TextDecoder();
    const decryptedText = decoder.decode(decrypted);
    const result = JSON.parse(decryptedText);
    
    self.postMessage({
      type: 'decrypted',
      payload: result
    });
  } catch (error) {
    self.postMessage({ type: 'error', payload: `Decryption failed: ${error.message}` });
  }
}

/**
 * Generate cryptographic hash of data
 */
async function generateHash({ data, algorithm = 'SHA-256' }) {
  try {
    const encoder = new TextEncoder();
    const encodedData = encoder.encode(JSON.stringify(data));
    
    const hashBuffer = await crypto.subtle.digest(algorithm, encodedData);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    
    self.postMessage({
      type: 'hashGenerated',
      payload: { hash: hashHex, algorithm }
    });
  } catch (error) {
    self.postMessage({ type: 'error', payload: `Hash generation failed: ${error.message}` });
  }
}

/**
 * Verify hash against data
 */
async function verifyHash({ data, hash, algorithm = 'SHA-256' }) {
  try {
    const encoder = new TextEncoder();
    const encodedData = encoder.encode(JSON.stringify(data));
    
    const hashBuffer = await crypto.subtle.digest(algorithm, encodedData);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const computedHash = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    
    self.postMessage({
      type: 'hashVerified',
      payload: { valid: computedHash === hash }
    });
  } catch (error) {
    self.postMessage({ type: 'error', payload: `Hash verification failed: ${error.message}` });
  }
}

/**
 * Generate a new cryptographic key
 */
async function generateKey({ keyId, algorithm = 'AES-GCM' }) {
  try {
    const cryptoKey = await generateCryptoKey();
    await storeKey(keyId, cryptoKey);
    
    // Export the key for storage (wrapped)
    const exportedKey = await crypto.subtle.exportKey('raw', cryptoKey);
    const keyBase64 = arrayBufferToBase64(exportedKey);
    
    self.postMessage({
      type: 'keyGenerated',
      payload: { keyId, key: keyBase64 }
    });
  } catch (error) {
    self.postMessage({ type: 'error', payload: `Key generation failed: ${error.message}` });
  }
}

/**
 * Generate a crypto key for encryption
 */
async function generateCryptoKey() {
  return await crypto.subtle.generateKey(
    { name: 'AES-GCM', length: 256 },
    true,
    ['encrypt', 'decrypt']
  );
}

/**
 * Store encryption key in IndexedDB
 */
async function storeKey(keyId, cryptoKey) {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('AbdulboyEbookKeys', 1);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => {
      const db = request.result;
      const transaction = db.transaction(['keys'], 'readwrite');
      const store = transaction.objectStore('keys');
      store.put(cryptoKey, keyId);
      transaction.oncomplete = () => resolve();
      transaction.onerror = () => reject(transaction.error);
    };
    
    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains('keys')) {
        db.createObjectStore('keys');
      }
    };
  });
}

/**
 * Retrieve stored encryption key
 */
async function getStoredKey(keyId) {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('AbdulboyEbookKeys', 1);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => {
      const db = request.result;
      const transaction = db.transaction(['keys'], 'readonly');
      const store = transaction.objectStore('keys');
      const getRequest = store.get(keyId);
      
      getRequest.onsuccess = () => resolve(getRequest.result);
      getRequest.onerror = () => reject(getRequest.error);
    };
    
    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains('keys')) {
        db.createObjectStore('keys');
      }
    };
  });
}

/**
 * Convert ArrayBuffer to Base64 string
 */
function arrayBufferToBase64(buffer) {
  const bytes = new Uint8Array(buffer);
  let binary = '';
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}

/**
 * Convert Base64 string to ArrayBuffer
 */
function base64ToArrayBuffer(base64) {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes.buffer;
}
