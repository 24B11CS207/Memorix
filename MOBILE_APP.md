                                                                                                                                                                                                                                                                                                             # Memorix Mobile App

This project is now configured as a Progressive Web App (PWA).

## How to Use on Mobile

1. Deploy the Django project to a public HTTPS URL.
2. Open that URL on your phone.
3. Android Chrome: tap the browser menu and choose **Install app** or **Add to Home screen**.
4. iPhone Safari: tap **Share** and choose **Add to Home Screen**.

The app uses:

- `manifest.webmanifest` for app name, theme color, launch URL, and icon.
- `service-worker.js` for app-shell caching.
- `static/js/pwa.js` to register the service worker.
- `static/img/memorix-icon.svg` as the app icon.

For a Play Store APK later, wrap the deployed PWA with a Trusted Web Activity or Capacitor after the public HTTPS deployment is working.

## Local Run

On Windows, double-click `run_project.bat`, or run:

```powershell
.\run_project.ps1
```

Keep that terminal open while using:

```text
http://127.0.0.1:8000/

```
