/* =============================================
   CLASSROOM FACE MONITOR — Shared Utilities
   ============================================= */

// Auto-dismiss flash messages after 5s
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.flash').forEach(el => {
    setTimeout(() => dismissFlash(el), 5000);
  });
});

function dismissFlash(el) {
  el.style.transition = 'opacity 0.4s, transform 0.4s';
  el.style.opacity = '0';
  el.style.transform = 'translateY(-8px)';
  setTimeout(() => el.remove(), 400);
}

// Confirm wrapper — returns true/false
function confirmAction(msg) {
  return confirm(msg || 'Are you sure?');
}

// Generic POST helper
async function postJson(url, data = {}) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  return res.json();
}

// Show temporary toast notification
function showToast(msg, type = 'info') {
  const container = document.querySelector('.flash-container') || createToastContainer();
  const el = document.createElement('div');
  el.className = `flash ${type}`;
  el.innerHTML = `<span>${msg}</span><button class="flash-close" onclick="dismissFlash(this.parentElement)">✕</button>`;
  container.appendChild(el);
  setTimeout(() => dismissFlash(el), 4000);
}

function createToastContainer() {
  const c = document.createElement('div');
  c.className = 'flash-container';
  c.style.cssText = 'position:fixed;top:20px;right:20px;z-index:9999;max-width:340px';
  document.body.appendChild(c);
  return c;
}

// Format datetime string
function fmtTime(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

// Highlight active nav item
(function markActiveNav() {
  const path = window.location.pathname;
  document.querySelectorAll('.nav-link').forEach(a => {
    if (a.getAttribute('href') === path) a.classList.add('active');
  });
})();
