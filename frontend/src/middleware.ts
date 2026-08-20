import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Rotas protegidas (tudo dentro de /dashboard, /liderancas, e root / que seja dashboard)
const protectedRoutes = ['/', '/liderancas', '/settings'];

export function middleware(request: NextRequest) {
  const path = request.nextUrl.pathname;
  
  // Considera root (/) e tudo que não for /login, /api, /_next, etc como protegido pelo matcher
  const isProtectedRoute = protectedRoutes.includes(path) || path.startsWith('/liderancas') || path.startsWith('/settings');
  
  if (isProtectedRoute) {
    // Verifica o cookie de sessão (o nome depende de como o backend/Next actions define)
    const token = request.cookies.get('token') || request.cookies.get('session');
    
    if (!token) {
      return NextResponse.redirect(new URL('/login', request.url));
    }
  }
  
  return NextResponse.next();
}

// O Matcher garante que o middleware só rode nas rotas necessárias
export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - login (auth routes)
     */
    '/((?!api|_next/static|_next/image|favicon.ico|login).*)',
  ],
};
