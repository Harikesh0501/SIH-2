"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Menu, X, ChevronDown, LogOut, Shield } from "lucide-react";
import { useAuth, DEMO_PERSONAS, DemoPersona } from "@/context/AuthContext";

export function Header() {
  const pathname = usePathname();
  const { currentUser, activePersona, switchPersona, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const [personaOpen, setPersonaOpen] = useState(false);

  const currentRole = (currentUser?.role || activePersona.role || "LEARNER").toUpperCase();

  // Role-specific navigation links
  const getNavLinks = (role: string) => {
    switch (role) {
      case "SUPERVISOR":
        return [
          { href: "/", label: "Team Dashboard", exact: true },
          { href: "/team-matrix", label: "Team Matrix" },
          { href: "/chat", label: "AI Tutor" },
          { href: "/passport", label: "Skill Passport" },
        ];
      case "TRAINER":
        return [
          { href: "/", label: "Faculty Hub", exact: true },
          { href: "/assessments", label: "Author Assessments" },
          { href: "/chat", label: "AI Tutor" },
          { href: "/passport", label: "Skill Passport" },
        ];
      case "ADMIN":
        return [
          { href: "/", label: "Cadre Analytics", exact: true },
          { href: "/admin", label: "TPAC Allocation" },
          { href: "/team-matrix", label: "Division Matrix" },
          { href: "/chat", label: "AI Tutor" },
          { href: "/passport", label: "Skill Passport" },
        ];
      case "LEARNER":
      default:
        return [
          { href: "/", label: "Dashboard", exact: true },
          { href: "/career-simulator", label: "Career Simulator" },
          { href: "/assessments", label: "Assessments" },
          { href: "/chat", label: "AI Tutor" },
          { href: "/passport", label: "Skill Passport" },
        ];
    }
  };

  const navLinks = getNavLinks(currentRole);

  const handleSelectPersona = async (persona: DemoPersona) => {
    setPersonaOpen(false);
    await switchPersona(persona);
  };

  return (
    <header className="sticky top-0 z-50 w-full bg-white border-b border-zinc-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-14 items-center">
          {/* Logo & Platform Name */}
          <div className="flex items-center space-x-3">
            <Link href="/" className="flex items-center space-x-2.5">
              <div className="w-8 h-8 rounded-md bg-zinc-900 text-white flex items-center justify-center font-bold text-sm">
                सं
              </div>
              <span className="font-semibold text-sm text-zinc-900 hidden sm:block">
                Karmayogi Sankhyiki
              </span>
            </Link>

            {/* Current Role Badge */}
            <span className="text-[11px] font-mono px-2 py-0.5 rounded border border-zinc-300 bg-zinc-100 text-zinc-700 uppercase tracking-wider font-semibold">
              {currentRole}
            </span>
          </div>

          {/* Desktop Nav - Strictly Filtered By Role */}
          <nav className="hidden lg:flex items-center space-x-1">
            {navLinks.map((link) => {
              const isActive = link.exact
                ? pathname === link.href
                : pathname.startsWith(link.href);
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-zinc-900 text-white"
                      : "text-zinc-600 hover:text-zinc-900 hover:bg-zinc-100"
                  }`}
                >
                  {link.label}
                </Link>
              );
            })}
          </nav>

          {/* Right: User Menu & Persona Switcher */}
          <div className="flex items-center space-x-3">
            <div className="relative">
              <button
                type="button"
                onClick={() => setPersonaOpen(!personaOpen)}
                className="flex items-center space-x-2 px-2.5 py-1.5 rounded-lg border border-zinc-200 hover:border-zinc-300 hover:bg-zinc-50 transition-all"
              >
                <div className="w-7 h-7 rounded-full bg-zinc-900 text-white text-xs font-semibold flex items-center justify-center">
                  {activePersona.name.split(" ").map((n) => n[0]).join("")}
                </div>
                <div className="text-left hidden sm:block">
                  <p className="text-xs font-semibold text-zinc-900 leading-tight">
                    {activePersona.name}
                  </p>
                  <p className="text-[10px] text-zinc-500 font-mono">
                    {currentRole}
                  </p>
                </div>
                <ChevronDown className="w-4 h-4 text-zinc-400" />
              </button>

              {personaOpen && (
                <>
                  <div className="fixed inset-0 z-40" onClick={() => setPersonaOpen(false)} />
                  <div className="absolute right-0 mt-1 w-80 bg-white border border-zinc-200 rounded-xl shadow-xl py-1 z-50">
                    <div className="px-3.5 py-2.5 border-b border-zinc-100">
                      <p className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">
                        Switch MoSPI Role / Persona
                      </p>
                    </div>
                    <div className="divide-y divide-zinc-100">
                      {DEMO_PERSONAS.map((persona) => {
                        const selected = activePersona.email === persona.email;
                        return (
                          <button
                            key={persona.email}
                            onClick={() => handleSelectPersona(persona)}
                            className={`w-full text-left px-3.5 py-3 flex items-start space-x-3 hover:bg-zinc-50 transition-colors ${
                              selected ? "bg-zinc-50" : ""
                            }`}
                          >
                            <div className="w-8 h-8 rounded-full bg-zinc-900 text-white text-xs font-semibold flex items-center justify-center shrink-0 mt-0.5">
                              {persona.name.split(" ").map((n) => n[0]).join("")}
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center justify-between">
                                <p className="text-sm font-semibold text-zinc-900">{persona.name}</p>
                                <span className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-zinc-100 border border-zinc-200 text-zinc-700">
                                  {persona.role}
                                </span>
                              </div>
                              <p className="text-xs text-zinc-600 mt-0.5 truncate">
                                {persona.designation} · {persona.cadre}
                              </p>
                              <p className="text-[11px] text-zinc-400 truncate mt-0.5">
                                {persona.division}
                              </p>
                            </div>
                            {selected && (
                              <div className="w-2 h-2 rounded-full bg-zinc-900 mt-2 shrink-0" />
                            )}
                          </button>
                        );
                      })}
                    </div>
                    <div className="border-t border-zinc-100 p-1.5">
                      <button
                        onClick={() => { setPersonaOpen(false); logout(); }}
                        className="w-full text-left px-3 py-2 flex items-center space-x-2 text-xs font-medium text-zinc-600 hover:text-zinc-900 hover:bg-zinc-100 rounded-md transition-colors"
                      >
                        <LogOut className="w-4 h-4" />
                        <span>Sign out / Return to Login</span>
                      </button>
                    </div>
                  </div>
                </>
              )}
            </div>

            {/* Mobile menu button */}
            <button
              type="button"
              onClick={() => setMenuOpen(!menuOpen)}
              className="lg:hidden p-1.5 rounded-md hover:bg-zinc-100"
            >
              {menuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Nav */}
      {menuOpen && (
        <div className="lg:hidden border-t border-zinc-100 bg-white pb-3">
          <div className="px-4 pt-2 space-y-1">
            {navLinks.map((link) => {
              const isActive = link.exact
                ? pathname === link.href
                : pathname.startsWith(link.href);
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  onClick={() => setMenuOpen(false)}
                  className={`block px-3 py-2 rounded-md text-sm font-medium ${
                    isActive
                      ? "bg-zinc-900 text-white"
                      : "text-zinc-600 hover:bg-zinc-100"
                  }`}
                >
                  {link.label}
                </Link>
              );
            })}
          </div>
        </div>
      )}
    </header>
  );
}
