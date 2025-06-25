import { defineNuxtConfig } from 'nuxt/config'

export default defineNuxtConfig({
  ssr: false,
  modules: ['@nuxtjs/tailwindcss'],
  runtimeConfig: {
    public: {
      clientId: process.env.MARKTPLAATS_CLIENT_ID,
      redirectUri: process.env.AUTH_REDIRECT_URI,
      authBase: 'https://auth.marktplaats.nl/accounts/oauth'
    }
  }
})
