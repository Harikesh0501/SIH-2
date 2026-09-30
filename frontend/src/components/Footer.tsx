import React from "react";
import Link from "next/link";

export function Footer() {
  return (
    <footer className="border-t border-zinc-200 bg-zinc-50 py-8 mt-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col sm:flex-row justify-between items-center space-y-3 sm:space-y-0">
          <div className="flex items-center space-x-2">
            <div className="w-6 h-6 rounded bg-zinc-900 text-white flex items-center justify-center font-bold text-xs">
              सं
            </div>
            <span className="text-sm font-semibold text-zinc-700">Karmayogi Sankhyiki</span>
          </div>
          <div className="flex items-center space-x-6 text-xs text-zinc-500">
            <span>MoSPI</span>
            <span>NSSTA</span>
            <Link href="/verify" className="hover:text-zinc-900 transition-colors">
              Verify Credentials
            </Link>
          </div>
          <p className="text-xs text-zinc-400">
            © 2026 Ministry of Statistics & Programme Implementation
          </p>
        </div>
      </div>
    </footer>
  );
}
