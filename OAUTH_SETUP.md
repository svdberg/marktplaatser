# OAuth Configuration for Hosted Frontend

## Current Setup

### Frontend Domain
- **Hosted at**: `http://marktplaats-frontend-simple-prod-website.s3-website.eu-west-1.amazonaws.com`

### Backend API
- **API Base**: `https://a6tudg4znk.execute-api.eu-west-1.amazonaws.com/dev`

### OAuth Endpoints
- **Authorization**: `https://a6tudg4znk.execute-api.eu-west-1.amazonaws.com/dev/oauth/authorize`
- **Callback**: `https://a6tudg4znk.execute-api.eu-west-1.amazonaws.com/dev/oauth/callback`

### Redirect URI Configuration
The OAuth callback is now configured to redirect to:
```
http://marktplaats-frontend-simple-prod-website.s3-website.eu-west-1.amazonaws.com/callback
```

## Marktplaats OAuth App Configuration

You'll need to update your Marktplaats OAuth application to allow this redirect URI:

1. **Login to Marktplaats Developer Portal**
2. **Edit your OAuth application**
3. **Add the new redirect URI**:
   ```
   http://marktplaats-frontend-simple-prod-website.s3-website.eu-west-1.amazonaws.com/callback
   ```
4. **Keep the localhost URI for development**:
   ```
   http://localhost:3000/callback
   ```

## Testing the OAuth Flow

1. **Visit your hosted frontend**: http://marktplaats-frontend-simple-prod-website.s3-website.eu-west-1.amazonaws.com
2. **Click "Authorize with Marktplaats"**
3. **Complete OAuth flow on Marktplaats**
4. **Get redirected back to your app**
5. **Upload image and create listings**

## Environment Variables

The backend now uses the `FRONTEND_DOMAIN` environment variable:
```yaml
environment:
  FRONTEND_DOMAIN: marktplaats-frontend-simple-prod-website.s3-website.eu-west-1.amazonaws.com
```

This automatically configures the correct redirect URIs for both authorization and callback.

## Development vs Production

- **Development**: Uses `localhost:3000` for redirects
- **Production**: Uses the hosted S3 domain for redirects
- **Auto-detection**: Based on the API Gateway domain name

## Next Steps

1. Update Marktplaats OAuth app configuration
2. Test the full OAuth flow on the hosted frontend
3. Optional: Set up a custom domain for cleaner URLs