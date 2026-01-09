/**
 * User information extracted from JWT token
 */
export interface User {
  id: string
  email: string
  name?: string
  avatar_url?: string
}

/**
 * Session object containing user info and optional access token
 */
export interface UserSession {
  user: User
  access_token?: string
}

/**
 * Team information for backward compatibility
 */
export interface UserTeam {
  id: string
  email: string
  name: string
  tier: string
}
