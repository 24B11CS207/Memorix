const CACHE_NAME = 'memorix-mobile-v3';
const APP_SHELL = [
  '/',
  '/index.html',
  '/dashboard.html',
  '/classes.html',
  '/learning-mode.html',
  '/subjects.html',
  '/topics-page.html',
  '/learn-module.html',
  '/module-test.html',
  '/deep-dive.html',
  '/ai-tutor.html',
  '/manifest.webmanifest',
  '/static/img/memorix-icon.svg'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(APP_SHELL))
  );
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;

  event.respondWith(
    fetch(event.request)
      .then(response => {
        const copy = response.clone();
        caches.open(CACHE_NAME).then(cache => cache.put(event.request, copy));
        return response;
      })
      .catch(() => caches.match(event.request).then(cached => cached || caches.match('/index.html')))
  );
});
