/* Network-first asset updates with offline fallback. Progress remains in localStorage. */
const CACHE='woordkracht-static-v3';
const PREFIX='woordkracht-static-';
const ASSETS=['./','./index.html','./styles.css?v=3','./app.js?v=3','./words.json','./a1-words.json','./icon.svg','./manifest.webmanifest'];
self.addEventListener('install',event=>{
  event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(ASSETS)));
  self.skipWaiting();
});
self.addEventListener('activate',event=>{
  event.waitUntil(Promise.all([
    caches.keys().then(keys=>Promise.all(keys.filter(k=>k.startsWith(PREFIX)&&k!==CACHE).map(k=>caches.delete(k)))),
    self.clients.claim()
  ]));
});
self.addEventListener('fetch',event=>{
  const request=event.request;
  if(request.method!=='GET'||new URL(request.url).origin!==location.origin)return;
  event.respondWith(
    fetch(request).then(response=>{
      if(response.ok)event.waitUntil(caches.open(CACHE).then(cache=>cache.put(request,response.clone())));
      return response;
    }).catch(async()=>{
      const cached=await caches.match(request);
      if(cached)return cached;
      if(request.mode==='navigate'){
        const fallback=await caches.match(new URL('./index.html',self.registration.scope).href);
        if(fallback)return fallback;
      }
      return Response.error();
    })
  );
});
