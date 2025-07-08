/**
 * API client for the Plantangenet session dashboard
 */

const API_BASE = 'http://localhost:8081';  // Proxied to localhost:8000 by Vite

/**
 * Fetch session data from the backend
 * @returns {Promise<Object>} Session data including dashboard objects, compositors, etc.
 */
export async function fetchSessionData() {
  const response = await fetch(`${API_BASE}/api/session`);
  
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }
  
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    throw new Error('Backend response is not JSON');
  }
  
  return await response.json();
}

/**
 * Get the asset URL for a dashboard object
 * @param {string} objectId - The object ID
 * @param {string} asset - Asset type ('default' or 'widget')
 * @returns {string} Asset URL
 */
export function getAssetUrl(objectId, asset = 'default') {
  return `${API_BASE}/asset/${objectId}?asset=${asset}`;
}

/**
 * Get the stream URL for a dashboard object
 * @param {string} objectId - The object ID
 * @param {string} asset - Asset type ('default' or 'widget')
 * @returns {string} Stream URL
 */
export function getStreamUrl(objectId, asset = 'default') {
  return `${API_BASE}/stream/${objectId}?asset=${asset}`;
}
