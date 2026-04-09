// background.js — Service Worker (Manifest V3)
// Receives deal counts from content script and updates the extension badge.

// Track unique tabs that found deals this service-worker session
// (resets on browser restart — intentional, gives organic repeat counts)
const countedTabs = new Set();

chrome.runtime.onMessage.addListener((msg, sender) => {
  if (msg.type !== 'DEAL_COUNT') return;

  const tabId = sender.tab?.id;
  if (!tabId) return;

  const count = msg.count || 0;
  const text  = count > 0 ? String(count) : '';
  const color = count > 0 ? '#e85d04' : '#888888';

  chrome.action.setBadgeText({ text, tabId });
  chrome.action.setBadgeBackgroundColor({ color, tabId });
  chrome.action.setBadgeTextColor({ color: '#ffffff', tabId });

  // Increment session counter once per unique tab that found deals
  // Used to trigger "please review" nudge after 10 deal-finding sessions
  if (count > 0 && !countedTabs.has(tabId)) {
    countedTabs.add(tabId);
    chrome.storage.local.get({ sessionCount: 0, reviewDismissed: false }, (data) => {
      if (!data.reviewDismissed) {
        chrome.storage.local.set({ sessionCount: data.sessionCount + 1 });
      }
    });
  }
});

// ── Keyboard shortcut: Ctrl+Shift+W toggles Walmart Direct filter ────────────

chrome.commands.onCommand.addListener((command) => {
  if (command !== 'toggle-filter') return;
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    const tab = tabs[0];
    if (!tab?.url?.includes('walmart.com')) return;
    chrome.storage.sync.get({ filterThirdParty: true }, (s) => {
      const newVal = !s.filterThirdParty;
      chrome.storage.sync.set({ filterThirdParty: newVal });
      chrome.tabs.sendMessage(tab.id, {
        type: 'SETTINGS_UPDATED',
        settings: { filterThirdParty: newVal },
      });
    });
  });
});

// Clear badge when navigating away from walmart.com
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'loading') {
    // Remove from counted set so navigating to a new search counts again
    countedTabs.delete(tabId);
    if (tab.url && !tab.url.includes('walmart.com')) {
      chrome.action.setBadgeText({ text: '', tabId });
    }
  }
});
