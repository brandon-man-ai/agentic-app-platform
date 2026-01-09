'use client'

import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { usePostHog } from 'posthog-js/react'
import { User, UserSession } from './user-types'

interface UserContextValue {
  session: UserSession | null
  isLoading: boolean
}

const UserContext = createContext<UserContextValue>({
  session: null,
  isLoading: true,
})

export function UserProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<UserSession | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const posthog = usePostHog()

  useEffect(() => {
    async function fetchUser() {
      try {
        const response = await fetch('/api/auth/user')
        const data = await response.json()

        if (data.user) {
          const userSession: UserSession = {
            user: data.user,
            access_token: data.access_token,
          }
          setSession(userSession)

          // PostHog identification
          posthog?.identify(data.user.id, {
            email: data.user.email,
            name: data.user.name,
          })
        }
      } catch (error) {
        console.error('[UserContext] Failed to fetch user:', error)
      } finally {
        setIsLoading(false)
      }
    }

    fetchUser()
  }, [posthog])

  return (
    <UserContext.Provider value={{ session, isLoading }}>
      {children}
    </UserContext.Provider>
  )
}

export function useUser() {
  return useContext(UserContext)
}
