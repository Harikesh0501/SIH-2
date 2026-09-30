"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { API_BASE_URL } from "@/lib/api-client";

export interface DemoPersona {
  email: string;
  name: string;
  role: "LEARNER" | "SUPERVISOR" | "TRAINER" | "ADMIN";
  designation: string;
  cadre: "ISS" | "SSS" | "CONTRACTUAL";
  division: string;
  description: string;
}

export const DEMO_PERSONAS: DemoPersona[] = [
  {
    email: "jso.sharma@mospi.gov.in",
    name: "Pooja Sharma",
    role: "LEARNER",
    designation: "Junior Statistical Officer",
    cadre: "SSS",
    division: "Field Operations Division (FOD)",
    description: "NSS Field Surveyor & CAPI Enumerator with gaps in Price Indices & Python"
  },
  {
    email: "ad.verma@mospi.gov.in",
    name: "Rajesh Verma",
    role: "SUPERVISOR",
    designation: "Assistant Director",
    cadre: "ISS",
    division: "National Accounts Division (NAD)",
    description: "Division Head overseeing GDP/GVA compilation with 6 subordinate officers"
  },
  {
    email: "faculty.nssta@nic.in",
    name: "Dr. Sunita Rao",
    role: "TRAINER",
    designation: "Director / Senior Faculty",
    cadre: "ISS",
    division: "NSSTA Greater Noida",
    description: "NSSTA Lead Professor authoring CAT assessments & TPAC residential curricula"
  },
  {
    email: "admin.cadre@mospi.gov.in",
    name: "Alok Mathur",
    role: "ADMIN",
    designation: "Director / Deputy Director General",
    cadre: "ISS",
    division: "Cadre Administration & Policy",
    description: "Cadre Controlling Authority overseeing national workforce heatmaps & TPAC allocations"
  }
];

export interface UserProfile {
  id: number;
  email: string;
  full_name: string;
  role: string;
  designation: string;
  cadre: string;
  division: string;
  organization: string;
  experience_years: number;
  education: string;
  avatar_url?: string;
}

interface AuthContextType {
  currentUser: UserProfile | null;
  token: string | null;
  isLoading: boolean;
  activePersona: DemoPersona;
  switchPersona: (persona: DemoPersona) => Promise<void>;
  login: (token: string, user: UserProfile) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [currentUser, setCurrentUser] = useState<UserProfile | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [activePersona, setActivePersona] = useState<DemoPersona>(DEMO_PERSONAS[0]);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Initial load
  useEffect(() => {
    async function initAuth() {
      const isLoggedOut = localStorage.getItem("karmayogi_logged_out") === "true";
      const storedToken = localStorage.getItem("karmayogi_token");
      const storedPersonaEmail = localStorage.getItem("karmayogi_persona_email");

      if (isLoggedOut || (!storedToken && !storedPersonaEmail)) {
        setIsLoading(false);
        return;
      }

      if (storedPersonaEmail) {
        const found = DEMO_PERSONAS.find((p) => p.email === storedPersonaEmail);
        if (found) setActivePersona(found);
      }

      if (storedToken) {
        setToken(storedToken);
        try {
          const res = await fetch(`${API_BASE_URL}/me`, {
            headers: { Authorization: `Bearer ${storedToken}` }
          });
          if (res.ok) {
            const data = await res.json();
            setCurrentUser(data);
          } else {
            localStorage.removeItem("karmayogi_token");
          }
        } catch (e) {
          console.warn("Backend /me check offline, using local state", e);
        }
      }
      setIsLoading(false);
    }

    initAuth();
  }, []);

  const switchPersona = async (persona: DemoPersona) => {
    setIsLoading(true);
    localStorage.removeItem("karmayogi_logged_out");
    setActivePersona(persona);
    localStorage.setItem("karmayogi_persona_email", persona.email);

    try {
      // Authenticate against backend
      const res = await fetch(`${API_BASE_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: persona.email, password: "Password@123" })
      });

      if (res.ok) {
        const data = await res.json();
        setToken(data.access_token);
        setCurrentUser(data.user);
        localStorage.setItem("karmayogi_token", data.access_token);
      } else {
        // Mock fallback if network blip
        setCurrentUser({
          id: persona.email.includes("sharma") ? 4 : persona.email.includes("verma") ? 3 : persona.email.includes("rao") ? 2 : 1,
          email: persona.email,
          full_name: persona.name,
          role: persona.role,
          designation: persona.designation,
          cadre: persona.cadre,
          division: persona.division,
          organization: "Ministry of Statistics & Programme Implementation (MoSPI)",
          experience_years: 2,
          education: "Master's in Statistics / Economics"
        });
      }
    } catch (err) {
      console.error("Failed to switch persona:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const login = (newToken: string, newUser: UserProfile) => {
    localStorage.removeItem("karmayogi_logged_out");
    setToken(newToken);
    setCurrentUser(newUser);
    localStorage.setItem("karmayogi_token", newToken);
  };

  const logout = () => {
    setToken(null);
    setCurrentUser(null);
    localStorage.removeItem("karmayogi_token");
    localStorage.removeItem("karmayogi_persona_email");
    localStorage.setItem("karmayogi_logged_out", "true");
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
  };

  return (
    <AuthContext.Provider
      value={{
        currentUser,
        token,
        isLoading,
        activePersona,
        switchPersona,
        login,
        logout
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
