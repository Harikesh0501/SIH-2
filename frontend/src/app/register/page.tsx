"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Mail, Lock, User, Briefcase, Building, ArrowRight, CheckCircle2 } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { API_BASE_URL } from "@/lib/api-client";

export default function RegisterPage() {
  const router = useRouter();
  const { login } = useAuth();

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [cadre, setCadre] = useState("SSS");
  const [designation, setDesignation] = useState("Junior Statistical Officer");
  const [division, setDivision] = useState("FOD");
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg("");
    setSuccessMsg("");

    if (password !== confirmPassword) {
      setErrorMsg("Passwords do not match.");
      return;
    }

    if (password.length < 6) {
      setErrorMsg("Password must be at least 6 characters long.");
      return;
    }

    setIsLoading(true);

    try {
      const res = await fetch(`${API_BASE_URL}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: email.trim(),
          password,
          full_name: fullName.trim(),
          cadre,
          designation,
          division,
          organization: "Ministry of Statistics & Programme Implementation (MoSPI)",
          experience_years: 1,
          role: "LEARNER",
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Registration failed. Please check your details.");
      }

      const data = await res.json();
      setSuccessMsg("Account created successfully! Redirecting...");
      login(data.access_token, data.user);

      setTimeout(() => {
        router.push("/onboarding");
      }, 1000);
    } catch (err: any) {
      setErrorMsg(err.message || "Registration failed.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-[85vh] flex items-center justify-center py-12 px-4 sm:px-6">
      <div className="w-full max-w-lg space-y-6">
        {/* Header */}
        <div className="text-center">
          <div className="w-12 h-12 rounded-lg bg-zinc-900 text-white flex items-center justify-center font-bold text-xl mx-auto shadow-sm">
            सं
          </div>
          <h1 className="mt-4 text-2xl font-bold text-zinc-900 tracking-tight">
            Create Official Account
          </h1>
          <p className="mt-1 text-sm text-zinc-500">
            Karmayogi Sankhyiki · MoSPI Officer Registration
          </p>
        </div>

        {/* Card */}
        <div className="bg-white border border-zinc-200 rounded-xl p-6 sm:p-8 shadow-sm">
          {errorMsg && (
            <div className="mb-5 p-3.5 rounded-lg bg-zinc-100 border border-zinc-300 text-sm text-zinc-800">
              {errorMsg}
            </div>
          )}

          {successMsg && (
            <div className="mb-5 p-3.5 rounded-lg bg-zinc-900 text-white text-sm flex items-center space-x-2">
              <CheckCircle2 className="w-4 h-4 text-zinc-300 shrink-0" />
              <span>{successMsg}</span>
            </div>
          )}

          <form onSubmit={handleRegister} className="space-y-4">
            {/* Full Name */}
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-700 mb-1.5">
                Full Name
              </label>
              <div className="relative">
                <User className="w-4 h-4 text-zinc-400 absolute left-3 top-3" />
                <input
                  type="text"
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="e.g. Ramesh Kumar"
                  className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-zinc-300 text-sm text-zinc-900 placeholder:text-zinc-400 focus:outline-none focus:ring-2 focus:ring-zinc-900 focus:border-transparent transition-all"
                />
              </div>
            </div>

            {/* Official Email */}
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-700 mb-1.5">
                Official Email
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-zinc-400 absolute left-3 top-3" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="officer@mospi.gov.in"
                  className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-zinc-300 text-sm text-zinc-900 placeholder:text-zinc-400 focus:outline-none focus:ring-2 focus:ring-zinc-900 focus:border-transparent transition-all"
                />
              </div>
            </div>

            {/* Cadre & Division Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-700 mb-1.5">
                  Cadre
                </label>
                <div className="relative">
                  <Briefcase className="w-4 h-4 text-zinc-400 absolute left-3 top-3 pointer-events-none" />
                  <select
                    value={cadre}
                    onChange={(e) => setCadre(e.target.value)}
                    className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-zinc-300 text-sm text-zinc-900 bg-white focus:outline-none focus:ring-2 focus:ring-zinc-900 focus:border-transparent transition-all appearance-none"
                  >
                    <option value="SSS">Subordinate Statistical Service (SSS)</option>
                    <option value="ISS">Indian Statistical Service (ISS)</option>
                    <option value="FACULTY">NSSTA Faculty / Training Cadre</option>
                    <option value="NON_CADRE">Non-Cadre / MoSPI Technical</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-700 mb-1.5">
                  Division
                </label>
                <div className="relative">
                  <Building className="w-4 h-4 text-zinc-400 absolute left-3 top-3 pointer-events-none" />
                  <select
                    value={division}
                    onChange={(e) => setDivision(e.target.value)}
                    className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-zinc-300 text-sm text-zinc-900 bg-white focus:outline-none focus:ring-2 focus:ring-zinc-900 focus:border-transparent transition-all appearance-none"
                  >
                    <option value="FOD">FOD (Field Operations)</option>
                    <option value="NAD">NAD (National Accounts)</option>
                    <option value="ESD">ESD (Economic Statistics)</option>
                    <option value="SDRD">SDRD (Survey Design & Research)</option>
                    <option value="NSSTA">NSSTA (Training Academy)</option>
                    <option value="DIID">DIID (Data & IT)</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Designation */}
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-700 mb-1.5">
                Designation
              </label>
              <input
                type="text"
                required
                value={designation}
                onChange={(e) => setDesignation(e.target.value)}
                placeholder="e.g. Junior Statistical Officer / Assistant Director"
                className="w-full px-4 py-2.5 rounded-lg border border-zinc-300 text-sm text-zinc-900 placeholder:text-zinc-400 focus:outline-none focus:ring-2 focus:ring-zinc-900 focus:border-transparent transition-all"
              />
            </div>

            {/* Password & Confirm Password */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-700 mb-1.5">
                  Password
                </label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-zinc-400 absolute left-3 top-3" />
                  <input
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-zinc-300 text-sm text-zinc-900 placeholder:text-zinc-400 focus:outline-none focus:ring-2 focus:ring-zinc-900 focus:border-transparent transition-all"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-700 mb-1.5">
                  Confirm Password
                </label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-zinc-400 absolute left-3 top-3" />
                  <input
                    type="password"
                    required
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-zinc-300 text-sm text-zinc-900 placeholder:text-zinc-400 focus:outline-none focus:ring-2 focus:ring-zinc-900 focus:border-transparent transition-all"
                  />
                </div>
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3 rounded-lg bg-zinc-900 text-white text-sm font-semibold hover:bg-zinc-800 transition-all disabled:opacity-50 flex items-center justify-center space-x-2 shadow-sm"
            >
              <span>{isLoading ? "Creating Account..." : "Complete Registration"}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          <div className="mt-6 pt-5 border-t border-zinc-200 text-center">
            <p className="text-sm text-zinc-500">
              Already have an account?{" "}
              <Link href="/login" className="font-semibold text-zinc-900 hover:underline">
                Sign In here →
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
