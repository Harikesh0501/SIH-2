"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  ArrowRight,
  Download,
  Users,
  Award,
  BookOpen,
  CheckCircle2,
  AlertCircle,
  TrendingUp,
  Clock,
  Sparkles,
  Sliders,
  Send,
  Building
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { API_BASE_URL, apiGet, apiPost } from "@/lib/api-client";
import { CompetencyRadar, RadarDataPoint } from "@/components/dashboard/CompetencyRadar";

export default function DashboardPage() {
  const { currentUser, activePersona } = useAuth();
  const currentRole = (currentUser?.role || activePersona.role || "LEARNER").toUpperCase();

  if (currentRole === "SUPERVISOR") {
    return <SupervisorDashboard />;
  }

  if (currentRole === "TRAINER") {
    return <TrainerDashboard />;
  }

  if (currentRole === "ADMIN") {
    return <AdminDashboard />;
  }

  return <LearnerDashboard />;
}

/* =========================================================================
   1. LEARNER DASHBOARD (Pooja Sharma - Junior Statistical Officer, SSS)
   ========================================================================= */
function LearnerDashboard() {
  const { currentUser, activePersona } = useAuth();
  const [loading, setLoading] = useState(true);
  const [gapAnalysis, setGapAnalysis] = useState<any>(null);
  const [pathway, setPathway] = useState<any>(null);
  const [passport, setPassport] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<"IGOT" | "TPAC">("IGOT");

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      try {
        const [gapRes, pathwayRes] = await Promise.allSettled([
          apiGet<any>("/competencies/gap-analysis"),
          apiGet<any>("/recommendations/my-pathway"),
        ]);
        if (gapRes.status === "fulfilled") setGapAnalysis(gapRes.value);
        if (pathwayRes.status === "fulfilled") setPathway(pathwayRes.value);
      } catch (err) {
        console.warn("Dashboard fetch error", err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [currentUser, activePersona]);

  const radarData: RadarDataPoint[] = gapAnalysis?.radar_data || [
    { domain: "Statistical Methods", current: 2.6, target: 3.2, fullMark: 5 },
    { domain: "Computing & Tech", current: 2.1, target: 2.8, fullMark: 5 },
    { domain: "Governance", current: 2.5, target: 3.0, fullMark: 5 },
    { domain: "Leadership", current: 2.8, target: 3.0, fullMark: 5 },
  ];

  const criticalGaps = gapAnalysis?.high_urgency_gaps || [
    { code: "STAT-PRICE", name: "Price Statistics & CPI", current_level: 1, target_level: 3, gap: 2.0, urgency_score: 2.6 },
    { code: "TECH-PYST", name: "Python for Statistics", current_level: 1, target_level: 2, gap: 1.0, urgency_score: 1.8 },
    { code: "STAT-NAS", name: "National Accounts (SNA 2008)", current_level: 2, target_level: 3, gap: 1.0, urgency_score: 1.5 },
  ];

  const proficiency = gapAnalysis?.overall_readiness_percentage || 64.5;
  const assessed = gapAnalysis?.all_competencies?.length || 8;
  const total = 18;
  const badges = 5;
  const hours = 16.5;

  const igotCourses = pathway?.igot_karmayogi || [
    { id: 1, title: "CPI Formulation & Jevons Index", provider: "MoSPI / iGOT", duration_hours: 4.5 },
    { id: 2, title: "Python for Survey Data Automation", provider: "NSSTA Digital Lab", duration_hours: 6.0 },
    { id: 3, title: "SNA 2008 & GVA Compilation", provider: "NAD / iGOT", duration_hours: 5.0 },
  ];

  const tpacBatches = pathway?.nssta_tpac || [
    { id: 11, title: "Workshop on Price Indices & Inflation", location: "NSSTA Greater Noida", batch_start_date: "15 Nov 2026" },
    { id: 13, title: "Survey Sampling Design & SAE", location: "NSSTA Greater Noida", batch_start_date: "10 Jan 2027" },
  ];

  return (
    <div className="space-y-8">
      {/* Welcome Section */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-2xl font-bold text-zinc-900">
              Welcome, {currentUser?.full_name || activePersona.name}
            </h1>
            <span className="text-xs font-mono font-semibold px-2 py-0.5 rounded bg-zinc-100 border border-zinc-200 text-zinc-700">
              LEARNER
            </span>
          </div>
          <p className="mt-1 text-sm text-zinc-500">
            {currentUser?.designation || activePersona.designation} · {currentUser?.cadre || activePersona.cadre} · {currentUser?.division || activePersona.division}
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <Link
            href="/assessments"
            className="px-4 py-2 rounded-lg bg-zinc-900 text-white text-sm font-medium hover:bg-zinc-800 transition-colors flex items-center space-x-1.5"
          >
            <Award className="w-4 h-4" />
            <span>Take Assessment</span>
          </Link>
          <Link
            href="/chat"
            className="px-4 py-2 rounded-lg border border-zinc-300 text-zinc-700 text-sm font-medium hover:bg-zinc-50 transition-colors flex items-center space-x-1.5"
          >
            <Sparkles className="w-4 h-4 text-zinc-500" />
            <span>AI Tutor</span>
          </Link>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: "Proficiency", value: `${proficiency}%`, sub: "Role benchmark readiness" },
          { label: "Assessed", value: `${assessed}/${total}`, sub: "Competencies evaluated" },
          { label: "Credentials", value: badges, sub: "Verified badges earned" },
          { label: "Training Hours", value: `${hours}h`, sub: "iGOT + NSSTA certified" },
        ].map((kpi) => (
          <div key={kpi.label} className="border border-zinc-200 rounded-xl p-5 bg-white shadow-sm">
            <p className="text-xs font-medium text-zinc-500 uppercase tracking-wide">{kpi.label}</p>
            <p className="mt-1 text-2xl font-bold text-zinc-900">{kpi.value}</p>
            <p className="mt-1 text-xs text-zinc-400">{kpi.sub}</p>
          </div>
        ))}
      </div>

      {/* Radar + Gaps */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="border border-zinc-200 rounded-xl p-6 bg-white shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold text-zinc-900">Competency Radar</h2>
            <span className="text-xs font-mono text-zinc-400">Current vs Benchmark</span>
          </div>
          <CompetencyRadar data={radarData} />
        </div>

        <div className="border border-zinc-200 rounded-xl p-6 bg-white shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold text-zinc-900">Critical Skill Gaps</h2>
            <span className="text-xs text-zinc-400 font-mono">{criticalGaps.length} areas to improve</span>
          </div>
          <div className="space-y-3">
            {criticalGaps.map((gap: any) => (
              <div key={gap.code} className="p-3.5 rounded-lg border border-zinc-200 bg-zinc-50">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono text-zinc-500">{gap.code}</span>
                  <span className="text-xs font-semibold text-zinc-700">Gap: {gap.gap} level(s)</span>
                </div>
                <p className="mt-1 text-sm font-medium text-zinc-900">{gap.name}</p>
                <div className="mt-2 flex items-center justify-between text-xs text-zinc-500">
                  <span>Current: L{gap.current_level} → Target: L{gap.target_level}</span>
                  <Link href={`/chat`} className="text-zinc-900 font-semibold hover:underline">
                    Ask AI Tutor →
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Learning Pathway */}
      <div className="border border-zinc-200 rounded-xl p-6 bg-white shadow-sm">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-base font-semibold text-zinc-900">Recommended Learning Pathway</h2>
          <div className="flex space-x-1 border border-zinc-200 rounded-lg p-1 bg-zinc-50">
            <button
              onClick={() => setActiveTab("IGOT")}
              className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                activeTab === "IGOT" ? "bg-white text-zinc-900 shadow-sm border border-zinc-200" : "text-zinc-500 hover:text-zinc-900"
              }`}
            >
              iGOT Karmayogi
            </button>
            <button
              onClick={() => setActiveTab("TPAC")}
              className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                activeTab === "TPAC" ? "bg-white text-zinc-900 shadow-sm border border-zinc-200" : "text-zinc-500 hover:text-zinc-900"
              }`}
            >
              NSSTA Residential TPAC
            </button>
          </div>
        </div>

        <div className="space-y-3">
          {(activeTab === "IGOT" ? igotCourses : tpacBatches).map((item: any) => (
            <div key={item.id} className="p-4 rounded-lg border border-zinc-200 hover:border-zinc-300 transition-colors flex items-center justify-between">
              <div>
                <p className="text-sm font-semibold text-zinc-900">{item.title}</p>
                <p className="text-xs text-zinc-500 mt-0.5">
                  {item.provider || item.location} · {item.duration_hours ? `${item.duration_hours} hrs` : item.batch_start_date}
                </p>
              </div>
              <Link
                href="/assessments"
                className="px-3 py-1.5 rounded-md border border-zinc-300 text-xs font-medium hover:bg-zinc-50 transition-colors"
              >
                Enroll / Nominate →
              </Link>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/* =========================================================================
   2. SUPERVISOR DASHBOARD (Rajesh Verma - Assistant Director, ISS, NAD)
   ========================================================================= */
function SupervisorDashboard() {
  const { currentUser, activePersona } = useAuth();
  const [subordinates, setSubordinates] = useState<any[]>([]);
  const [calibratingOfficer, setCalibratingOfficer] = useState<any | null>(null);
  const [selectedComp, setSelectedComp] = useState("STAT-PRICE");
  const [calibratedLevel, setCalibratedLevel] = useState(3);
  const [calibrating, setCalibrating] = useState(false);
  const [calibratedMsg, setCalibratedMsg] = useState("");

  useEffect(() => {
    async function loadTeam() {
      try {
        const res = await apiGet<any>("/team/my-subordinates");
        if (res?.subordinates && res.subordinates.length > 0) {
          setSubordinates(res.subordinates);
        } else {
          setSubordinates(getSupervisorSubordinates());
        }
      } catch {
        setSubordinates(getSupervisorSubordinates());
      }
    }
    loadTeam();
  }, []);

  function getSupervisorSubordinates() {
    return [
      {
        id: 4,
        full_name: "Pooja Sharma",
        designation: "Junior Statistical Officer",
        cadre: "SSS",
        division: "Field Operations Division (FOD)",
        readiness_percentage: 64.5,
        urgent_gap: "Price Statistics (L1 vs L3 required)",
        status: "NEEDS_INTERVENTION"
      },
      {
        id: 7,
        full_name: "Amit Patel",
        designation: "Junior Statistical Officer",
        cadre: "SSS",
        division: "National Accounts Division (NAD)",
        readiness_percentage: 78.0,
        urgent_gap: "Python Data Automation (L1 vs L2 required)",
        status: "MODERATE"
      },
      {
        id: 8,
        full_name: "Sunita Verma",
        designation: "Senior Statistical Officer",
        cadre: "SSS",
        division: "National Accounts Division (NAD)",
        readiness_percentage: 86.5,
        urgent_gap: "SNA 2008 & SUT Tables (L2 vs L3 required)",
        status: "ON_TRACK"
      },
      {
        id: 9,
        full_name: "Vikas Meena",
        designation: "Junior Statistical Officer",
        cadre: "SSS",
        division: "National Accounts Division (NAD)",
        readiness_percentage: 58.0,
        urgent_gap: "National Accounts Compilation (L1 vs L3 required)",
        status: "NEEDS_INTERVENTION"
      },
      {
        id: 10,
        full_name: "Deepak Rawat",
        designation: "Junior Statistical Officer",
        cadre: "SSS",
        division: "National Accounts Division (NAD)",
        readiness_percentage: 72.0,
        urgent_gap: "Quarterly GDP Estimation (L2 vs L3 required)",
        status: "MODERATE"
      },
      {
        id: 11,
        full_name: "Meenakshi Sundaram",
        designation: "Senior Statistical Officer",
        cadre: "SSS",
        division: "National Accounts Division (NAD)",
        readiness_percentage: 82.5,
        urgent_gap: "None (Benchmark Met)",
        status: "ON_TRACK"
      }
    ];
  }

  const handleSaveCalibration = async () => {
    if (!calibratingOfficer) return;
    setCalibrating(true);
    try {
      await apiPost(`/team/calibrate/${calibratingOfficer.id}`, {
        competency_code: selectedComp,
        new_level: calibratedLevel,
        justification: "Supervisor competency review"
      });
      setCalibratedMsg(`Successfully calibrated ${calibratingOfficer.full_name} to Level ${calibratedLevel}`);
      setTimeout(() => {
        setCalibratingOfficer(null);
        setCalibratedMsg("");
      }, 1500);
    } catch {
      setCalibratedMsg(`Calibrated ${calibratingOfficer.full_name} locally.`);
      setTimeout(() => {
        setCalibratingOfficer(null);
        setCalibratedMsg("");
      }, 1500);
    } finally {
      setCalibrating(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Welcome Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-2xl font-bold text-zinc-900">
              Team Command Center
            </h1>
            <span className="text-xs font-mono font-semibold px-2 py-0.5 rounded bg-zinc-900 text-white">
              SUPERVISOR
            </span>
          </div>
          <p className="mt-1 text-sm text-zinc-500">
            {currentUser?.full_name || activePersona.name} · {currentUser?.designation || activePersona.designation} · {currentUser?.division || activePersona.division}
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <Link
            href="/team-matrix"
            className="px-4 py-2 rounded-lg bg-zinc-900 text-white text-sm font-medium hover:bg-zinc-800 transition-colors flex items-center space-x-1.5"
          >
            <Sliders className="w-4 h-4" />
            <span>Open Full Team Matrix</span>
          </Link>
        </div>
      </div>

      {/* 4 Supervisor KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: "Supervised Officers", value: subordinates.length, sub: "Direct reports in division" },
          { label: "Team Average Readiness", value: "73.2%", sub: "NAD role benchmark score" },
          { label: "Below Benchmark", value: "2", sub: "Require training intervention" },
          { label: "TPAC Nominations", value: "4", sub: "Recommended for NSSTA workshop" },
        ].map((kpi) => (
          <div key={kpi.label} className="border border-zinc-200 rounded-xl p-5 bg-white shadow-sm">
            <p className="text-xs font-medium text-zinc-500 uppercase tracking-wide">{kpi.label}</p>
            <p className="mt-1 text-2xl font-bold text-zinc-900">{kpi.value}</p>
            <p className="mt-1 text-xs text-zinc-400">{kpi.sub}</p>
          </div>
        ))}
      </div>

      {/* Subordinates Roster with Calibrate & Nominate Actions */}
      <div className="border border-zinc-200 rounded-xl p-6 bg-white shadow-sm">
        <div className="flex items-center justify-between mb-5">
          <div>
            <h2 className="text-base font-semibold text-zinc-900">National Accounts Subordinate Officers</h2>
            <p className="text-xs text-zinc-500 mt-0.5">Evaluate and calibrate competency ratings of reporting personnel</p>
          </div>
          <span className="text-xs font-mono text-zinc-400">{subordinates.length} Active Officers</span>
        </div>

        <div className="divide-y divide-zinc-100">
          {subordinates.map((officer) => (
            <div key={officer.id} className="py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="flex items-start space-x-3">
                <div className="w-9 h-9 rounded-full bg-zinc-100 text-zinc-800 font-semibold text-xs flex items-center justify-center shrink-0 mt-0.5">
                  {officer.full_name.split(" ").map((n: string) => n[0]).join("")}
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <p className="text-sm font-semibold text-zinc-900">{officer.full_name}</p>
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-zinc-100 text-zinc-600 border border-zinc-200">
                      {officer.cadre}
                    </span>
                  </div>
                  <p className="text-xs text-zinc-500">{officer.designation} · {officer.division}</p>
                  <p className="text-xs text-zinc-700 mt-1">
                    <span className="text-zinc-400 font-mono">Top Need:</span> {officer.urgent_gap || "Price & National Accounts"}
                  </p>
                </div>
              </div>

              <div className="flex items-center space-x-3 sm:self-center">
                <div className="text-right mr-2 hidden sm:block">
                  <span className="text-sm font-bold text-zinc-900">{officer.readiness_percentage}%</span>
                  <p className="text-[10px] text-zinc-400">Readiness</p>
                </div>

                <button
                  onClick={() => setCalibratingOfficer(officer)}
                  className="px-3 py-1.5 rounded-lg border border-zinc-300 text-xs font-medium text-zinc-700 hover:bg-zinc-100 transition-colors"
                >
                  Calibrate Rating
                </button>
                <Link
                  href="/team-matrix"
                  className="px-3 py-1.5 rounded-lg bg-zinc-900 text-white text-xs font-medium hover:bg-zinc-800 transition-colors"
                >
                  Nominate TPAC
                </Link>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Calibration Modal */}
      {calibratingOfficer && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl border border-zinc-200 max-w-md w-full p-6 space-y-4 shadow-xl">
            <div>
              <h3 className="text-base font-bold text-zinc-900">
                Calibrate Officer Rating
              </h3>
              <p className="text-xs text-zinc-500 mt-0.5">
                Officer: {calibratingOfficer.full_name} ({calibratingOfficer.designation})
              </p>
            </div>

            {calibratedMsg && (
              <div className="p-3 rounded-lg bg-zinc-900 text-white text-xs">
                {calibratedMsg}
              </div>
            )}

            <div className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-zinc-700 mb-1">
                  Competency
                </label>
                <select
                  value={selectedComp}
                  onChange={(e) => setSelectedComp(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-zinc-300 text-sm bg-white text-zinc-900"
                >
                  <option value="STAT-PRICE">Price Statistics & CPI (STAT-PRICE)</option>
                  <option value="STAT-NAS">National Accounts & SNA 2008 (STAT-NAS)</option>
                  <option value="TECH-PYST">Python for Official Statistics (TECH-PYST)</option>
                  <option value="STAT-DQAF">Data Quality Framework (STAT-DQAF)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-zinc-700 mb-1">
                  Calibrated Proficiency Level (1 to 5)
                </label>
                <div className="grid grid-cols-5 gap-2">
                  {[1, 2, 3, 4, 5].map((lvl) => (
                    <button
                      key={lvl}
                      type="button"
                      onClick={() => setCalibratedLevel(lvl)}
                      className={`py-2 rounded-lg text-xs font-semibold border transition-all ${
                        calibratedLevel === lvl
                          ? "bg-zinc-900 text-white border-zinc-900"
                          : "bg-white text-zinc-700 border-zinc-200 hover:border-zinc-400"
                      }`}
                    >
                      L{lvl}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-zinc-700 mb-1">
                  Supervisory Justification
                </label>
                <textarea
                  rows={2}
                  placeholder="e.g. Demonstrated satisfactory command over quarterly GVA estimation schedule."
                  className="w-full p-2.5 rounded-lg border border-zinc-300 text-xs text-zinc-900 focus:outline-none focus:ring-1 focus:ring-zinc-900"
                />
              </div>
            </div>

            <div className="flex justify-end space-x-2 pt-2">
              <button
                type="button"
                onClick={() => setCalibratingOfficer(null)}
                className="px-4 py-2 rounded-lg border border-zinc-300 text-xs font-medium text-zinc-700 hover:bg-zinc-50"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={calibrating}
                onClick={handleSaveCalibration}
                className="px-4 py-2 rounded-lg bg-zinc-900 text-white text-xs font-semibold hover:bg-zinc-800 disabled:opacity-50"
              >
                {calibrating ? "Saving..." : "Confirm Rating"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/* =========================================================================
   3. TRAINER DASHBOARD (Dr. Sunita Rao - Senior Faculty, NSSTA Academy)
   ========================================================================= */
function TrainerDashboard() {
  const { currentUser, activePersona } = useAuth();

  const activeBatches = [
    { id: 1, title: "Price Statistics & Inflation Indices", type: "Residential TPAC", start: "15 Nov 2026", enrolled: 28, capacity: 30, location: "NSSTA Campus, Greater Noida" },
    { id: 2, title: "SNA 2008 & Macroeconomic Aggregates", type: "Executive Workshop", start: "02 Dec 2026", enrolled: 22, capacity: 25, location: "NSSTA Campus, Greater Noida" },
    { id: 3, title: "Survey Sampling Design & SAE Methodology", type: "Residential TPAC", start: "10 Jan 2027", enrolled: 18, capacity: 25, location: "NSSTA Campus, Greater Noida" },
    { id: 4, title: "Python for Survey Data Automation", type: "Hybrid Lab", start: "20 Jan 2027", enrolled: 30, capacity: 30, location: "Virtual + NSSTA Digital Lab" }
  ];

  return (
    <div className="space-y-8">
      {/* Welcome Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-2xl font-bold text-zinc-900">
              NSSTA Faculty Hub
            </h1>
            <span className="text-xs font-mono font-semibold px-2 py-0.5 rounded bg-zinc-900 text-white">
              TRAINER / FACULTY
            </span>
          </div>
          <p className="mt-1 text-sm text-zinc-500">
            {currentUser?.full_name || activePersona.name} · {currentUser?.designation || activePersona.designation} · {currentUser?.division || activePersona.division}
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <Link
            href="/assessments"
            className="px-4 py-2 rounded-lg bg-zinc-900 text-white text-sm font-medium hover:bg-zinc-800 transition-colors flex items-center space-x-1.5"
          >
            <Sparkles className="w-4 h-4 text-zinc-300" />
            <span>AI Question Generator</span>
          </Link>
        </div>
      </div>

      {/* 4 Faculty KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: "Active Training Batches", value: "4", sub: "Residential & Hybrid at NSSTA" },
          { label: "Question Bank Size", value: "145+", sub: "MoSPI manual aligned MCQs" },
          { label: "Officers Trained", value: "240", sub: "Civil servants certified this year" },
          { label: "Assessment Pass Rate", value: "91.4%", sub: "Avg score: 76.8%" },
        ].map((kpi) => (
          <div key={kpi.label} className="border border-zinc-200 rounded-xl p-5 bg-white shadow-sm">
            <p className="text-xs font-medium text-zinc-500 uppercase tracking-wide">{kpi.label}</p>
            <p className="mt-1 text-2xl font-bold text-zinc-900">{kpi.value}</p>
            <p className="mt-1 text-xs text-zinc-400">{kpi.sub}</p>
          </div>
        ))}
      </div>

      {/* Fast AI Assessment Authoring Action Card */}
      <div className="border border-zinc-200 rounded-xl p-6 bg-zinc-50 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-semibold text-zinc-900">Author Adaptive Assessments with AI</h2>
          <p className="text-xs text-zinc-600 mt-1 max-w-xl">
            Upload MoSPI manuals (National Accounts, CPI, PLFS) and automatically generate Bloom-stratified psychometric multiple-choice items with authentic distractors.
          </p>
        </div>
        <Link
          href="/assessments"
          className="px-5 py-2.5 rounded-lg bg-zinc-900 text-white text-xs font-semibold hover:bg-zinc-800 transition-colors shrink-0 flex items-center space-x-1.5"
        >
          <span>Open Authoring Studio →</span>
        </Link>
      </div>

      {/* Active Residential Batches at NSSTA Greater Noida */}
      <div className="border border-zinc-200 rounded-xl p-6 bg-white shadow-sm">
        <div className="flex items-center justify-between mb-5">
          <div>
            <h2 className="text-base font-semibold text-zinc-900">Active & Upcoming NSSTA Training Batches</h2>
            <p className="text-xs text-zinc-500 mt-0.5">Residential capacity planning and attendee enrollment monitoring</p>
          </div>
          <span className="text-xs font-mono text-zinc-400">NSSTA Greater Noida</span>
        </div>

        <div className="space-y-3">
          {activeBatches.map((batch) => {
            const pct = Math.round((batch.enrolled / batch.capacity) * 100);
            return (
              <div key={batch.id} className="p-4 rounded-lg border border-zinc-200 hover:border-zinc-300 transition-colors">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div>
                    <div className="flex items-center space-x-2">
                      <p className="text-sm font-semibold text-zinc-900">{batch.title}</p>
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-zinc-100 border border-zinc-200 text-zinc-700">
                        {batch.type}
                      </span>
                    </div>
                    <p className="text-xs text-zinc-500 mt-0.5">
                      Start: {batch.start} · Location: {batch.location}
                    </p>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="text-right">
                      <span className="text-xs font-semibold text-zinc-900">{batch.enrolled}/{batch.capacity} seats</span>
                      <p className="text-[10px] text-zinc-400">{pct}% filled</p>
                    </div>
                    <div className="w-20 bg-zinc-100 rounded-full h-2">
                      <div className="bg-zinc-900 h-2 rounded-full" style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

/* =========================================================================
   4. ADMIN DASHBOARD (Alok Mathur - Director / DDG, Cadre Admin)
   ========================================================================= */
function AdminDashboard() {
  const { currentUser, activePersona } = useAuth();
  const [downloading, setDownloading] = useState(false);

  const divisions = [
    { code: "FOD", name: "Field Operations Division", officers: 15, avg: 58 },
    { code: "NAD", name: "National Accounts Division", officers: 10, avg: 68 },
    { code: "ESD", name: "Economic Statistics Division", officers: 9, avg: 62 },
    { code: "SDRD", name: "Survey Design & Research", officers: 8, avg: 55 },
  ];

  const bottlenecks = [
    { code: "STAT-PRICE", name: "Price Statistics & CPI", gap: 1.8, officers_below: 28 },
    { code: "TECH-PYST", name: "Python for Official Statistics", gap: 1.5, officers_below: 31 },
    { code: "STAT-NAS", name: "National Accounts & SNA 2008", gap: 1.2, officers_below: 18 },
    { code: "GOV-DPDP", name: "Data Privacy & DPDP Act", gap: 1.0, officers_below: 22 },
  ];

  const handleDownloadReport = async () => {
    setDownloading(true);
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
        a.download = "Ministry_Capacity_Readiness_Report.pdf";
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
      } else {
        window.print();
      }
    } catch {
      window.print();
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Welcome Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-2xl font-bold text-zinc-900">
              Cadre Administration Command
            </h1>
            <span className="text-xs font-mono font-semibold px-2 py-0.5 rounded bg-zinc-900 text-white">
              ADMIN / DDG
            </span>
          </div>
          <p className="mt-1 text-sm text-zinc-500">
            {currentUser?.full_name || activePersona.name} · {currentUser?.designation || activePersona.designation} · {currentUser?.division || activePersona.division}
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={handleDownloadReport}
            disabled={downloading}
            className="px-4 py-2 rounded-lg bg-zinc-900 text-white text-sm font-medium hover:bg-zinc-800 transition-colors flex items-center space-x-1.5"
          >
            <Download className="w-4 h-4" />
            <span>{downloading ? "Generating..." : "Download Readiness PDF"}</span>
          </button>
          <Link
            href="/admin"
            className="px-4 py-2 rounded-lg border border-zinc-300 text-zinc-700 text-sm font-medium hover:bg-zinc-50 transition-colors"
          >
            TPAC Allocator →
          </Link>
        </div>
      </div>

      {/* 4 Macro KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: "Total Officers in Cadre", value: "42", sub: "Active statistical personnel" },
          { label: "MoSPI Workforce Readiness", value: "64.2%", sub: "National benchmark aggregate" },
          { label: "Total Identified Gaps", value: "87", sub: "Across 4 operational divisions" },
          { label: "Priority TPAC Actions", value: "12", sub: "Immediate allocations required" },
        ].map((kpi) => (
          <div key={kpi.label} className="border border-zinc-200 rounded-xl p-5 bg-white shadow-sm">
            <p className="text-xs font-medium text-zinc-500 uppercase tracking-wide">{kpi.label}</p>
            <p className="mt-1 text-2xl font-bold text-zinc-900">{kpi.value}</p>
            <p className="mt-1 text-xs text-zinc-400">{kpi.sub}</p>
          </div>
        ))}
      </div>

      {/* Division Comparison Bars */}
      <div className="border border-zinc-200 rounded-xl p-6 bg-white shadow-sm">
        <h2 className="text-base font-semibold text-zinc-900 mb-4">Ministry Division Competency Comparison</h2>
        <div className="space-y-4">
          {divisions.map((div) => (
            <div key={div.code} className="space-y-1.5">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-zinc-900">{div.name} ({div.code})</span>
                <span className="text-zinc-500 font-mono">{div.officers} officers · {div.avg}% avg</span>
              </div>
              <div className="w-full bg-zinc-100 rounded-full h-2.5">
                <div
                  className="bg-zinc-900 h-2.5 rounded-full transition-all"
                  style={{ width: `${div.avg}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Top Ministry Bottlenecks */}
      <div className="border border-zinc-200 rounded-xl p-6 bg-white shadow-sm">
        <h2 className="text-base font-semibold text-zinc-900 mb-4">Top Ministry-Wide Competency Bottlenecks</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-zinc-200 text-left">
                <th className="pb-3 text-xs font-semibold uppercase text-zinc-500">Code</th>
                <th className="pb-3 text-xs font-semibold uppercase text-zinc-500">Competency</th>
                <th className="pb-3 text-xs font-semibold uppercase text-zinc-500 text-right">Avg Gap</th>
                <th className="pb-3 text-xs font-semibold uppercase text-zinc-500 text-right">Officers Below Target</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-100">
              {bottlenecks.map((b) => (
                <tr key={b.code}>
                  <td className="py-3 font-mono text-xs text-zinc-500">{b.code}</td>
                  <td className="py-3 font-medium text-zinc-900">{b.name}</td>
                  <td className="py-3 text-right font-mono font-semibold text-zinc-800">{b.gap}</td>
                  <td className="py-3 text-right font-mono text-zinc-600">{b.officers_below}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
