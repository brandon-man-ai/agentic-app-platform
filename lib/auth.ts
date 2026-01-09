import { useUser } from './user-context'
import { UserTeam } from './user-types'

/**
 * Simplified useAuth hook that wraps useUser context.
 * Maintains API compatibility with existing components.
 *
 * Note: The setAuthDialog and setAuthView parameters are kept for backward
 * compatibility but are no longer used since auth is handled externally.
 */
export function useAuth(
  _setAuthDialog?: (value: boolean) => void,
  _setAuthView?: (value: string) => void,
) {
  const { session, isLoading } = useUser()

  // Convert to Supabase-like session format for compatibility with existing code
  const compatSession = session
    ? {
        user: {
          id: session.user.id,
          email: session.user.email,
          user_metadata: {
            avatar_url: session.user.avatar_url,
          },
        },
        access_token: session.access_token,
      }
    : null

  // Create userTeam from user info for backward compatibility
  const userTeam: UserTeam | undefined = session
    ? {
        id: session.user.id,
        email: session.user.email,
        name: session.user.name || session.user.email,
        tier: 'default',
      }
    : undefined

  return {
    session: compatSession,
    userTeam,
    isLoading,
  }
}
