import { headers } from 'next/headers'
import { decodeJWT, extractUserFromJWT } from './jwt-decode'
import { User, UserSession } from './user-types'

/**
 * Mock user for local/testing environments
 */
const MOCK_USER: User = {
  id: 'dev-user-001',
  email: 'developer@localhost.dev',
  name: 'Local Developer',
  avatar_url: undefined,
}

/**
 * Header name containing the JWT token from GCP Identity-Aware Proxy
 * See: https://cloud.google.com/iap/docs/signed-headers-howto
 */
const AUTH_HEADER = 'x-goog-iap-jwt-assertion'

/**
 * Check if mock auth is enabled via environment variable or development mode
 */
function isMockAuthEnabled(): boolean {
  // Enable mock auth via explicit env var (works in any environment including Docker)
  if (process.env.MOCK_AUTH === 'true') {
    return true
  }
  // Also enable in development mode for convenience
  if (process.env.NODE_ENV === 'development') {
    return true
  }
  return false
}

/**
 * Get user from X-Forwarded-User header (server-side only).
 * Returns mock user if MOCK_AUTH=true or in development mode.
 */
export async function getUserFromHeaders(): Promise<UserSession | null> {
  const headersList = await headers()
  const forwardedUser = headersList.get(AUTH_HEADER)

  // If header is present, decode and extract user
  if (forwardedUser) {
    const payload = decodeJWT(forwardedUser)
    if (!payload) {
      console.warn('[Auth] Invalid JWT in header')
      // Fall through to mock auth fallback
    } else {
      const user = extractUserFromJWT(payload)
      if (user) {
        return {
          user,
          access_token: forwardedUser,
        }
      }
      console.warn('[Auth] Could not extract user from JWT')
    }
  }

  // Mock auth fallback - return mock user if enabled
  if (isMockAuthEnabled()) {
    console.log('[Auth] Using mock user (MOCK_AUTH enabled or development mode)')
    return { user: MOCK_USER }
  }

  // Production without valid header - no user
  console.log('[Auth] No user - X-Forwarded-User header missing and mock auth disabled')
  return null
}
