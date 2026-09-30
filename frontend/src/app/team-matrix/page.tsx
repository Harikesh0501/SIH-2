"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "@/context/AuthContext";
import { apiGet, apiPost } from "@/lib/api-client";
import { Breadcrumbs } from "@/components/Breadcrumbs";

interface Officer {
  id: number;
  full_name: string;
  designation: string;
  cadre: string;
  competencies: Array<{
    code: string;
    name: string;
    current_level: number;
    target_level: number;
  }>;
}

export default function TeamMatrixPage() {
  const { currentUser, activePersona } = useAuth();
  const [loading, setLoading] = useState(true);
  const [officers, setOfficers] = useState<Officer[]>([]);
  const [calibrating, setCalibratingId] = useState<number | null>(null);
  const [calibrationData, setCalibrationData] = useState({ competency_code: "", new_level: 3, justification: "" });

  useEffect(() => {
    async function fetchTeam() {
      setLoading(true);
      try {
        const res = await apiGet<any>("/team/my-subordinates");
        if (res?.subordinates) {
          setOfficers(res.subordinates);
        } else {
          setOfficers(getFallbackOfficers());
        }
      } catch {
        setOfficers(getFallbackOfficers());
      } finally {
        setLoading(false);
      }
    }
    fetchTeam();
  }, [currentUser, activePersona]);

  const handleCalibrate = async (officerId: number) => {
    try {
      await apiPost(`/team/calibrate/${officerId}`, {
        competency_code: calibrationData.competency_code,
        new_level: calibrationData.new_level,
        justification: calibrationData.justification,
      });
      setCalibratingId(null);
      setCalibrationData({ competency_code: "", new_level: 3, justification: "" });
    } catch {
      setCalibratingId(null);
    }
  };

  const currentRole = (currentUser?.role || activePersona.role || "LEARNER").toUpperCase();

  if (currentRole === "LEARNER") {
    return (
      <div className="max-w-2xl mx-auto py-16 text-center space-y-4">
        <div className="w-12 h-12 rounded-xl bg-zinc-100 text-zinc-700 flex items-center justify-center font-bold text-xl mx-auto">
          🔒
        </div>
        <h1 className="text-xl font-bold text-zinc-900">
          Supervisory Access Restricted
        </h1>
        <p className="text-sm text-zinc-500 max-w-md mx-auto">
          The Team Matrix and Subordinate Rating Calibration is accessible to Division Heads (Supervisors) and Cadre Administrators.
        </p>
        <div className="pt-2">
          <p className="text-xs text-zinc-400 font-mono mb-4">
            Tip: Switch persona to Rajesh Verma (Supervisor) or Alok Mathur (Admin) in the top-right menu to manage subordinates.
          </p>
          <a
            href="/"
            className="px-4 py-2 rounded-lg bg-zinc-900 text-white text-xs font-semibold hover:bg-zinc-800 transition-colors inline-block"
          >
            ← Return to Learner Dashboard
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Breadcrumbs items={[{ label: "Team Matrix" }]} />

      <div>
        <h1 className="text-2xl font-bold text-zinc-900">Supervisor Team Matrix</h1>
        <p className="mt-1 text-sm text-zinc-500">
          Review and calibrate subordinate competency levels
        </p>
      </div>

      {loading ? (
        <div className="text-center py-20 text-sm text-zinc-400">Loading team...</div>
      ) : officers.length === 0 ? (
        <div className="text-center py-20 text-sm text-zinc-400">No subordinates found for your role.</div>
      ) : (
        <div className="space-y-4">
          {officers.map((officer) => (
            <div key={officer.id} className="border border-zinc-200 rounded-lg p-5">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 rounded-full bg-zinc-100 text-zinc-700 text-sm font-semibold flex items-center justify-center">
                    {officer.full_name.split(" ").map((n) => n[0]).join("")}
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-zinc-900">{officer.full_name}</p>
                    <p className="text-xs text-zinc-500">{officer.designation} · {officer.cadre}</p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setCalibratingId(calibrating === officer.id ? null : officer.id)}
                  className="px-3 py-1.5 rounded-md border border-zinc-300 text-xs font-medium text-zinc-700 hover:bg-zinc-50 transition-colors"
                >
                  {calibrating === officer.id ? "Cancel" : "Calibrate"}
                </button>
              </div>

              {/* Competency Bars */}
              <div className="space-y-2">
                {(officer.competencies || []).map((comp) => (
                  <div key={comp.code} className="flex items-center space-x-3">
                    <span className="text-xs text-zinc-500 w-40 truncate">{comp.name}</span>
                    <div className="flex-1 bg-zinc-100 rounded-full h-2">
                      <div
                        className="bg-zinc-900 h-2 rounded-full transition-all"
                        style={{ width: `${(comp.current_level / comp.target_level) * 100}%` }}
                      />
                    </div>
                    <span className="text-xs font-mono text-zinc-600 w-16 text-right">
                      L{comp.current_level}/L{comp.target_level}
                    </span>
                  </div>
                ))}
              </div>

              {/* Calibration Form */}
              {calibrating === officer.id && (
                <div className="mt-4 border-t border-zinc-100 pt-4 space-y-3">
                  <p className="text-xs font-medium text-zinc-700">Calibrate a competency level</p>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <select
                      value={calibrationData.competency_code}
                      onChange={(e) => setCalibrationData({ ...calibrationData, competency_code: e.target.value })}
                      className="px-3 py-2 rounded-md border border-zinc-300 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-zinc-900"
                    >
                      <option value="">Select competency</option>
                      {(officer.competencies || []).map((c) => (
                        <option key={c.code} value={c.code}>{c.name}</option>
                      ))}
                    </select>
                    <select
                      value={calibrationData.new_level}
                      onChange={(e) => setCalibrationData({ ...calibrationData, new_level: parseInt(e.target.value) })}
                      className="px-3 py-2 rounded-md border border-zinc-300 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-zinc-900"
                    >
                      {[1, 2, 3, 4, 5].map((l) => (
                        <option key={l} value={l}>Level {l}</option>
                      ))}
                    </select>
                    <input
                      type="text"
                      placeholder="Justification"
                      value={calibrationData.justification}
                      onChange={(e) => setCalibrationData({ ...calibrationData, justification: e.target.value })}
                      className="px-3 py-2 rounded-md border border-zinc-300 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-900"
                    />
                  </div>
                  <button
                    type="button"
                    onClick={() => handleCalibrate(officer.id)}
                    disabled={!calibrationData.competency_code || !calibrationData.justification}
                    className="px-4 py-2 rounded-md bg-zinc-900 text-white text-sm font-medium hover:bg-zinc-800 disabled:opacity-30 transition-colors"
                  >
                    Submit Calibration
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function getFallbackOfficers(): Officer[] {
  return [
    {
      id: 4,
      full_name: "Pooja Sharma",
      designation: "Junior Statistical Officer",
      cadre: "SSS",
      competencies: [
        { code: "STAT-SURV", name: "Survey Design", current_level: 2, target_level: 3 },
        { code: "STAT-PRICE", name: "Price Statistics", current_level: 1, target_level: 3 },
        { code: "TECH-PYST", name: "Python", current_level: 1, target_level: 2 },
        { code: "STAT-NAS", name: "National Accounts", current_level: 2, target_level: 3 },
      ],
    },
    {
      id: 6,
      full_name: "Anjali Mehra",
      designation: "Statistical Investigator",
      cadre: "SSS",
      competencies: [
        { code: "STAT-SURV", name: "Survey Design", current_level: 3, target_level: 3 },
        { code: "STAT-PRICE", name: "Price Statistics", current_level: 2, target_level: 3 },
        { code: "TECH-DBQL", name: "Database & SQL", current_level: 2, target_level: 2 },
      ],
    },
    {
      id: 7,
      full_name: "Vikram Singh",
      designation: "Statistical Investigator",
      cadre: "SSS",
      competencies: [
        { code: "STAT-SURV", name: "Survey Design", current_level: 2, target_level: 3 },
        { code: "STAT-LABOUR", name: "Labour Statistics", current_level: 3, target_level: 3 },
        { code: "TECH-PYST", name: "Python", current_level: 2, target_level: 2 },
      ],
    },
  ];
}
