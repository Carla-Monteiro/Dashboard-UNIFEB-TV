const CACHE_NAME = 'chamados-unifeb-v1';
const urlsToCache = [
  '/',
  '/index.html',
  '/manifest.json',
];

// Instalar o service worker
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
      .then(() => self.skipWaiting())
  );
});

// Ativar o service worker
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Interceptar requisições
self.addEventListener('fetch', event => {
  // Se for uma requisição GET, tentar cache primeiro
  if (event.request.method === 'GET') {
    event.respondWith(
      caches.match(event.request)
        .then(response => {
          // Retornar cache se existir
          if (response) {
            return response;
          }

          // Senão, fazer a requisição
          return fetch(event.request)
            .then(response => {
              // Clonar a resposta
              const responseClone = response.clone();

              // Salvar na cache se for sucesso
              if (response.status === 200 && response.type !== 'error') {
                caches.open(CACHE_NAME).then(cache => {
                  cache.put(event.request, responseClone);
                });
              }

              return response;
            })
            .catch(() => {
              // Se offline e não tem cache, retornar página offline
              return caches.match('/index.html');
            });
        })
    );
  }
  // Para outras requisições, deixar passar normalmente
  else {
    event.respondWith(
      fetch(event.request)
        .catch(() => {
          // Se falhar (offline), tentar do cache
          return caches.match(event.request);
        })
    );
  }
});

console.log('✅ Service Worker instalado com sucesso!');
