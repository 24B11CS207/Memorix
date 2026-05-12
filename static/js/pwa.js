// Unregister any previously installed service workers
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.getRegistrations().then(function(registrations) {
    registrations.forEach(function(reg) { reg.unregister(); });
  });
}
