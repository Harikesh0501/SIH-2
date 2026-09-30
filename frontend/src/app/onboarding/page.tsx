"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { ChevronRight, ChevronLeft } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { API_BASE_URL } from "@/lib/api-client";
import { Breadcrumbs } from "@/components/Breadcrumbs";

const COMPETENCIES = [
  { code: "STAT-SURV", name: "Survey Design & Sampling", domain: "Statistical" },
  { code: "STAT-NAS", name: "National Accounts (SNA 2008)", domain: "Statistical" },
  { code: "STAT-PRICE", name: "Price Statistics & CPI", domain: "Statistical" },
  { code: "STAT-LABOUR", name: "Labour Force & Employment (PLFS)", domain: "Statistical" },
  { code: "STAT-DQAF", name: "Data Quality Framework (DQAF)", domain: "Statistical" },
  { code: "TECH-PYST", name: "Python for Statistics", domain: "Technical" },
  { code: "TECH-RSTA", name: "R Programming", domain: "Technical" },
  { code: "TECH-DBQL", name: "Database & SQL", domain: "Technical" },
  { code: "GOV-DPDP", name: "Data Privacy (DPDP Act)", domain: "Governance" },
  { code: "GOV-CYBER", name: "Cybersecurity Protocols", domain: "Governance" },
  { code: "BEH-ETHIC", name: "Statistical Ethics", domain: "Behavioural" },
  { code: "BEH-LEAD", name: "Leadership & Communication", domain: "Behavioural" },
];

const DIVISIONS = [
  "Field Operations Division (FOD)",
  "National Accounts Division (NAD)",
  "Economic Statistics Division (ESD)",
  "Survey Design & Research Division (SDRD)",
  "Social Statistics Division (SSD)",
  "NSSTA Greater Noida",
];

export default function OnboardingPage() {
  const router = useRouter();
  const { currentUser, token } = useAuth();
  const [step, setStep] = useState(1);
  const [cadre, setCadre] = useState("SSS");
  const [division, setDivision] = useState(DIVISIONS[0]);
  const [levels, setLevels] = useState<Record<string, number>>(
    Object.fromEntries(COMPETENCIES.map((c) => [c.code, 2]))
  );
  const [submitting, setSubmitting] = useState(false);

  const updateLevel = (code: string, level: number) => {
    setLevels((prev) => ({ ...prev, [code]: level }));
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      await fetch(`${API_BASE_URL}/profile/onboarding`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ cadre, division, competency_levels: levels }),
      });
      router.push("/");
    } catch {
      router.push("/");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto py-6 space-y-6">
      <Breadcrumbs items={[{ label: "Onboarding" }]} />

      <div>
        <h1 className="text-2xl font-bold text-zinc-900">Competency Onboarding</h1>
        <p className="mt-1 text-sm text-zinc-500">Step {step} of 3</p>
      </div>

      {/* Progress */}
      <div className="flex space-x-2">
        {[1, 2, 3].map((s) => (
          <div
            key={s}
            className={`h-1.5 flex-1 rounded-full ${s <= step ? "bg-zinc-900" : "bg-zinc-200"}`}
          />
        ))}
      </div>

      {/* Step 1: Cadre */}
      {step === 1 && (
        <div className="border border-zinc-200 rounded-lg p-6 space-y-4">
          <h2 className="text-base font-semibold text-zinc-900">Select Cadre</h2>
          <div className="space-y-2">
            {[
              { value: "SSS", label: "SSS — Subordinate Statistical Service" },
              { value: "ISS", label: "ISS — Indian Statistical Service" },
            ].map((opt) => (
              <label
                key={opt.value}
                className={`flex items-center p-3 rounded-md border cursor-pointer transition-colors ${
                  cadre === opt.value
                    ? "border-zinc-900 bg-zinc-50"
                    : "border-zinc-200 hover:border-zinc-400"
                }`}
              >
                <input
                  type="radio"
                  name="cadre"
                  value={opt.value}
                  checked={cadre === opt.value}
                  onChange={() => setCadre(opt.value)}
                  className="mr-3 accent-zinc-900"
                />
                <span className="text-sm font-medium text-zinc-900">{opt.label}</span>
              </label>
            ))}
          </div>
        </div>
      )}

      {/* Step 2: Division */}
      {step === 2 && (
        <div className="border border-zinc-200 rounded-lg p-6 space-y-4">
          <h2 className="text-base font-semibold text-zinc-900">Select Division</h2>
          <div className="space-y-2">
            {DIVISIONS.map((div) => (
              <label
                key={div}
                className={`flex items-center p-3 rounded-md border cursor-pointer transition-colors ${
                  division === div
                    ? "border-zinc-900 bg-zinc-50"
                    : "border-zinc-200 hover:border-zinc-400"
                }`}
              >
                <input
                  type="radio"
                  name="division"
                  value={div}
                  checked={division === div}
                  onChange={() => setDivision(div)}
                  className="mr-3 accent-zinc-900"
                />
                <span className="text-sm font-medium text-zinc-900">{div}</span>
              </label>
            ))}
          </div>
        </div>
      )}

      {/* Step 3: Self-Assessment */}
      {step === 3 && (
        <div className="border border-zinc-200 rounded-lg p-6 space-y-4">
          <h2 className="text-base font-semibold text-zinc-900">Self-Assess Competencies</h2>
          <p className="text-xs text-zinc-500">Rate each competency from 1 (Beginner) to 5 (Expert)</p>
          <div className="space-y-3">
            {COMPETENCIES.map((comp) => (
              <div key={comp.code} className="flex items-center justify-between py-2 border-b border-zinc-100 last:border-0">
                <div className="flex-1 min-w-0 mr-4">
                  <p className="text-sm font-medium text-zinc-900">{comp.name}</p>
                  <p className="text-xs text-zinc-400">{comp.domain}</p>
                </div>
                <div className="flex space-x-1">
                  {[1, 2, 3, 4, 5].map((lvl) => (
                    <button
                      key={lvl}
                      type="button"
                      onClick={() => updateLevel(comp.code, lvl)}
                      className={`w-8 h-8 rounded-md text-xs font-semibold transition-colors ${
                        levels[comp.code] === lvl
                          ? "bg-zinc-900 text-white"
                          : "bg-zinc-100 text-zinc-600 hover:bg-zinc-200"
                      }`}
                    >
                      {lvl}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Navigation */}
      <div className="flex justify-between">
        <button
          type="button"
          onClick={() => setStep(Math.max(1, step - 1))}
          disabled={step === 1}
          className="px-4 py-2.5 rounded-md border border-zinc-300 text-zinc-700 text-sm font-medium hover:bg-zinc-50 disabled:opacity-30 transition-colors flex items-center space-x-1"
        >
          <ChevronLeft className="w-4 h-4" />
          <span>Back</span>
        </button>

        {step < 3 ? (
          <button
            type="button"
            onClick={() => setStep(step + 1)}
            className="px-4 py-2.5 rounded-md bg-zinc-900 text-white text-sm font-medium hover:bg-zinc-800 transition-colors flex items-center space-x-1"
          >
            <span>Next</span>
            <ChevronRight className="w-4 h-4" />
          </button>
        ) : (
          <button
            type="button"
            onClick={handleSubmit}
            disabled={submitting}
            className="px-6 py-2.5 rounded-md bg-zinc-900 text-white text-sm font-medium hover:bg-zinc-800 disabled:opacity-50 transition-colors"
          >
            {submitting ? "Saving..." : "Complete Onboarding"}
          </button>
        )}
      </div>
    </div>
  );
}
