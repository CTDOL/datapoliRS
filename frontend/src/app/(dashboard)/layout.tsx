'use client';

import { useRouter, usePathname } from 'next/navigation';
import Link from 'next/link';
import { useAuthStore } from '@/stores/useAuthStore';
import { Map, Users, Settings, LogOut, Shield, Globe } from 'lucide-react';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const { logout } = useAuthStore();

  const handleLogout = () => {
    logout();
    router.replace('/login');
  };

  const navItems = [
    { name: 'Mapa Tático', href: '/', icon: Map },
    { name: 'Lideranças', href: '/liderancas', icon: Users },
    { name: 'Configurações', href: '/settings', icon: Settings },
  ];

  return (
    <div className="flex h-screen w-full bg-zinc-950 overflow-hidden">
      {/* Tactical Glassmorphism Sidebar */}
      <aside className="w-64 h-full flex flex-col backdrop-blur-xl bg-zinc-900/40 border-r border-zinc-800/60 shadow-2xl z-20 relative">
        <div className="absolute top-0 right-0 bottom-0 w-px bg-gradient-to-b from-transparent via-blue-500/20 to-transparent" />
        
        {/* Brand Header */}
        <div className="p-6 flex items-center gap-3 border-b border-zinc-800/40">
          <div className="w-10 h-10 bg-purple-500/10 rounded-xl flex items-center justify-center border border-purple-500/20 shadow-[0_0_15px_rgba(59,130,246,0.2)]">
            <Shield className="w-5 h-5 text-purple-400" />
          </div>
          <div>
            <h2 className="text-white font-bold tracking-tight">DATAPOLIRS</h2>
            <p className="text-[10px] text-zinc-400 uppercase tracking-widest font-semibold">Command Center</p>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-4 py-6 space-y-2">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.name}
                href={item.href}
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
          
          {/* External Link to Public Portal */}
          <a
            href="http://localhost:8000/"
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
      <main className="flex-1 h-full relative overflow-hidden bg-zinc-950">
        {children}
      </main>
    </div>
  );
}
