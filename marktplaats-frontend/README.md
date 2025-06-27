# Marktplaats AI Assistant - Frontend

A Progressive Web App (PWA) built with Nuxt 3 and TailwindCSS for generating and creating Marktplaats advertisements using AI.

## Features

- 📸 Upload product images
- 🤖 AI-powered listing generation with Claude 3.7 Sonnet
- 🔑 OAuth 2.0 integration with Marktplaats
- 🎯 Direct advertisement creation on Marktplaats
- 📱 PWA support for mobile devices

## Setup

1. Install dependencies:
```bash
npm install
```

2. Update the API base URL in `nuxt.config.ts` if needed:
```typescript
runtimeConfig: {
  public: {
    apiBaseUrl: 'https://your-api-gateway-url.amazonaws.com/dev'
  }
}
```

3. Run development server:
```bash
npm run dev
```

4. Build for production:
```bash
npm run build
npm run preview
```

## OAuth Flow

1. Click "Authorize with Marktplaats" to start OAuth flow
2. You'll be redirected to Marktplaats authorization
3. After approval, you'll be redirected back with access tokens
4. The app stores your user ID in localStorage
5. You can now create advertisements directly on Marktplaats

## Usage

1. **Authorize**: Click the authorize button to connect your Marktplaats account
2. **Upload Image**: Select a product image from your device
3. **Generate Listing**: AI analyzes the image and creates title, description, and category
4. **Customize**: Edit the generated content and add price/postcode
5. **Create Ad**: Submit to create the actual advertisement on Marktplaats

## API Endpoints

- `GET /oauth/authorize` - Start OAuth flow
- `GET /oauth/callback` - Handle OAuth callback
- `POST /generate-listing` - Generate listing from image
- `POST /create-advertisement` - Create advertisement on Marktplaats

## PWA Features

- Installable on mobile devices
- Offline-ready (basic functionality)
- Native app-like experience
- Push notification support (future feature)