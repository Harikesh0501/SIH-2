"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Mail, Lock, ArrowRight, UserPlus, LogIn } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { API_BASE_URL } from "@/lib/api-client";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMsg("");

    try {
      const res = await fetch(`${API_BASE_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim(), password }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Invalid official email or password.");
      }

      const data = await res.json();
      login(data.access_token, data.user);
      router.push("/");
    } catch (err: any) {
      setErrorMsg(err.message || "Login failed");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-[85vh] flex items-center justify-center py-12 px-4 sm:px-6">
      <div className="w-full max-w-md space-y-6">
        {/* Header */}
        <div className="text-center">
          <div className="w-12 h-12 rounded-lg bg-zinc-900 text-white flex items-center justify-center font-bold text-xl mx-auto shadow-sm">
            सं
          </div>
          <h1 className="mt-4 text-2xl font-bold text-zinc-900 tracking-tight">
            Karmayogi Sankhyiki
          </h1>
          <p className="mt-1 text-sm text-zinc-500">
            MoSPI Competency & Learning Platform
          </p>
        </div>

        {/* Form Card */}
        <div className="bg-white border border-zinc-200 rounded-xl p-6 sm:p-8 shadow-sm">
          {/* Navigation Tabs */}
          <div className="flex mb-6 border-b border-zinc-200">
            <button
              type="button"
              className="flex-1 pb-3 text-sm font-semibold border-b-2 border-zinc-900 text-zinc-900 flex items-center justify-center space-x-2"
            >
              <LogIn className="w-4 h-4" />
              <span>Sign In</span>
            </button>
            <Link
              href="/register"
              className="flex-1 pb-3 text-sm font-medium border-b-2 border-transparent text-zinc-400 hover:text-zinc-700 flex items-center justify-center space-x-2 transition-colors"
            >
              <UserPlus className="w-4 h-4" />
              <span>Register</span>
            </Link>
          </div>

          {errorMsg && (
            <div className="mb-4 p-3 rounded-lg bg-zinc-100 border border-zinc-300 text-sm text-zinc-800">
              {errorMsg}
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-700 mb-1.5">
                Official Email
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-zinc-400 absolute left-3 top-3" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  placeholder="officer@mospi.gov.in"
                  className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-zinc-300 text-sm text-zinc-900 placeholder:text-zinc-400 focus:outline-none focus:ring-2 focus:ring-zinc-900 focus:border-transparent transition-all"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-700 mb-1.5">
                Password
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-zinc-400 absolute left-3 top-3" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  placeholder="••••••••"
                  className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-zinc-300 text-sm text-zinc-900 placeholder:text-zinc-400 focus:outline-none focus:ring-2 focus:ring-zinc-900 focus:border-transparent transition-all"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-2.5 rounded-lg bg-zinc-900 text-white text-sm font-semibold hover:bg-zinc-800 transition-all disabled:opacity-50 flex items-center justify-center space-x-2 shadow-sm"
            >
              <span>{isLoading ? "Signing in..." : "Sign In"}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          <div className="mt-5 text-center">
            <p className="text-xs text-zinc-500">
              New MoSPI Officer?{" "}
              <Link href="/register" className="font-semibold text-zinc-900 hover:underline">
                Register here →
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
