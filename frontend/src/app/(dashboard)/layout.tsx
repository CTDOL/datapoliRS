'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Link from 'next/link';
import { useAuthStore } from '@/stores/useAuthStore';
import { api } from '@/services/api';
import { Map, Users, FileText, Landmark, Settings, LogOut, Shield, Globe, Menu, X } from 'lucide-react';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, logout, login } = useAuthStore();
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  // A store (Zustand, sem persist) some num refresh de página; o cookie
  // HttpOnly continua válido. Sem isso, o botão de admin (role) some ao dar F5.
  useEffect(() => {
    if (user) return;
    api
      .get('/api/v1/auth/me')
      .then((res) => {
        login({ email: res.data.email, tenant_id: res.data.tenant_id, role: res.data.role });
      })
      .catch(() => {
        // 401/403 já é tratado pelo interceptor global (redireciona para /login).
      });
  }, [user, login]);

  const handleLogout = async () => {
    // Cookie é HttpOnly: só o backend consegue removê-lo (Set-Cookie de expiração).
    try {
      await api.post('/api/v1/auth/logout');
    } finally {
      logout();
      router.replace('/login');
    }
  };

  const navItems = [
    { name: 'Mapa Tático', href: '/', icon: Map },
    { name: 'Lideranças', href: '/liderancas', icon: Users },
    { name: 'Projetos de Lei', href: '/projetos-lei', icon: Landmark },
    { name: 'Emendas', href: '/emendas', icon: FileText },
    { name: 'Configurações', href: '/settings', icon: Settings },
  ];

  return (
    // min-h-0 em vez de h-screen: o pai é um flex-col que já pode conter o
    // EnvironmentBadge — h-screen somaria 100vh ao selo e estouraria o viewport.
    <div className="flex flex-1 min-h-0 w-full bg-zinc-950 overflow-hidden">
      {/* Backdrop da gaveta (só existe no mobile, quando aberta) */}
      {isSidebarOpen && (
        <button
          type="button"
          aria-label="Fechar menu"
          onClick={() => setIsSidebarOpen(false)}
          className="fixed inset-0 z-[1200] bg-black/60 backdrop-blur-sm lg:hidden"
        />
      )}

      {/* Tactical Glassmorphism Sidebar — gaveta off-canvas no mobile, fixa no desktop */}
      {/* z-[1300]: o Leaflet empilha panes/controles até ~z-1000 e passaria por
          cima da gaveta, deixando "Pesquisa Pública" e "Desconectar" inacessíveis. */}
      <aside
        className={`fixed inset-y-0 left-0 z-[1300] w-64 max-w-[80vw] flex flex-col backdrop-blur-xl bg-zinc-900/95 lg:bg-zinc-900/40 border-r border-zinc-800/60 shadow-2xl transition-transform duration-300 lg:static lg:z-20 lg:max-w-none lg:translate-x-0 ${
          isSidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="absolute top-0 right-0 bottom-0 w-px bg-gradient-to-b from-transparent via-blue-500/20 to-transparent" />

        {/* Brand Header */}
        <div className="p-6 flex items-center gap-3 border-b border-zinc-800/40">
          <div className="w-10 h-10 shrink-0 bg-purple-500/10 rounded-xl flex items-center justify-center border border-purple-500/20 shadow-[0_0_15px_rgba(59,130,246,0.2)]">
            <Shield className="w-5 h-5 text-purple-400" />
          </div>
          <div className="min-w-0">
            <h2 className="text-white font-bold tracking-tight">DATAPOLIRS</h2>
            <p className="text-[10px] text-zinc-400 uppercase tracking-widest font-semibold">Command Center</p>
          </div>
          <button
            type="button"
            aria-label="Fechar menu"
            onClick={() => setIsSidebarOpen(false)}
            className="ml-auto p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-zinc-800/60 lg:hidden"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 min-h-0 overflow-y-auto px-4 py-6 space-y-2">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.name}
                href={item.href}
                onClick={() => setIsSidebarOpen(false)}
                className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300 ${
                  isActive 
                    ? 'bg-purple-500/10 text-purple-400 border border-purple-500/20 shadow-[0_0_20px_rgba(59,130,246,0.1)]' 
                    : 'text-zinc-400 hover:text-white hover:bg-zinc-800/50 border border-transparent'
                }`}
              >
                <item.icon className={`w-5 h-5 ${isActive ? 'text-purple-400' : 'text-zinc-500'}`} />
                <span className="font-medium text-sm">{item.name}</span>
              </Link>
            );
          })}
          
          {/* External Link to Public Portal — URL absoluta legítima (é outro
              domínio/subdomínio, não a própria API interna). Distinta de
              NEXT_PUBLIC_API_URL de propósito: esta nunca é usada pelo axios
              same-origin, só por este link externo (ADR_026_datapolirs). */}
          <a
            href={process.env.NEXT_PUBLIC_PORTAL_URL || 'http://127.0.0.1:8000'}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-3 px-4 py-3 rounded-xl text-zinc-400 hover:text-white hover:bg-zinc-800/50 border border-transparent transition-all duration-300 mt-4"
          >
            <Globe className="w-5 h-5 text-zinc-500" />
            <span className="font-medium text-sm">Pesquisa Pública</span>
          </a>
        </nav>

        {/* Footer / Logout */}
        <div className="p-4 border-t border-zinc-800/40">
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 w-full px-4 py-3 rounded-xl text-zinc-400 hover:text-red-400 hover:bg-red-500/10 border border-transparent hover:border-red-500/20 transition-all duration-300"
          >
            <LogOut className="w-5 h-5" />
            <span className="font-medium text-sm">Desconectar</span>
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 min-w-0 flex flex-col bg-zinc-950">
        {/* Topbar mobile — único ponto de acesso à navegação quando a gaveta está fechada */}
        <header className="lg:hidden flex items-center gap-3 px-4 py-3 border-b border-zinc-800/60 bg-zinc-900/40 backdrop-blur-xl">
          <button
            type="button"
            aria-label="Abrir menu"
            aria-expanded={isSidebarOpen}
            onClick={() => setIsSidebarOpen(true)}
            className="p-2 -ml-2 rounded-lg text-zinc-300 hover:text-white hover:bg-zinc-800/60"
          >
            <Menu className="w-5 h-5" />
          </button>
          <div className="w-8 h-8 shrink-0 bg-purple-500/10 rounded-lg flex items-center justify-center border border-purple-500/20">
            <Shield className="w-4 h-4 text-purple-400" />
          </div>
          <span className="text-white font-bold tracking-tight text-sm">DATAPOLIRS</span>
        </header>

        <main className="flex-1 min-h-0 relative overflow-hidden">
          {children}
        </main>
      </div>
    </div>
  );
}
