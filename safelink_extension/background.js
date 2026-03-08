/**
 * SafeLink AI - Service Worker (Background Script)
 * 
 * Handles background events for the Chrome extension.
 */

// Listen for extension installation
chrome.runtime.onInstalled.addListener((details) => {
  if (details.reason === 'install') {
    console.log('[SafeLink AI] Extension installed successfully');
  }
});

// Listen for messages from content scripts
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.type === 'passwordFieldDetected') {
    console.log('[SafeLink AI] Password field detected from:', sender.url);
    sendResponse({ status: 'acknowledged' });
  }
});

console.log('[SafeLink AI] Service worker loaded');
