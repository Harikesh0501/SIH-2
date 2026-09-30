"use client";

import React, { useState, useEffect } from "react";
import { Loader2, Download } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { Breadcrumbs } from "@/components/Breadcrumbs";
import { API_BASE_URL, apiGet, apiPost } from "@/lib/api-client";

interface DivisionData {
  division_code: string;
  division_name: string;
  officers_count: number;
  avg_proficiency_pct: number;
}

interface Bottleneck {
  competency_code: string;
  competency_name: string;
  avg_gap: number;
  officers_below_benchmark: number;
}

export default function AdminPage() {
  const { activePersona } = useAuth();
  const [loading, setLoading] = useState(true);
  const [metrics, setMetrics] = useState<any>(null);
  const [divisions, setDivisions] = useState<DivisionData[]>([]);
  const [bottlenecks, setBottlenecks] = useState<Bottleneck[]>([]);

  // Batch allocation
  const [batchTitle, setBatchTitle] = useState("");
  const [batchCapacity, setBatchCapacity] = useState(30);
  const [allocating, setAllocating] = useState(false);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const data = await apiGet<any>("/admin/dashboard");
        if (data?.macro_metrics) {
          setMetrics(data.macro_metrics);
          setDivisions(data.division_matrix?.divisions || []);
          setBottlenecks(data.top_bottlenecks || []);
        } else {
          loadFallback();
        }
      } catch {
        loadFallback();
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [activePersona]);

  function loadFallback() {
    setMetrics({ total_officers: 42, average_proficiency_pct: 61, total_gaps_identified: 87, priority_actions: 12 });
    setDivisions([
      { division_code: "FOD", division_name: "Field Operations Division", officers_count: 15, avg_proficiency_pct: 58 },
      { division_code: "NAD", division_name: "National Accounts Division", officers_count: 10, avg_proficiency_pct: 68 },
      { division_code: "ESD", division_name: "Economic Statistics Division", officers_count: 9, avg_proficiency_pct: 62 },
      { division_code: "SDRD", division_name: "Survey Design & Research", officers_count: 8, avg_proficiency_pct: 55 },
    ]);
    setBottlenecks([
      { competency_code: "STAT-PRICE", competency_name: "Price Statistics & CPI", avg_gap: 1.8, officers_below_benchmark: 28 },
      { competency_code: "TECH-PYST", competency_name: "Python for Statistics", avg_gap: 1.5, officers_below_benchmark: 31 },
      { competency_code: "STAT-NAS", competency_name: "National Accounts (SNA)", avg_gap: 1.2, officers_below_benchmark: 18 },
      { competency_code: "GOV-DPDP", competency_name: "Data Privacy (DPDP Act)", avg_gap: 1.0, officers_below_benchmark: 22 },
    ]);
  }

  const handleAllocate = async () => {
    setAllocating(true);
    try {
      await apiPost("/admin/allocate-batch", { title: batchTitle, capacity: batchCapacity });
    } catch {}
    setAllocating(false);
    setBatchTitle("");
  };

  const handleDownloadReport = async () => {
    try {
      const token = typeof window !== "undefined" ? localStorage.getItem("karmayogi_token") : null;
      const headers: Record<string, string> = {};
      if (token) headers["Authorization"] = `Bearer ${token}`;
      const res = await fetch(`${API_BASE_URL}/reports/ministry-capacity-readiness`, { headers });
      if (res.ok) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "Capacity_Readiness_Report.pdf";
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
      }
    } catch {
      window.print();
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-6 h-6 animate-spin text-zinc-400" />
      </div>
    );
  }

  const currentRole = (activePersona.role || "LEARNER").toUpperCase();
  if (currentRole !== "ADMIN") {
    return (
      <div className="max-w-2xl mx-auto py-16 text-center space-y-4">
        <div className="w-12 h-12 rounded-xl bg-zinc-100 text-zinc-700 flex items-center justify-center font-bold text-xl mx-auto">
          🏛️
        </div>
        <h1 className="text-xl font-bold text-zinc-900">
          Cadre Administration Access Restricted
        </h1>
        <p className="text-sm text-zinc-500 max-w-md mx-auto">
          Ministry-wide TPAC batch allocations and macro workforce analytics are restricted to the Cadre Controlling Authority (Director/DDG).
        </p>
        <div className="pt-2">
          <p className="text-xs text-zinc-400 font-mono mb-4">
            Tip: Switch persona to Alok Mathur (Admin) in the top-right menu to manage national cadre allocations.
          </p>
          <a
            href="/"
            className="px-4 py-2 rounded-lg bg-zinc-900 text-white text-xs font-semibold hover:bg-zinc-800 transition-colors inline-block"
          >
            ← Return to Dashboard
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Breadcrumbs items={[{ label: "Admin" }]} />

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-900">Cadre Analytics</h1>
          <p className="mt-1 text-sm text-zinc-500">Ministry-wide competency overview</p>
        </div>
        <button
          onClick={handleDownloadReport}
          className="px-4 py-2 rounded-md bg-zinc-900 text-white text-sm font-medium hover:bg-zinc-800 transition-colors flex items-center space-x-1.5"
        >
          <Download className="w-4 h-4" />
          <span>Download Report</span>
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: "Total Officers", value: metrics?.total_officers || 0 },
          { label: "Avg Readiness", value: `${metrics?.average_proficiency_pct || 0}%` },
          { label: "Gaps Identified", value: metrics?.total_gaps_identified || 0 },
          { label: "Priority Actions", value: metrics?.priority_actions || 0 },
        ].map((kpi) => (
          <div key={kpi.label} className="border border-zinc-200 rounded-lg p-4">
            <p className="text-xs font-medium text-zinc-500 uppercase tracking-wide">{kpi.label}</p>
            <p className="mt-1 text-2xl font-bold text-zinc-900">{kpi.value}</p>
          </div>
        ))}
      </div>

      {/* Division Comparison */}
      <div className="border border-zinc-200 rounded-lg p-5">
        <h2 className="text-base font-semibold text-zinc-900 mb-4">Division Comparison</h2>
        <div className="space-y-3">
          {divisions.map((div) => (
            <div key={div.division_code} className="flex items-center space-x-4">
              <span className="text-sm font-medium text-zinc-900 w-48">{div.division_name}</span>
              <div className="flex-1 bg-zinc-100 rounded-full h-2">
                <div
                  className="bg-zinc-900 h-2 rounded-full transition-all"
                  style={{ width: `${div.avg_proficiency_pct}%` }}
                />
              </div>
              <span className="text-sm font-mono text-zinc-600 w-12 text-right">{div.avg_proficiency_pct}%</span>
              <span className="text-xs text-zinc-400 w-20 text-right">{div.officers_count} officers</span>
            </div>
          ))}
        </div>
      </div>

      {/* Top Bottlenecks */}
      <div className="border border-zinc-200 rounded-lg p-5">
        <h2 className="text-base font-semibold text-zinc-900 mb-4">Top Competency Bottlenecks</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-zinc-200">
                <th className="text-left py-2 text-xs font-medium text-zinc-500">Code</th>
                <th className="text-left py-2 text-xs font-medium text-zinc-500">Competency</th>
                <th className="text-right py-2 text-xs font-medium text-zinc-500">Avg Gap</th>
                <th className="text-right py-2 text-xs font-medium text-zinc-500">Officers Below</th>
              </tr>
            </thead>
            <tbody>
              {bottlenecks.map((b) => (
                <tr key={b.competency_code} className="border-b border-zinc-100">
                  <td className="py-2 font-mono text-xs text-zinc-500">{b.competency_code}</td>
                  <td className="py-2 text-zinc-900">{b.competency_name}</td>
                  <td className="py-2 text-right font-medium text-zinc-700">{b.avg_gap}</td>
                  <td className="py-2 text-right text-zinc-500">{b.officers_below_benchmark}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Batch Allocation */}
      <div className="border border-zinc-200 rounded-lg p-5">
        <h2 className="text-base font-semibold text-zinc-900 mb-4">TPAC Batch Allocation</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <input
            type="text"
            placeholder="Batch title"
            value={batchTitle}
            onChange={(e) => setBatchTitle(e.target.value)}
            className="px-3 py-2 rounded-md border border-zinc-300 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-900"
          />
          <input
            type="number"
            placeholder="Capacity"
            value={batchCapacity}
            onChange={(e) => setBatchCapacity(parseInt(e.target.value) || 30)}
            className="px-3 py-2 rounded-md border border-zinc-300 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-900"
          />
          <button
            onClick={handleAllocate}
            disabled={allocating || !batchTitle}
            className="px-4 py-2 rounded-md bg-zinc-900 text-white text-sm font-medium hover:bg-zinc-800 disabled:opacity-30 transition-colors"
          >
            {allocating ? "Allocating..." : "Create Batch"}
          </button>
        </div>
      </div>
    </div>
  );
}
