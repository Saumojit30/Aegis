"use client";

import React, { useEffect, useState } from "react";

export default function ClinicianDashboard() {
  const [patientId, setPatientId] = useState("P001");
  const [speed, setSpeed] = useState(10);
  const [degradation, setDegradation] = useState("D0");
  const [liveGlucose, setLiveGlucose] = useState(124);
  const [liveHR, setLiveHR] = useState(74);
  const [liveMETs, setLiveMETs] = useState(1.15);
  const [reliability, setReliability] = useState("HIGH");

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const handleStart = async () => {
    await fetch(`${API_URL}/replay/start?session_id=web_ui&patient_id=${patientId}&speed=${speed}&degradation=${degradation}`, { method: "POST" });
  };

  const handlePause = async () => {
    await fetch(`${API_URL}/replay/pause?session_id=web_ui`, { method: "POST" });
  };

  const handleStop = async () => {
    await fetch(`${API_URL}/replay/stop?session_id=web_ui`, { method: "POST" });
  };

  const handleDegradation = async (deg: string) => {
    setDegradation(deg);
    await fetch(`${API_URL}/replay/degrade?session_id=web_ui&degradation=${deg}`, { method: "POST" });
    if (deg === "D4" || deg === "D7") setReliability("LOW");
    else if (deg.startsWith("D1") || deg === "D3") setReliability("MODERATE");
    else setReliability("HIGH");
  };

  return (
    <div className="flex flex-col min-h-screen">
      {/* Clinical Disclaimer */}
      <div className="bg-amber-950/80 border-b border-amber-600/40 text-amber-200 px-4 py-2 text-xs flex justify-between items-center">
        <div>
          <span className="font-bold uppercase tracking-wider bg-amber-500 text-neutral-950 px-1.5 py-0.5 rounded text-[10px] mr-2">Research Prototype</span>
          Model-based estimates using open & synthetic data only. <strong>Not medical advice and not suitable for treatment decisions.</strong>
        </div>
        <div className="hidden md:block font-mono text-[11px] text-amber-300/70">
          Decisions D12-D16 Enforced • Gate G2 Approved
        </div>
      </div>

      {/* Header */}
      <header className="bg-slate-900 border-b border-slate-800 px-6 py-3 flex justify-between items-center">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400 font-bold">
            AE
          </div>
          <div>
            <h1 className="text-sm font-bold text-white flex items-center gap-2">
              Aegis Clinician Twin Dashboard
              <span className="text-[10px] bg-slate-800 text-slate-300 px-1.5 py-0.5 rounded font-mono">Next.js 14</span>
            </h1>
            <p className="text-[11px] text-slate-400">180-Min Calibrated Glucose Trajectory Forecasting</p>
          </div>
        </div>

        {/* Replay Controls */}
        <div className="flex items-center space-x-2 bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-800 text-xs">
          <label className="text-slate-400">Twin:</label>
          <select value={patientId} onChange={(e) => setPatientId(e.target.value)} className="bg-slate-900 border border-slate-700 text-white rounded px-2 py-0.5 outline-none">
            <option value="P001">P001 (T2D, 58y, HbA1c 6.8%)</option>
            <option value="P002">P002 (T2D, 62y, HbA1c 7.4%)</option>
            <option value="P010">P010 (T2D, 54y, HbA1c 6.3%)</option>
          </select>
          <button onClick={handleStart} className="bg-emerald-600 hover:bg-emerald-500 text-white px-2 py-0.5 rounded font-medium">▶ Start</button>
          <button onClick={handlePause} className="bg-slate-800 hover:bg-slate-700 text-slate-200 px-2 py-0.5 rounded font-medium">⏸ Pause</button>
          <button onClick={handleStop} className="bg-slate-800 hover:bg-slate-700 text-rose-400 px-2 py-0.5 rounded font-medium">⏹ Stop</button>
        </div>
      </header>

      {/* Main Grid */}
      <main className="flex-1 p-5 grid grid-cols-1 lg:grid-cols-12 gap-5 max-w-[1700px] w-full mx-auto">
        {/* Left Profile Column */}
        <div className="lg:col-span-3 space-y-4">
          <div className="bg-slate-900 rounded-xl border border-slate-800 p-4">
            <h2 className="text-xs font-semibold uppercase text-slate-400 mb-2">Digital Twin Profile</h2>
            <div className="space-y-1 text-xs">
              <div className="flex justify-between py-1 border-b border-slate-800/60"><span className="text-slate-400">Patient ID:</span> <span className="font-mono text-white">{patientId}</span></div>
              <div className="flex justify-between py-1 border-b border-slate-800/60"><span className="text-slate-400">Clinical Group:</span> <span className="text-emerald-400 font-bold">Type 2 Diabetes</span></div>
              <div className="flex justify-between py-1 border-b border-slate-800/60"><span className="text-slate-400">HbA1c Baseline:</span> <span className="text-amber-400 font-bold">6.8%</span></div>
              <div className="flex justify-between py-1"><span className="text-slate-400">Fasting Glucose:</span> <span className="text-white">118 mg/dL</span></div>
            </div>
          </div>

          <div className="bg-slate-900 rounded-xl border border-slate-800 p-4">
            <div className="flex justify-between items-center mb-2">
              <h2 className="text-xs font-semibold uppercase text-slate-400">Synthetic EHR Extras</h2>
              <span className="text-[9px] bg-amber-500/20 text-amber-300 border border-amber-500/40 px-1 rounded font-bold font-mono">D14</span>
            </div>
            <p className="text-xs text-slate-300">Medications: Metformin 500mg, Lisinopril 10mg</p>
            <p className="text-xs text-slate-400 mt-1">Comorbidities: Essential Hypertension, Dyslipidemia</p>
          </div>
        </div>

        {/* Center Forecast Column */}
        <div className="lg:col-span-6 space-y-4">
          <div className="bg-slate-900 rounded-xl border border-slate-800 p-4">
            <div className="flex justify-between items-center mb-3">
              <h2 className="text-sm font-bold text-white">180-Minute Calibrated Forecast</h2>
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded font-mono ${reliability === "HIGH" ? "bg-emerald-950 text-emerald-400 border border-emerald-800" : "bg-rose-950 text-rose-400 border border-rose-800"}`}>
                {reliability} CONFIDENCE
              </span>
            </div>
            <div className="h-64 bg-slate-950/80 rounded-lg border border-slate-800 flex items-center justify-center text-slate-500 text-xs font-mono">
              [ Candidate S Trajectory Plot & Conformal ±20 mg/dL Uncertainty Band ]
            </div>
            <div className="grid grid-cols-3 gap-2 mt-3 text-center text-xs font-mono">
              <div className="bg-slate-950 p-2 rounded border border-slate-800"><span className="text-[10px] text-slate-400 block font-sans">Predicted Peak</span>164.2 mg/dL</div>
              <div className="bg-slate-950 p-2 rounded border border-slate-800"><span className="text-[10px] text-slate-400 block font-sans">Time to Peak</span>55 min</div>
              <div className="bg-slate-950 p-2 rounded border border-slate-800"><span className="text-[10px] text-slate-400 block font-sans">Time &gt; 180</span>0 min</div>
            </div>
          </div>
        </div>

        {/* Right Telemetry Column */}
        <div className="lg:col-span-3 space-y-4">
          <div className="bg-slate-900 rounded-xl border border-slate-800 p-4">
            <h2 className="text-xs font-semibold uppercase text-slate-400 mb-2">Live Sensor Stream</h2>
            <div className="grid grid-cols-3 gap-2 text-center font-mono">
              <div className="bg-slate-950 p-2 rounded border border-slate-800"><span className="text-[9px] text-slate-400 block">Glucose</span><span className="text-emerald-400 font-bold">{liveGlucose}</span></div>
              <div className="bg-slate-950 p-2 rounded border border-slate-800"><span className="text-[9px] text-slate-400 block">HR</span><span className="text-slate-200 font-bold">{liveHR}</span></div>
              <div className="bg-slate-950 p-2 rounded border border-slate-800"><span className="text-[9px] text-slate-400 block">METs</span><span className="text-slate-200 font-bold">{liveMETs}</span></div>
            </div>
          </div>

          <div className="bg-slate-900 rounded-xl border border-slate-800 p-4">
            <h2 className="text-xs font-semibold uppercase text-slate-400 mb-2">Degradation Injector (D0-D7)</h2>
            <div className="grid grid-cols-2 gap-1.5 text-xs">
              <button onClick={() => handleDegradation("D0")} className="bg-slate-800 hover:bg-slate-700 p-1.5 rounded text-[11px] text-left">D0: Nominal</button>
              <button onClick={() => handleDegradation("D1_30m")} className="bg-slate-800 hover:bg-slate-700 text-amber-300 p-1.5 rounded text-[11px] text-left">D1: Dropout 30m</button>
              <button onClick={() => handleDegradation("D3")} className="bg-slate-800 hover:bg-slate-700 text-amber-300 p-1.5 rounded text-[11px] text-left">D3: No HR/METs</button>
              <button onClick={() => handleDegradation("D4")} className="bg-slate-800 hover:bg-slate-700 text-rose-400 p-1.5 rounded text-[11px] text-left">D4: Reduced CGM</button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
