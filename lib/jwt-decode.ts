import { User } from './user-types'

/**
 * JWT payload structure
 */
export interface JWTPayload {
  sub?: string
  email?: string
  name?: string
  picture?: string
  avatar_url?: string
  iat?: number
  exp?: number
  [key: string]: unknown
}

/**
 * Decode a JWT token without signature verification.
 * Trusted because the load balancer handles authentication.
 */
export function decodeJWT(token: string): JWTPayload | null {
  try {
    const parts = token.split('.')
    if (parts.length !== 3) {
      return null
    }

    // Decode base64url payload (part 1)
    const payload = parts[1]
    const decoded = Buffer.from(payload, 'base64url').toString('utf-8')
    return JSON.parse(decoded) as JWTPayload
  } catch (error) {
    console.error('[JWT] Failed to decode token:', error)
    return null
  }
}

/**
 * Extract user info from JWT payload
 */
export function extractUserFromJWT(payload: JWTPayload): User | null {
  if (!payload.email) {
    console.warn('[JWT] No email claim in token')
    return null
  }

  return {
    id: payload.sub || payload.email,
    email: payload.email,
    name: payload.name,
    avatar_url: payload.picture || payload.avatar_url,
  }
}
