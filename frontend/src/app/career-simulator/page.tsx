"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "@/context/AuthContext";
import { apiGet, apiPost } from "@/lib/api-client";
import { Breadcrumbs } from "@/components/Breadcrumbs";
import { CompetencyRadar, RadarDataPoint } from "@/components/dashboard/CompetencyRadar";

const TARGET_ROLES = [
  { value: "SSO", label: "Senior Statistical Officer (SSO)" },
  { value: "AD", label: "Assistant Director (AD)" },
  { value: "DD", label: "Deputy Director (DD)" },
  { value: "DIR", label: "Director" },
];

export default function CareerSimulatorPage() {
  const { currentUser, activePersona } = useAuth();
  const [targetRole, setTargetRole] = useState("AD");
  const [loading, setLoading] = useState(false);
  const [simData, setSimData] = useState<any>(null);

  useEffect(() => {
    async function fetchSimulation() {
      setLoading(true);
      try {
        const res = await apiPost<any>("/competencies/career-simulation", {
          target_role: targetRole,
        });
        setSimData(res);
      } catch {
        setSimData({
          readiness_percentage: targetRole === "SSO" ? 72 : targetRole === "AD" ? 54 : 38,
          projected_gaps: [
            { competency: "Price Statistics & CPI", current: 1, required: 3, gap: 2 },
            { competency: "Python for Statistics", current: 1, required: 3, gap: 2 },
            { competency: "National Accounts (SNA)", current: 2, required: 4, gap: 2 },
          ],
          recommended_pathway_summary: `Complete CPI methodology certification and Python for Official Statistics course to qualify for ${targetRole} promotion.`,
          radar_data: [
            { domain: "Statistical Methods", current: 2.6, target: targetRole === "SSO" ? 3.0 : 3.8, fullMark: 5 },
            { domain: "Computing & Tech", current: 2.1, target: targetRole === "SSO" ? 2.5 : 3.5, fullMark: 5 },
            { domain: "Governance", current: 2.5, target: targetRole === "SSO" ? 2.8 : 3.2, fullMark: 5 },
            { domain: "Leadership", current: 2.8, target: targetRole === "SSO" ? 3.0 : 3.8, fullMark: 5 },
          ],
        });
      } finally {
        setLoading(false);
      }
    }
    fetchSimulation();
  }, [targetRole]);

  const radarData: RadarDataPoint[] = simData?.radar_data || [];
  const readiness = simData?.readiness_percentage || 0;
  const gaps = simData?.projected_gaps || [];
  const summary = simData?.recommended_pathway_summary || "";

  return (
    <div className="space-y-6">
      <Breadcrumbs items={[{ label: "Career Simulator" }]} />

      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-zinc-900">Career Progression Simulator</h1>
          <p className="mt-1 text-sm text-zinc-500">
            Compare your current profile against a target role benchmark
          </p>
        </div>
        <div>
          <label className="block text-xs font-medium text-zinc-500 mb-1">Target Role</label>
          <select
            value={targetRole}
            onChange={(e) => setTargetRole(e.target.value)}
            className="px-3 py-2 rounded-md border border-zinc-300 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-zinc-900"
          >
            {TARGET_ROLES.map((r) => (
              <option key={r.value} value={r.value}>{r.label}</option>
            ))}
          </select>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-20 text-sm text-zinc-400">Loading simulation...</div>
      ) : (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Readiness + Radar */}
            <div className="border border-zinc-200 rounded-lg p-5 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-zinc-500 uppercase tracking-wide font-medium">Promotion Readiness</p>
                  <p className="text-4xl font-bold text-zinc-900 mt-1">{readiness}%</p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-zinc-500">Current</p>
                  <p className="text-sm font-medium text-zinc-900">
                    {currentUser?.designation || activePersona.designation}
                  </p>
                  <p className="text-xs text-zinc-500 mt-1">Target</p>
                  <p className="text-sm font-medium text-zinc-900">
                    {TARGET_ROLES.find((r) => r.value === targetRole)?.label}
                  </p>
                </div>
              </div>
              <div className="w-full bg-zinc-100 rounded-full h-2">
                <div
                  className="bg-zinc-900 h-2 rounded-full transition-all"
                  style={{ width: `${Math.min(100, readiness)}%` }}
                />
              </div>
              <CompetencyRadar data={radarData} />
            </div>

            {/* Projected Gaps */}
            <div className="border border-zinc-200 rounded-lg p-5 space-y-4">
              <h2 className="text-base font-semibold text-zinc-900">Projected Gaps</h2>
              <div className="space-y-3">
                {gaps.map((gap: any, i: number) => (
                  <div key={i} className="border border-zinc-200 rounded-md p-3">
                    <p className="text-sm font-medium text-zinc-900">{gap.competency}</p>
                    <div className="flex items-center justify-between mt-1 text-xs text-zinc-500">
                      <span>Current: L{gap.current}</span>
                      <span>Required: L{gap.required}</span>
                      <span className="font-medium text-zinc-700">Gap: {gap.gap}</span>
                    </div>
                    <div className="mt-2 w-full bg-zinc-100 rounded-full h-1.5">
                      <div
                        className="bg-zinc-900 h-1.5 rounded-full"
                        style={{ width: `${(gap.current / gap.required) * 100}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>

              {summary && (
                <div className="border-t border-zinc-100 pt-4">
                  <p className="text-xs font-medium text-zinc-500 uppercase tracking-wide mb-1">Recommendation</p>
                  <p className="text-sm text-zinc-700 leading-relaxed">{summary}</p>
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
