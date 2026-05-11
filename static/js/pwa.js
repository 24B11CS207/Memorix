(function () {
  if (!('serviceWorker' in navigator)) return;

  window.addEventListener('load', function () {
    navigator.serviceWorker.register('/service-worker.js').catch(function () {
      // The app still works normally if the browser blocks service workers.
    });
  });
})();
