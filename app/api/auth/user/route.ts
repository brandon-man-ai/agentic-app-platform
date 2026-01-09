import { NextResponse } from 'next/server'
import { getUserFromHeaders } from '@/lib/server-auth'

/**
 * GET /api/auth/user
 * Returns the current user based on X-Forwarded-User header
 */
export async function GET() {
  const session = await getUserFromHeaders()

  if (!session) {
    return NextResponse.json({ user: null }, { status: 200 })
  }

  return NextResponse.json({
    user: session.user,
    access_token: session.access_token,
  })
}
