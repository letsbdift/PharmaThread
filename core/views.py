from django.http import HttpResponse, JsonResponse
import json

def manifest_json(request):
    manifest = {
        "name": "PharmaThread POS",
        "short_name": "PharmaThread",
        "description": "Meezan Pharmacy POS & Inventory System",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#0f172a",
        "theme_color": "#0f172a",
        "icons": [
            {
                "src": "/pwa/icon.svg",
                "sizes": "192x192 512x512",
                "type": "image/svg+xml",
                "purpose": "any maskable"
            }
        ]
    }
    return JsonResponse(manifest)

def service_worker(request):
    sw_script = """
const CACHE_NAME = 'pharmathread-v1';
const ASSETS_TO_CACHE = [
    '/login/'
];

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => {
            return cache.addAll(ASSETS_TO_CACHE);
        })
    );
});

self.addEventListener('fetch', event => {
    event.respondWith(
        caches.match(event.request).then(response => {
            // Cache hit - return response
            if (response) {
                return response;
            }
            return fetch(event.request);
        }).catch(() => {
            // Offline fallback
            if (event.request.mode === 'navigate') {
                return caches.match('/login/');
            }
        })
    );
});

self.addEventListener('push', event => {
    const data = event.data ? event.data.json() : {title: 'PharmaThread Notification', body: 'New alert!'};
    event.waitUntil(
        self.registration.showNotification(data.title, {
            body: data.body,
            icon: '/pwa/icon.svg'
        })
    );
});
"""
    return HttpResponse(sw_script, content_type='application/javascript')

def pwa_icon(request):
    svg = '<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg"><g transform="rotate(-45 50 50)"><path d="M 35 50 L 35 70 A 15 15 0 0 0 65 70 L 65 50 Z" fill="#38bdf8"/><path d="M 35 50 L 35 30 A 15 15 0 0 1 65 30 L 65 50 Z" fill="#f8fafc"/><path d="M 30 65 Q 50 75 70 55 M 30 45 Q 50 55 70 35 Q 85 20 60 10" stroke="#10b981" stroke-width="5" fill="none" stroke-linecap="round"/><path d="M 60 10 C 45 -5, 75 -10, 80 5 C 85 20, 70 35, 70 35" stroke="#10b981" stroke-width="5" fill="none" stroke-linecap="round"/></g></svg>'
    return HttpResponse(svg, content_type='image/svg+xml')
