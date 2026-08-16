const CACHE_NAME = 'mir-samozanyatykh-v8.7.0';
const urlsToCache = [
  '/',
  '/static/css/main.css',
  '/login',
  '/register'
];

self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(urlsToCache)));
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request).then(response => {
      if (response) return response;
      return fetch(event.request);
    })
  );
});
