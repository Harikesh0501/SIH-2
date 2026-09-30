"use client";

import React from "react";
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from "recharts";

export interface RadarDataPoint {
  domain: string;
  current: number;
  target: number;
  fullMark: number;
}

interface CompetencyRadarProps {
  data: RadarDataPoint[];
}

export function CompetencyRadar({ data }: CompetencyRadarProps) {
  if (!data || data.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-xs text-zinc-400">
        No competency rubric data available.
      </div>
    );
  }

  return (
    <div className="w-full h-72 sm:h-80">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart cx="50%" cy="50%" outerRadius="70%" data={data}>
          <PolarGrid stroke="#e4e4e7" strokeDasharray="3 3" />
          <PolarAngleAxis
            dataKey="domain"
            tick={{ fill: "#27272a", fontSize: 11, fontWeight: 500 }}
          />
          <PolarRadiusAxis
            angle={30}
            domain={[0, 5]}
            tick={{ fill: "#71717a", fontSize: 10 }}
            tickCount={6}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#18181b",
              borderColor: "#27272a",
              color: "#ffffff",
              borderRadius: "6px",
              fontSize: "11px",
            }}
            formatter={(value: any, name: any) => [
              `Level ${value} / 5`,
              name === "current" ? "Current Assessed" : "Target Benchmark",
            ]}
          />
          <Legend
            wrapperStyle={{ fontSize: "11px", paddingTop: "10px" }}
            formatter={(value) => (
              <span className="text-zinc-700 font-medium">
                {value === "current" ? "Current Proficiency Level" : "Official Role Benchmark"}
              </span>
            )}
          />
          <Radar
            name="current"
            dataKey="current"
            stroke="#09090b"
            strokeWidth={2}
            fill="#18181b"
            fillOpacity={0.35}
          />
          <Radar
            name="target"
            dataKey="target"
            stroke="#71717a"
            strokeWidth={1.5}
            strokeDasharray="4 4"
            fill="#a1a1aa"
            fillOpacity={0.1}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
