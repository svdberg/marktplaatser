# Marktplaatser

This repository contains a backend AWS Lambda application and a minimal Nuxt PWA to authenticate users with the Marktplaats API.

- **marktplaats-backend** – Python code for generating listings and interacting with the Marktplaats API.
- **marktplaats-frontend** – Nuxt 3 PWA with Tailwind CSS demonstrating the OAuth login flow.

## OAuth Demo

Set the following environment variables when running the frontend:

```bash
export MARKTPLAATS_CLIENT_ID=your_client_id
export AUTH_REDIRECT_URI=http://localhost:3000/callback
```

Then run the frontend with `npm install` and `npm run dev` inside `marktplaats-frontend`.
