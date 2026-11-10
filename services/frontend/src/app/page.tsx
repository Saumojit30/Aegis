"use client";

import React, { useState, useEffect, useMemo } from "react";

interface CommandAction {
  id: string;
  title: string;
  cat: string;
  key: string;
  run: () => void;
}

export default function ClinicianDashboard() {
  // Navigation & View State
  const [activeTab, setActiveTab] = useState<"forecast" | "whatif" | "timeline" | "profile" | "audit" | "settings">("forecast");
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const sidebarRef = React.useRef<HTMLElement | null>(null);

  const handleSelectTab = (tab: "forecast" | "whatif" | "timeline" | "profile" | "audit" | "settings") => {
    setActiveTab(tab);
    setMobileMenuOpen(false);
  };

  useEffect(() => {
    const handleDocumentClick = (e: MouseEvent) => {
      if (window.innerWidth >= 1024 || !mobileMenuOpen) return;
      const toggleBtn = document.getElementById("mobileSidebarToggle");
      if (
        sidebarRef.current &&
        !sidebarRef.current.contains(e.target as Node) &&
        (!toggleBtn || !toggleBtn.contains(e.target as Node))
      ) {
        setMobileMenuOpen(false);
      }
    };
    document.addEventListener("click", handleDocumentClick);
    return () => document.removeEventListener("click", handleDocumentClick);
  }, [mobileMenuOpen]);

  // Theme State (Dark / Light) - Light mode is default
  const [theme, setTheme] = useState<"dark" | "light">("light");

  // Patient Twin & Replay Cockpit State
  const [patientId, setPatientId] = useState("P020");
  const [speed, setSpeed] = useState(10);
  const [isPlaying, setIsPlaying] = useState(false);
  const [degradation, setDegradation] = useState("D0");
  const [reliability, setReliability] = useState<"HIGH" | "MODERATE" | "LOW">("HIGH");

  // Command Palette State
  const [isPaletteOpen, setIsPaletteOpen] = useState(false);
  const [paletteQuery, setPaletteQuery] = useState("");
  const [paletteIndex, setPaletteIndex] = useState(0);

  // Custom Meal Modal State
  const [isCustomMealOpen, setIsCustomMealOpen] = useState(false);
  const [customName, setCustomName] = useState("Paneer Butter Masala with Roti");
  const [customCarbs, setCustomCarbs] = useState(52);
  const [customFat, setCustomFat] = useState(24);
  const [customProtein, setCustomProtein] = useState(18);

  // Doctronic AI Doctor Persona State
  const [doctorResponseStyle, setDoctorResponseStyle] = useState("Just the facts");
  const [isStylePopoverOpen, setIsStylePopoverOpen] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Biometrics Telemetry
  const liveGlucose = 136.6;
  const liveHR = 71;
  const liveMETs = 1.0;
  const lastMeal = "Roti, Dal & Sabzi";
  const lastMealMacros = "48g Carbs • 12g Fat";

  // What-If Sandbox State
  const [activeDishName, setActiveDishName] = useState("Roti, Dal & Sabzi");
  const [carbs, setCarbs] = useState(48);
  const [fat, setFat] = useState(12);
  const [protein, setProtein] = useState(16);
  const [portion, setPortion] = useState(100);
  const [portionUncertainty, setPortionUncertainty] = useState(0);
  const [bolusUnits, setBolusUnits] = useState(0.0);
  const [bolusTime, setBolusTime] = useState(0);
  const [basalDiff, setBasalDiff] = useState(0.0);
  const [walking, setWalking] = useState(false);
  const [sequencing, setSequencing] = useState(false);

  // Biomarkers Modal State
  const [isBiomarkersModalOpen, setIsBiomarkersModalOpen] = useState(false);
  const [editWeight, setEditWeight] = useState(78.0);
  const [editHeight, setEditHeight] = useState(168.0);
  const [editFastingGlucose, setEditFastingGlucose] = useState(138.0);
  const [editFastingInsulin, setEditFastingInsulin] = useState(14.2);
  const [editHbA1c, setEditHbA1c] = useState(7.4);
  const [editTriglycerides, setEditTriglycerides] = useState(185);
  const [editHDL, setEditHDL] = useState(42);
  const [editLDL, setEditLDL] = useState(128);
  const [editISF, setEditISF] = useState<string>("");
  const [editCIR, setEditCIR] = useState<string>("");

  // Patient Twin Phenotypes with Complete Metabolic Lab Panels
  interface PatientProfile {
    age: string;
    weight: number;
    height: number;
    bmi: string;
    hba1c: string;
    fasting: string;
    fastingGlucose: number;
    fastingInsulin: number;
    homa: number;
    triglycerides: number;
    hdl: number;
    ldl: number;
    tdd: number;
    isf: number;
    cir: number;
    isfOverride: number | null;
    cirOverride: number | null;
    diagnosis: string;
    meds: string;
    comorbidities: string;
  }

  const [patientDatabase, setPatientDatabase] = useState<Record<string, PatientProfile>>({
    P020: {
      age: "58y / Male", weight: 78.0, height: 168.0, bmi: "27.6 kg/m²", hba1c: "7.4%",
      fasting: "138 mg/dL", fastingGlucose: 138.0, fastingInsulin: 14.2, homa: 4.84,
      triglycerides: 185, hdl: 42, ldl: 128,
      tdd: 42.9, isf: 42.0, cir: 11.7, isfOverride: null, cirOverride: null,
      diagnosis: "Type 2 Diabetes", meds: "Metformin 500mg BID, Lisinopril 10mg QD",
      comorbidities: "Essential Hypertension, Dyslipidemia"
    },
    P021: {
      age: "61y / Female", weight: 82.0, height: 165.0, bmi: "30.1 kg/m²", hba1c: "7.8%",
      fasting: "146 mg/dL", fastingGlucose: 146.0, fastingInsulin: 16.5, homa: 5.95,
      triglycerides: 210, hdl: 38, ldl: 142,
      tdd: 45.1, isf: 39.9, cir: 11.1, isfOverride: null, cirOverride: null,
      diagnosis: "Type 2 Diabetes", meds: "Metformin 1000mg BID, Empagliflozin 10mg QD",
      comorbidities: "Microalbuminuria"
    },
    P010: {
      age: "48y / Male", weight: 74.0, height: 172.0, bmi: "25.0 kg/m²", hba1c: "6.0%",
      fasting: "112 mg/dL", fastingGlucose: 112.0, fastingInsulin: 8.5, homa: 2.35,
      triglycerides: 155, hdl: 46, ldl: 118,
      tdd: 40.7, isf: 44.2, cir: 12.3, isfOverride: null, cirOverride: null,
      diagnosis: "Prediabetes", meds: "Lifestyle modification, Metformin 250mg QD",
      comorbidities: "None recorded"
    },
    P001: {
      age: "28y / Female", weight: 58.0, height: 164.0, bmi: "21.6 kg/m²", hba1c: "5.2%",
      fasting: "88 mg/dL", fastingGlucose: 88.0, fastingInsulin: 4.5, homa: 0.98,
      triglycerides: 95, hdl: 58, ldl: 85,
      tdd: 31.9, isf: 56.4, cir: 15.7, isfOverride: null, cirOverride: null,
      diagnosis: "Healthy Control", meds: "None",
      comorbidities: "None"
    }
  });

  const currentPatient = patientDatabase[patientId] || patientDatabase.P020;
  const activeISF = currentPatient.isfOverride || currentPatient.isf || 42.0;

  // Closed-form analytical gamma absorption calculation
  const calculateGammaAbs = (t_min: number, t_bolus_min: number): number => {
    const delta_t = t_min - t_bolus_min;
    if (delta_t <= 0) return 0.0;
    if (delta_t >= 300.0) return 1.0;
    const x = delta_t / 55.0;
    return Math.min(1.0, Math.max(0.0, 1.0 - (1.0 + x) * Math.exp(-x)));
  };

  const calculateIOB = (t_min: number, units: number, t_bolus: number): number => {
    if (units <= 0 || t_min < t_bolus) return 0.0;
    const f_abs = calculateGammaAbs(t_min, t_bolus);
    return Math.max(0.0, units * (1.0 - f_abs));
  };

  // Trajectory Constants & Closed-Form Pharmacological Arrays
  const nominalPred = [136.6, 142.1, 151.4, 161.0, 164.2, 160.8, 154.2, 148.0, 142.5, 139.1, 137.8, 136.9, 136.2];
  const timeSteps = [0, 15, 30, 45, 60, 75, 90, 105, 120, 135, 150, 165, 180];

  const f_abs_0 = calculateGammaAbs(0.0, bolusTime);
  const insulinDeflections = timeSteps.map((t) => {
    const f_abs_t = calculateGammaAbs(t, bolusTime);
    const delta_abs = f_abs_t - f_abs_0;
    const bolus_def = -activeISF * bolusUnits * delta_abs;
    const basal_def = -activeISF * basalDiff * (t / 60.0);
    return bolus_def + basal_def;
  });

  const activeIOB60 = calculateIOB(60.0, bolusUnits, bolusTime);
  const netDeflection60 = insulinDeflections[4]; // idx 4 = 60 min

  const carbDelta = ((portion / 100 - 1) * 35) + ((carbs - 48) * 0.45);
  const fatDelta = (fat - 12) * 0.3;
  const exerciseDelta = (walking ? -18 : 0) + (sequencing ? -15 : 0);

  const counterfactualTrajectory = nominalPred.map((val, idx) => {
    if (idx === 0) return val;
    const progress = idx / 12;
    const peakImpact = Math.sin(progress * Math.PI) * (carbDelta + exerciseDelta);
    const lateImpact = (progress > 0.5 ? (progress - 0.5) * 2 : 0) * fatDelta;
    const insImpact = insulinDeflections[idx];
    return Number(Math.max(40.0, Math.min(400.0, val + peakImpact + lateImpact + insImpact)).toFixed(1));
  });

  const deltaPortion = portionUncertainty / 100.0;
  const robustUpper = counterfactualTrajectory.map((y) => {
    const kinetic = Math.abs(y - nominalPred[0]);
    const dTraj = deltaPortion * kinetic;
    return Number(Math.min(400.0, y + dTraj + 14.0).toFixed(1));
  });
  const robustLower = counterfactualTrajectory.map((y) => {
    const kinetic = Math.abs(y - nominalPred[0]);
    const dTraj = deltaPortion * kinetic;
    return Number(Math.max(40.0, y - dTraj - 14.0).toFixed(1));
  });

  const peakBaseline = Math.max(...nominalPred);
  const peakCounterfactual = Math.max(...counterfactualTrajectory);
  const deltaPeakValue = Number((peakCounterfactual - peakBaseline).toFixed(1));

  // Live Modal calculations
  const modalBMI = (editWeight > 0 && editHeight > 0)
    ? Number((editWeight / ((editHeight / 100) * (editHeight / 100))).toFixed(1))
    : 0;
  const modalHOMA = (editFastingGlucose > 0 && editFastingInsulin > 0)
    ? Number(((editFastingGlucose * editFastingInsulin) / 405.0).toFixed(2))
    : 0;
  const modalTDD = editWeight > 0 ? Number((0.55 * editWeight).toFixed(1)) : 0;
  const modalISF = editWeight > 0 ? Number((1800.0 / (0.55 * editWeight)).toFixed(1)) : 0;
  const modalCIR = editWeight > 0 ? Number((500.0 / (0.55 * editWeight)).toFixed(1)) : 0;

  const openBiomarkersModal = () => {
    const p = patientDatabase[patientId] || patientDatabase.P020;
    setEditWeight(p.weight);
    setEditHeight(p.height);
    setEditFastingGlucose(p.fastingGlucose);
    setEditFastingInsulin(p.fastingInsulin);
    setEditHbA1c(parseFloat(p.hba1c) || 7.4);
    setEditTriglycerides(p.triglycerides);
    setEditHDL(p.hdl);
    setEditLDL(p.ldl);
    setEditISF(p.isfOverride !== null ? String(p.isfOverride) : "");
    setEditCIR(p.cirOverride !== null ? String(p.cirOverride) : "");
    setIsBiomarkersModalOpen(true);
  };

  // Re-sync modal fields if active patient is changed while modal is open
  useEffect(() => {
    if (isBiomarkersModalOpen) {
      const p = patientDatabase[patientId] || patientDatabase.P020;
      setEditWeight(p.weight);
      setEditHeight(p.height);
      setEditFastingGlucose(p.fastingGlucose);
      setEditFastingInsulin(p.fastingInsulin);
      setEditHbA1c(parseFloat(p.hba1c) || 7.4);
      setEditTriglycerides(p.triglycerides);
      setEditHDL(p.hdl);
      setEditLDL(p.ldl);
      setEditISF(p.isfOverride !== null ? String(p.isfOverride) : "");
      setEditCIR(p.cirOverride !== null ? String(p.cirOverride) : "");
    }
  }, [patientId, isBiomarkersModalOpen]);

  const saveBiomarkers = async () => {
    if (editWeight <= 0 || editHeight <= 0 || editFastingGlucose <= 0 || editFastingInsulin <= 0) {
      triggerToast("Please enter positive numerical values for weight, height, glucose, and insulin");
      return;
    }

    const isfParsed = parseFloat(editISF);
    const cirParsed = parseFloat(editCIR);
    const isfVal = editISF.trim() !== "" && !isNaN(isfParsed) && isfParsed > 0 ? isfParsed : null;
    const cirVal = editCIR.trim() !== "" && !isNaN(cirParsed) && cirParsed > 0 ? cirParsed : null;
    const finalISF = isfVal || modalISF;
    const finalCIR = cirVal || modalCIR;

    const updatedProfile: PatientProfile = {
      ...(patientDatabase[patientId] || patientDatabase.P020),
      weight: editWeight,
      height: editHeight,
      bmi: `${modalBMI} kg/m²`,
      hba1c: `${editHbA1c}%`,
      fasting: `${editFastingGlucose} mg/dL`,
      fastingGlucose: editFastingGlucose,
      fastingInsulin: editFastingInsulin,
      homa: modalHOMA,
      triglycerides: editTriglycerides,
      hdl: editHDL,
      ldl: editLDL,
      tdd: modalTDD,
      isf: finalISF,
      cir: finalCIR,
      isfOverride: isfVal,
      cirOverride: cirVal,
    };

    setPatientDatabase((prev) => ({
      ...prev,
      [patientId]: updatedProfile,
    }));

    try {
      await fetch(`/patients/${patientId}/biomarkers`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          weight_kg: editWeight,
          height_cm: editHeight,
          bmi: modalBMI,
          fasting_glucose: editFastingGlucose,
          fasting_insulin: editFastingInsulin,
          hba1c: editHbA1c,
          triglycerides: editTriglycerides,
          hdl: editHDL,
          ldl: editLDL,
          isf: isfVal,
          cir: cirVal,
        }),
      });
    } catch (err) {
      console.warn("Backend update error:", err);
    }

    setIsBiomarkersModalOpen(false);
    triggerToast(`Biomarkers updated successfully for ${patientId}`);
  };

  // Total Calories & Macro Percentages
  const totalKcal = carbs * 4 + protein * 4 + fat * 9;
  const totalGrams = carbs + protein + fat || 1;
  const cPct = Math.round((carbs / totalGrams) * 100);
  const pPct = Math.round((protein / totalGrams) * 100);
  const fPct = 100 - cPct - pPct;

  // Initialize and synchronize theme (Default: Light mode)
  useEffect(() => {
    const saved = localStorage.getItem("aegis_theme") as "dark" | "light" | null;
    if (saved === "light" || saved === "dark") {
      setTheme(saved);
      document.documentElement.classList.toggle("dark", saved === "dark");
    } else {
      setTheme("light");
      document.documentElement.classList.remove("dark");
    }
  }, []);

  const handleSetTheme = (newTheme: "dark" | "light") => {
    setTheme(newTheme);
    localStorage.setItem("aegis_theme", newTheme);
    document.documentElement.classList.toggle("dark", newTheme === "dark");
  };

  const triggerToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3000);
  };

  // Preset Selection
  const selectDish = (dish: string) => {
    if (dish === "masala_dosa") {
      setActiveDishName("Masala Dosa + Sambar");
      setCarbs(62); setFat(18); setProtein(10);
    } else if (dish === "chicken_biryani") {
      setActiveDishName("Chicken Biryani Plate");
      setCarbs(68); setFat(22); setProtein(32);
    } else if (dish === "rajma_chawal") {
      setActiveDishName("Rajma Chawal");
      setCarbs(72); setFat(14); setProtein(20);
    } else {
      setActiveDishName("Roti, Dal & Sabzi");
      setCarbs(48); setFat(12); setProtein(16);
    }
    triggerToast(`Loaded meal preset: ${activeDishName}`);
  };

  const applyCustomMeal = () => {
    setActiveDishName(customName);
    setCarbs(customCarbs);
    setFat(customFat);
    setProtein(customProtein);
    setIsCustomMealOpen(false);
    setActiveTab("whatif");
    triggerToast(`Applied custom meal: ${customName}`);
  };

  const handleDegradation = (deg: string) => {
    setDegradation(deg);
    if (deg === "D4" || deg === "D7") setReliability("LOW");
    else if (deg.startsWith("D1") || deg === "D3" || deg === "D2") setReliability("MODERATE");
    else setReliability("HIGH");
    triggerToast(`Stress test injected: ${deg}`);
  };

  // Command Palette Actions
  const actions: CommandAction[] = useMemo(() => [
    { id: "play", title: "Replay: Toggle Play / Pause Stream", cat: "Replay", key: "Space", run: () => setIsPlaying((p) => !p) },
    { id: "jump", title: "Replay: Jump to Next Clinical Meal", cat: "Replay", key: "N", run: () => triggerToast("Jumping to next clinical postprandial meal (+180m)") },
    { id: "p020", title: "Twin: Switch to P020 (Type 2 Diabetes, 58y)", cat: "Twin", key: "P20", run: () => { setPatientId("P020"); triggerToast("Switched active twin to P020"); } },
    { id: "p021", title: "Twin: Switch to P021 (Type 2 Diabetes, 61y)", cat: "Twin", key: "P21", run: () => { setPatientId("P021"); triggerToast("Switched active twin to P021"); } },
    { id: "p010", title: "Twin: Switch to P010 (Prediabetes, 48y)", cat: "Twin", key: "P10", run: () => { setPatientId("P010"); triggerToast("Switched active twin to P010"); } },
    { id: "p001", title: "Twin: Switch to P001 (Healthy Control, 28y)", cat: "Twin", key: "P01", run: () => { setPatientId("P001"); triggerToast("Switched active twin to P001"); } },
    { id: "preset_roti", title: "What-If: Roti, Dal & Sabzi", cat: "What-If", key: "R", run: () => { setActiveTab("whatif"); selectDish("roti_dal_sabzi"); } },
    { id: "preset_dosa", title: "What-If: Masala Dosa + Sambar", cat: "What-If", key: "D", run: () => { setActiveTab("whatif"); selectDish("masala_dosa"); } },
    { id: "preset_biryani", title: "What-If: Chicken Biryani", cat: "What-If", key: "B", run: () => { setActiveTab("whatif"); selectDish("chicken_biryani"); } },
    { id: "custom_modal", title: "What-If: Open Custom Meal Builder Modal", cat: "What-If", key: "+", run: () => setIsCustomMealOpen(true) },
    { id: "biomarkers_modal", title: "Twin: Edit Patient Biomarkers & Metabolic Panel", cat: "Twin", key: "M", run: () => openBiomarkersModal() },
    { id: "theme_light", title: "Theme: Switch to Light Theme", cat: "Theme", key: "L", run: () => handleSetTheme("light") },
    { id: "theme_dark", title: "Theme: Switch to Dark Theme", cat: "Theme", key: "D", run: () => handleSetTheme("dark") },
    { id: "deg_d0", title: "Stress: Nominal 5-Min Telemetry (D0)", cat: "Stress", key: "D0", run: () => handleDegradation("D0") },
    { id: "deg_d1", title: "Stress: 30m Signal Dropout (D1)", cat: "Stress", key: "D1", run: () => handleDegradation("D1_30m") },
    { id: "deg_d3", title: "Stress: No Wearable HR/METs (D3)", cat: "Stress", key: "D3", run: () => handleDegradation("D3") },
    { id: "tab_1", title: "View: 1. Overview & Forecast", cat: "View", key: "1", run: () => setActiveTab("forecast") },
    { id: "tab_2", title: "View: 2. What-If Meal Sandbox", cat: "View", key: "2", run: () => setActiveTab("whatif") },
    { id: "tab_3", title: "View: 3. Meal Timeline (Refero)", cat: "View", key: "3", run: () => setActiveTab("timeline") },
    { id: "tab_4", title: "View: 4. Digital Twin Phenotype", cat: "View", key: "4", run: () => setActiveTab("profile") },
    { id: "tab_5", title: "View: 5. Sensor Stress Audit", cat: "View", key: "5", run: () => setActiveTab("audit") },
    { id: "tab_6", title: "View: 6. Doctor AI Persona (Doctronic)", cat: "View", key: "6", run: () => setActiveTab("settings") },
  ], [isPlaying, patientId, patientDatabase]);

  const filteredActions = useMemo(() => {
    return actions.filter((a) =>
      a.title.toLowerCase().includes(paletteQuery.toLowerCase()) ||
      a.cat.toLowerCase().includes(paletteQuery.toLowerCase())
    );
  }, [actions, paletteQuery]);

  // Keyboard Shortcuts (Cmd+K, Space, N, 1-6)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setIsPaletteOpen((prev) => !prev);
        setPaletteQuery("");
        setPaletteIndex(0);
        return;
      }

      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLSelectElement) {
        if (e.key === "Escape") {
          setIsPaletteOpen(false);
          setIsCustomMealOpen(false);
          setIsBiomarkersModalOpen(false);
          setIsStylePopoverOpen(false);
          setMobileMenuOpen(false);
        }
        return;
      }

      if (e.key === "Escape") {
        setMobileMenuOpen(false);
      }

      if (isPaletteOpen) {
        if (e.key === "ArrowDown") {
          e.preventDefault();
          setPaletteIndex((prev) => (prev + 1) % (filteredActions.length || 1));
        } else if (e.key === "ArrowUp") {
          e.preventDefault();
          setPaletteIndex((prev) => (prev - 1 + (filteredActions.length || 1)) % (filteredActions.length || 1));
        } else if (e.key === "Enter") {
          e.preventDefault();
          if (filteredActions[paletteIndex]) {
            filteredActions[paletteIndex].run();
            setIsPaletteOpen(false);
          }
        } else if (e.key === "Escape") {
          setIsPaletteOpen(false);
        }
        return;
      }

      if (e.code === "Space") {
        e.preventDefault();
        setIsPlaying((prev) => !prev);
      } else if (e.code === "KeyN") {
        e.preventDefault();
        triggerToast("Jumping to next clinical postprandial meal (+180m)");
      } else if (e.key === "1") setActiveTab("forecast");
      else if (e.key === "2") setActiveTab("whatif");
      else if (e.key === "3") setActiveTab("timeline");
      else if (e.key === "4") setActiveTab("profile");
      else if (e.key === "5") setActiveTab("audit");
      else if (e.key === "6") setActiveTab("settings");
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isPlaying, isPaletteOpen, filteredActions, paletteIndex]);

  return (
    <div className="min-h-screen flex overflow-x-hidden font-sans bg-[var(--bg-canvas)] text-[var(--text-main)] transition-colors duration-200">
      
      {/* 1. LEFT MICRO-RAIL (Hidden on small mobile screens, 56px) */}
      <aside aria-label="Micro-Rail" className="hidden md:flex w-14 flex-shrink-0 flex-col items-center justify-between py-3.5 border-r border-[var(--border-main)] bg-[var(--bg-micro)] z-50">
        <div className="flex flex-col items-center gap-4">
          <div className="w-8 h-8 rounded-lg bg-slate-900 dark:bg-white text-white dark:text-slate-900 flex items-center justify-center shadow-xs cursor-pointer" title="Aegis Twin Suite">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2.2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 2L3 7v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-9-5z" />
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6m0 0l3 3m-3-3l-3 3" />
            </svg>
          </div>

          <div className="w-7 h-px bg-[var(--border-main)] my-1"></div>

          <button onClick={() => setActiveTab("forecast")} className={`p-2 rounded-lg transition ${activeTab === "forecast" ? "text-[var(--text-main)] bg-[var(--bg-card)] shadow-xs font-semibold" : "text-[var(--text-secondary)] hover:text-[var(--text-main)]"}`} title="Activity & Trajectory Forecast">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/></svg>
          </button>

          <button onClick={() => setActiveTab("whatif")} className={`p-2 rounded-lg transition ${activeTab === "whatif" ? "text-[var(--text-main)] bg-[var(--bg-card)] shadow-xs font-semibold" : "text-[var(--text-secondary)] hover:text-[var(--text-main)]"}`} title="What-If Counterfactual Sandbox">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"/></svg>
          </button>

          <button onClick={() => setActiveTab("timeline")} className={`p-2 rounded-lg transition ${activeTab === "timeline" ? "text-[var(--text-main)] bg-[var(--bg-card)] shadow-xs font-semibold" : "text-[var(--text-secondary)] hover:text-[var(--text-main)]"}`} title="Chronological Meal Timeline (Refero)">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>
          </button>

          <button onClick={() => setActiveTab("profile")} className={`p-2 rounded-lg transition ${activeTab === "profile" ? "text-[var(--text-main)] bg-[var(--bg-card)] shadow-xs font-semibold" : "text-[var(--text-secondary)] hover:text-[var(--text-main)]"}`} title="Patient Digital Twin Phenotype">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/></svg>
          </button>

          <button onClick={() => setActiveTab("audit")} className={`p-2 rounded-lg transition ${activeTab === "audit" ? "text-[var(--text-main)] bg-[var(--bg-card)] shadow-xs font-semibold" : "text-[var(--text-secondary)] hover:text-[var(--text-main)]"}`} title="Sensor Stress-Test Studio">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/></svg>
          </button>

          <button onClick={() => setActiveTab("settings")} className={`p-2 rounded-lg transition ${activeTab === "settings" ? "text-[var(--text-main)] bg-[var(--bg-card)] shadow-xs font-semibold" : "text-[var(--text-secondary)] hover:text-[var(--text-main)]"}`} title="AI Doctor Persona & Settings (Doctronic)">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
          </button>
        </div>

        <div className="flex flex-col items-center gap-3">
          <button onClick={() => setIsPaletteOpen(true)} className="p-2 rounded-lg text-[var(--text-secondary)] hover:text-[var(--text-main)] transition" title="Search Actions (⌘K)">
            <kbd className="font-mono text-[10px] bg-[var(--bg-card)] border border-[var(--border-main)] px-1 py-0.5 rounded">⌘K</kbd>
          </button>
          <div className="w-8 h-8 rounded-full bg-slate-300 dark:bg-slate-700 border border-[var(--border-main)] flex items-center justify-center text-xs font-semibold text-[var(--text-main)]" title="Dr. Connie (Lead Endocrinologist)">
            DC
          </div>
        </div>
      </aside>

      {/* Mobile Drawer Overlay */}
      {mobileMenuOpen && (
        <div
          onClick={() => setMobileMenuOpen(false)}
          className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs z-[35] lg:hidden cursor-pointer"
          style={{ zIndex: 35 }}
          aria-label="Close sidebar overlay"
        />
      )}

      {/* 2. EXPANDED SIDEBAR NAVIGATION (Auto-collapsible on screens < lg) */}
      <aside
        ref={sidebarRef}
        aria-label="Sidebar"
        className={`${
          mobileMenuOpen ? "flex fixed inset-y-0 left-0 w-64 shadow-2xl z-40" : "hidden lg:flex w-60 z-40"
        } flex-shrink-0 flex-col border-r border-[var(--border-main)] bg-[var(--bg-sidebar)] transition-all duration-200`}
      >
        
        {/* Workspace / Twin Selector */}
        <div className="p-3.5 border-b border-[var(--border-main)]">
          <div className="flex items-center justify-between text-xs font-medium text-[var(--text-secondary)] mb-1.5">
            <div className="flex items-center gap-1.5">
              <span className="w-4 h-4 rounded bg-slate-900 dark:bg-white text-white dark:text-slate-900 flex items-center justify-center text-[9px] font-bold">Æ</span>
              <span>Twin Workspace</span>
            </div>
            <span className="text-[10px] text-[var(--text-muted)] font-mono">v1.1</span>
          </div>
          <select
            value={patientId}
            onChange={(e) => { setPatientId(e.target.value); triggerToast(`Switched active twin to ${e.target.value}`); }}
            className="w-full bg-[var(--bg-card-subtle)] border border-[var(--border-main)] text-[var(--text-main)] rounded-lg px-2.5 py-1.5 text-xs font-semibold outline-none focus:border-slate-900 dark:focus:border-slate-100 cursor-pointer"
          >
            <option value="P020">P020 — T2D (58y, HbA1c 7.4%)</option>
            <option value="P021">P021 — T2D (61y, HbA1c 7.8%)</option>
            <option value="P010">P010 — Prediabetes (48y, 6.0%)</option>
            <option value="P001">P001 — Healthy Control (28y)</option>
          </select>
        </div>

        {/* Search Bar */}
        <div className="px-3 py-2.5 border-b border-[var(--border-main)]">
          <div onClick={() => setIsPaletteOpen(true)} className="flex items-center justify-between px-2.5 py-1.5 rounded-lg border border-[var(--border-main)] bg-[var(--bg-card-subtle)] text-[var(--text-secondary)] hover:text-[var(--text-main)] text-xs cursor-pointer">
            <div className="flex items-center gap-2">
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
              <span>Search telemetry...</span>
            </div>
            <kbd className="font-mono text-[10px] bg-[var(--bg-card)] px-1 rounded border border-[var(--border-main)]">⌘K</kbd>
          </div>
        </div>

        {/* Sidebar Nav Items */}
        <nav className="flex-1 overflow-y-auto px-2.5 py-3 space-y-4 text-xs font-medium">
          
          <div>
            <div className="px-2 py-1 text-[11px] font-semibold uppercase tracking-wider text-[var(--text-muted)]">
              Clinical Monitoring
            </div>
            <div className="mt-1 space-y-0.5">
              <button
                onClick={() => handleSelectTab("forecast")}
                className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-left transition ${
                  activeTab === "forecast" ? "bg-[var(--nav-active-bg)] text-[var(--nav-active-text)] font-semibold" : "text-[var(--text-secondary)] hover:text-[var(--text-main)] hover:bg-[var(--bg-card-subtle)]"
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/></svg>
                  <span>Activity &amp; Forecast</span>
                </div>
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
              </button>

              <button
                onClick={() => handleSelectTab("timeline")}
                className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-left transition ${
                  activeTab === "timeline" ? "bg-[var(--nav-active-bg)] text-[var(--nav-active-text)] font-semibold" : "text-[var(--text-secondary)] hover:text-[var(--text-main)] hover:bg-[var(--bg-card-subtle)]"
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>
                  <span>Meal Timeline</span>
                </div>
                <span className="text-[10px] text-[var(--text-muted)] font-mono">Refero</span>
              </button>

              <button
                onClick={() => handleSelectTab("profile")}
                className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-left transition ${
                  activeTab === "profile" ? "bg-[var(--nav-active-bg)] text-[var(--nav-active-text)] font-semibold" : "text-[var(--text-secondary)] hover:text-[var(--text-main)] hover:bg-[var(--bg-card-subtle)]"
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/></svg>
                  <span>Twin Phenotype</span>
                </div>
                <span className="text-[10px] text-emerald-600 dark:text-emerald-400 font-mono">K=5</span>
              </button>
            </div>
          </div>

          <div>
            <div className="px-2 py-1 text-[11px] font-semibold uppercase tracking-wider text-[var(--text-muted)]">
              Counterfactual Lab
            </div>
            <div className="mt-1 space-y-0.5">
              <button
                onClick={() => handleSelectTab("whatif")}
                className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-left transition ${
                  activeTab === "whatif" ? "bg-[var(--nav-active-bg)] text-[var(--nav-active-text)] font-semibold" : "text-[var(--text-secondary)] hover:text-[var(--text-main)] hover:bg-[var(--bg-card-subtle)]"
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"/></svg>
                  <span>What-If Sandbox</span>
                </div>
                <span className="text-[10px] bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 border border-slate-300 dark:border-slate-700 px-1 rounded">Sim</span>
              </button>

              <button
                onClick={() => { setIsCustomMealOpen(true); setMobileMenuOpen(false); }}
                className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-left transition text-[var(--text-secondary)] hover:text-[var(--text-main)] hover:bg-[var(--bg-card-subtle)]"
              >
                <div className="flex items-center gap-2.5">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4"/></svg>
                  <span>Add Custom Meal</span>
                </div>
                <kbd className="font-mono text-[10px] text-[var(--text-muted)]">+</kbd>
              </button>
            </div>
          </div>

          <div>
            <div className="px-2 py-1 text-[11px] font-semibold uppercase tracking-wider text-[var(--text-muted)]">
              Audit &amp; Intelligence
            </div>
            <div className="mt-1 space-y-0.5">
              <button
                onClick={() => handleSelectTab("audit")}
                className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-left transition ${
                  activeTab === "audit" ? "bg-[var(--nav-active-bg)] text-[var(--nav-active-text)] font-semibold" : "text-[var(--text-secondary)] hover:text-[var(--text-main)] hover:bg-[var(--bg-card-subtle)]"
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/></svg>
                  <span>Sensor Quality D0–D7</span>
                </div>
                <span className="text-[10px] text-emerald-600 dark:text-emerald-400 font-mono">High</span>
              </button>

              <button
                onClick={() => handleSelectTab("settings")}
                className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-left transition ${
                  activeTab === "settings" ? "bg-[var(--nav-active-bg)] text-[var(--nav-active-text)] font-semibold" : "text-[var(--text-secondary)] hover:text-[var(--text-main)] hover:bg-[var(--bg-card-subtle)]"
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                  <span>AI Doctor Persona</span>
                </div>
                <span className="text-[10px] bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 px-1 rounded">Doctronic</span>
              </button>
            </div>
          </div>

        </nav>

        <div className="p-3 border-t border-[var(--border-main)] flex items-center justify-between text-[11px] text-[var(--text-muted)]">
          <span>Candidate S Model</span>
          <span className="font-mono text-emerald-600 dark:text-emerald-400 font-medium">Split-Conformal 90%</span>
        </div>

      </aside>

      {/* 3. MAIN WORKSPACE CANVAS */}
      <div className="flex-1 flex flex-col min-w-0 min-h-screen">
        
        {/* Top Header Bar */}
        <header className="sticky top-0 z-30 bg-[var(--bg-card)] border-b border-[var(--border-main)] px-6 py-2.5 transition-colors duration-200">
          <div className="max-w-[1600px] mx-auto flex flex-wrap items-center justify-between gap-4">
            
            <div className="flex items-center gap-2 text-xs">
              <button
                id="mobileSidebarToggle"
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="lg:hidden p-1.5 rounded-lg border border-[var(--border-main)] bg-[var(--bg-card)] text-[var(--text-main)] hover:bg-[var(--bg-card-subtle)] mr-1 transition"
                aria-label="Toggle navigation"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>
              <span className="text-[var(--text-secondary)]">Aegis Twin Suite</span>
              <span className="text-[var(--border-subtle)]">/</span>
              <span className="font-semibold text-[var(--text-main)]">
                {activeTab === "forecast" ? "Activity & Trajectory Forecast" :
                 activeTab === "whatif" ? "Counterfactual Meal Sandbox" :
                 activeTab === "timeline" ? "Chronological Meal Timeline" :
                 activeTab === "profile" ? "Patient Digital Twin Phenotype" :
                 activeTab === "audit" ? "Sensor Quality & Stress Testing" :
                 "Doctor AI Persona & Settings"}
              </span>
              <span className="text-[11px] px-2 py-0.2 rounded font-mono font-medium bg-[var(--bg-card-subtle)] text-[var(--text-secondary)] border border-[var(--border-main)]">
                Candidate S
              </span>
            </div>

            <div className="flex items-center gap-3 text-xs">
              
              {/* Replay Playback Transport */}
              <div className="flex items-center gap-1.5 p-1 rounded-lg border border-[var(--border-main)] bg-[var(--bg-card-subtle)]">
                <button
                  onClick={() => { setIsPlaying((p) => !p); triggerToast(!isPlaying ? "Telemetry stream playback active" : "Telemetry playback paused"); }}
                  className="px-2.5 py-1 rounded-md bg-[var(--bg-card)] text-[var(--text-main)] font-semibold shadow-sm flex items-center gap-1.5 transition"
                >
                  <span>{isPlaying ? "⏸" : "▶"}</span>
                  <span>{isPlaying ? "Pause" : "Play"}</span>
                  <kbd className="font-mono text-[10px] text-[var(--text-muted)]">Space</kbd>
                </button>
                <button
                  onClick={() => triggerToast("Jumping to next clinical postprandial meal (+180m)")}
                  className="px-2.5 py-1 rounded-md hover:bg-[var(--bg-card)] text-[var(--text-secondary)] hover:text-[var(--text-main)] flex items-center gap-1 transition"
                >
                  <span>Next Meal</span>
                  <kbd className="font-mono text-[10px] text-[var(--text-muted)]">N</kbd>
                </button>
                <div className="h-3.5 w-px bg-[var(--border-main)]"></div>
                <select
                  value={speed}
                  onChange={(e) => { setSpeed(Number(e.target.value)); triggerToast(`Replay speed set to ${e.target.value}x`); }}
                  className="bg-transparent text-[var(--text-main)] font-mono font-medium text-xs outline-none cursor-pointer"
                >
                  <option value={1}>1x</option>
                  <option value={5}>5x</option>
                  <option value={10}>10x</option>
                  <option value={20}>20x</option>
                </select>
              </div>

              {/* Dark & Light Segmented Switch */}
              <div className="flex items-center p-0.5 rounded-lg border border-[var(--border-main)] bg-[var(--bg-canvas)]">
                <button
                  onClick={() => handleSetTheme("light")}
                  className={`px-2.5 py-1 rounded-md text-xs font-medium flex items-center gap-1.5 transition ${
                    theme === "light" ? "bg-[var(--bg-card)] text-[var(--text-main)] shadow-sm font-semibold" : "text-[var(--text-secondary)] hover:text-[var(--text-main)]"
                  }`}
                  title="Switch to Light mode"
                >
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"/></svg>
                  <span>Light</span>
                </button>
                <button
                  onClick={() => handleSetTheme("dark")}
                  className={`px-2.5 py-1 rounded-md text-xs font-medium flex items-center gap-1.5 transition ${
                    theme === "dark" ? "bg-[var(--bg-card)] text-[var(--text-main)] shadow-sm font-semibold" : "text-[var(--text-secondary)] hover:text-[var(--text-main)]"
                  }`}
                  title="Switch to Dark mode"
                >
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"/></svg>
                  <span>Dark</span>
                </button>
              </div>

            </div>

          </div>
        </header>

        {/* Floating Doctronic Toast Notification */}
        {toastMessage && (
          <div className="fixed top-14 right-8 z-50 transition-all duration-300">
            <div className="flex items-center gap-2.5 px-4 py-2.5 rounded-full shadow-lg border border-blue-200 dark:border-blue-900 bg-blue-50 dark:bg-blue-950/90 text-blue-800 dark:text-blue-200 text-xs font-medium">
              <svg className="w-4 h-4 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
              <span>{toastMessage}</span>
            </div>
          </div>
        )}

        {/* Main Body */}
        <main className="flex-1 p-6 max-w-[1600px] w-full mx-auto space-y-6">
          
          {/* OpenRouter Dismissible Clinical Banner */}
          <section className="p-4 rounded-xl border border-blue-500/20 bg-blue-500/5 dark:bg-blue-950/20 flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-blue-600/10 border border-blue-500/30 flex items-center justify-center text-blue-600 dark:text-blue-400 font-bold text-xs">
                G2
              </div>
              <div>
                <div className="text-xs font-semibold text-[var(--text-main)]">
                  Candidate S Digital Twin Research Prototype (Dual-Gamma Absorption)
                </div>
                <div className="text-[11px] text-[var(--text-secondary)]">
                  Calibrated with 90% Split-Conformal intervals and Ridge K=5 personalization. <strong>Not medical advice and not suitable for treatment decisions.</strong>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button onClick={() => setActiveTab("audit")} className="px-3 py-1 rounded-lg bg-[var(--bg-card)] border border-[var(--border-main)] text-xs font-medium text-[var(--text-main)] hover:border-[var(--border-subtle)] transition">
                View Conformal Audit
              </button>
            </div>
          </section>

          {/* OpenRouter Page Title & Underline Tabs */}
          <div className="border-b border-[var(--border-main)] pb-0">
            <div className="flex flex-wrap items-end justify-between gap-4 mb-4">
              <div>
                <h1 className="text-2xl font-bold tracking-tight text-[var(--text-main)]">
                  {activeTab === "forecast" ? "Activity" :
                   activeTab === "whatif" ? "What-If Simulation" :
                   activeTab === "timeline" ? "Meal Excursions Timeline" :
                   activeTab === "profile" ? "Patient Profile" :
                   activeTab === "audit" ? "Resilience Audit" :
                   "AI Doctor Persona"}
                </h1>
                <p className="text-xs text-[var(--text-secondary)] mt-0.5">
                  {activeTab === "forecast" ? "Continuous 180-min postprandial glycemic digital twin telemetry across patient models" :
                   activeTab === "whatif" ? "Test nutritional substitutions, portion scaling, and behavioral exercise timing" :
                   activeTab === "timeline" ? "Historical postprandial sessions with macronutrient ratios and glycemic envelopes" :
                   activeTab === "profile" ? "Clinical baseline, synthetic EHR comorbidities, and few-shot Ridge K=5 adapted weights" :
                   activeTab === "audit" ? "Validate digital twin fidelity across realistic packet dropouts (D0–D7)" :
                   "Customize clinical communication tone, telemetry memory, and physician consent preferences"}
                </p>
              </div>
              
              <div className="flex items-center gap-2 text-xs">
                <span className="px-2.5 py-1 rounded-md border border-[var(--border-main)] bg-[var(--bg-card)] text-[var(--text-secondary)] font-mono">
                  🌐 GMT+5:30
                </span>
                <span className="px-2.5 py-1 rounded-md border border-[var(--border-main)] bg-[var(--bg-card)] text-[var(--text-main)] font-medium">
                  Past 180-Min Excursion ▾
                </span>
              </div>
            </div>

            <div className="flex items-center gap-8 text-xs">
              <button onClick={() => setActiveTab("forecast")} className={`tab-underline ${activeTab === "forecast" ? "active" : ""}`}>
                Overview &amp; Forecast
              </button>
              <button onClick={() => setActiveTab("whatif")} className={`tab-underline ${activeTab === "whatif" ? "active" : ""}`}>
                What-If Sandbox
              </button>
              <button onClick={() => setActiveTab("timeline")} className={`tab-underline ${activeTab === "timeline" ? "active" : ""}`}>
                Meal Timeline (Refero)
              </button>
              <button onClick={() => setActiveTab("profile")} className={`tab-underline ${activeTab === "profile" ? "active" : ""}`}>
                Patient Phenotype
              </button>
              <button onClick={() => setActiveTab("audit")} className={`tab-underline ${activeTab === "audit" ? "active" : ""}`}>
                Sensor Stress Audit
              </button>
              <button onClick={() => setActiveTab("settings")} className={`tab-underline ${activeTab === "settings" ? "active" : ""}`}>
                Doctor AI Persona (Doctronic)
              </button>
            </div>
          </div>

          {/* TAB 1: OVERVIEW & FORECAST */}
          {activeTab === "forecast" && (
            <div className="space-y-6">
              
              {/* 5-Column Bento KPI Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3.5">
                <div className="clean-card p-4 space-y-2">
                  <div className="flex items-center justify-between text-xs text-[var(--text-secondary)]">
                    <span>Current CGM</span>
                    <span className="px-1.5 py-0.2 rounded text-[10px] font-mono font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">IN RANGE</span>
                  </div>
                  <div className="flex items-baseline justify-between">
                    <div>
                      <span className="text-2xl font-bold font-mono tracking-tight text-[var(--text-main)]">{liveGlucose}</span>
                      <span className="text-xs text-[var(--text-secondary)] ml-1">mg/dL</span>
                    </div>
                    <svg className="w-16 h-6 text-emerald-500" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 64 24"><path strokeLinecap="round" strokeLinejoin="round" d="M2 18 L16 14 L30 16 L44 8 L62 4" /></svg>
                  </div>
                  <div className="text-[11px] text-[var(--text-muted)] font-mono flex items-center justify-between pt-1 border-t border-[var(--border-main)]">
                    <span className="text-emerald-600 dark:text-emerald-400">↗ +1.2 mg/dL/min</span>
                    <span>Dexcom G6</span>
                  </div>
                </div>

                <div className="clean-card p-4 space-y-2">
                  <div className="flex items-center justify-between text-xs text-[var(--text-secondary)]">
                    <span>Resting HR</span>
                    <span className="px-1.5 py-0.2 rounded text-[10px] font-mono text-[var(--text-secondary)] bg-[var(--bg-card-subtle)]">NORMAL</span>
                  </div>
                  <div className="flex items-baseline justify-between">
                    <div>
                      <span className="text-2xl font-bold font-mono tracking-tight text-[var(--text-main)]">{liveHR}</span>
                      <span className="text-xs text-[var(--text-secondary)] ml-1">bpm</span>
                    </div>
                    <svg className="w-16 h-6 text-slate-800 dark:text-slate-200" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 64 24"><path strokeLinecap="round" strokeLinejoin="round" d="M2 12 L16 12 L22 4 L28 20 L34 8 L40 12 L62 12" /></svg>
                  </div>
                  <div className="text-[11px] text-[var(--text-muted)] flex items-center justify-between pt-1 border-t border-[var(--border-main)]">
                    <span>Baseline: 68 bpm</span>
                    <span>Optical PPG</span>
                  </div>
                </div>

                <div className="clean-card p-4 space-y-2">
                  <div className="flex items-center justify-between text-xs text-[var(--text-secondary)]">
                    <span>Physical Activity</span>
                    <span className="px-1.5 py-0.2 rounded text-[10px] font-mono text-[var(--text-secondary)] bg-[var(--bg-card-subtle)]">SEDENTARY</span>
                  </div>
                  <div className="flex items-baseline justify-between">
                    <div>
                      <span className="text-2xl font-bold font-mono tracking-tight text-[var(--text-main)]">{liveMETs.toFixed(2)}</span>
                      <span className="text-xs text-[var(--text-secondary)] ml-1">METs</span>
                    </div>
                    <svg className="w-16 h-6 text-slate-800 dark:text-slate-200" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 64 24"><path strokeLinecap="round" strokeLinejoin="round" d="M2 20 L20 18 L38 20 L50 16 L62 18" /></svg>
                  </div>
                  <div className="text-[11px] text-[var(--text-muted)] flex items-center justify-between pt-1 border-t border-[var(--border-main)]">
                    <span>Desk / Resting</span>
                    <span>Accelerometry</span>
                  </div>
                </div>

                <div className="clean-card p-4 space-y-2">
                  <div className="flex items-center justify-between text-xs text-[var(--text-secondary)]">
                    <span>Time in Range (TIR)</span>
                    <span className="text-[10px] font-mono text-[var(--text-muted)]">GMI: 6.8%</span>
                  </div>
                  <div className="flex items-baseline justify-between">
                    <div>
                      <span className="text-2xl font-bold font-mono tracking-tight text-slate-900 dark:text-slate-100">78%</span>
                      <span className="text-xs text-[var(--text-muted)] ml-1">(&ge;70%)</span>
                    </div>
                    <span className="text-[11px] font-mono text-slate-900 dark:text-slate-100 font-semibold">OPTIMAL</span>
                  </div>
                  <div className="w-full h-1.5 rounded-full overflow-hidden flex bg-[var(--border-main)] mt-1">
                    <div className="bg-slate-900 dark:bg-slate-100 h-full" style={{ width: "78%" }}></div>
                    <div className="bg-slate-400 dark:bg-slate-500 h-full" style={{ width: "18%" }}></div>
                    <div className="bg-slate-200 dark:bg-slate-700 h-full" style={{ width: "4%" }}></div>
                  </div>
                </div>

                <div className="clean-card p-4 space-y-2">
                  <div className="flex items-center justify-between text-xs text-[var(--text-secondary)]">
                    <span>Candidate S Peak</span>
                    <span className="px-1.5 py-0.2 rounded text-[10px] font-mono font-semibold text-slate-900 dark:text-slate-100 bg-slate-100 dark:bg-slate-800">INFERENCE</span>
                  </div>
                  <div className="flex items-baseline justify-between">
                    <div>
                      <span className="text-2xl font-bold font-mono tracking-tight text-[var(--text-main)]">164.2</span>
                      <span className="text-xs text-[var(--text-secondary)] ml-1">mg/dL</span>
                    </div>
                    <span className="text-[11px] font-mono text-slate-500">+55m</span>
                  </div>
                  <div className="text-[11px] text-[var(--text-muted)] flex items-center justify-between pt-1 border-t border-[var(--border-main)]">
                    <span>Target &lt; 180</span>
                    <span className="text-slate-900 dark:text-slate-100 font-semibold">PASS</span>
                  </div>
                </div>
              </div>

              {/* Trajectory Display */}
              <div className="clean-card p-6 space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[var(--border-main)] pb-3">
                  <div>
                    <div className="flex items-center gap-2.5">
                      <h2 className="text-base font-semibold text-[var(--text-main)]">180-Minute Postprandial Glycemic Forecast</h2>
                      <span className="px-2 py-0.2 rounded text-[11px] font-mono font-semibold bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100 border border-slate-300 dark:border-slate-700">
                        {reliability} CONFIDENCE
                      </span>
                    </div>
                    <p className="text-xs text-[var(--text-secondary)] mt-0.5">
                      Dual-gamma neural model with 90% split-conformal uncertainty intervals and real recorded sensor ground truth overlay
                    </p>
                  </div>

                  <div className="flex flex-wrap items-center gap-3.5 text-xs">
                    <span className="flex items-center gap-1.5 text-[var(--text-secondary)]">
                      <span className="w-3 h-0.5 bg-slate-900 dark:bg-slate-100 inline-block"></span> Candidate S Prediction
                    </span>
                    <span className="flex items-center gap-1.5 text-[var(--text-secondary)]">
                      <span className="w-3 h-0.5 border-b-2 border-dashed border-slate-600 dark:border-slate-300 inline-block"></span> Recorded CGM Truth
                    </span>
                    <span className="flex items-center gap-1.5 text-[var(--text-secondary)]">
                      <span className="w-3 h-2 bg-slate-200 dark:bg-slate-700 border border-slate-400 dark:border-slate-600 rounded-xs inline-block"></span> 90% Conformal Band
                    </span>
                  </div>
                </div>

                <div className="flex flex-wrap items-center justify-between px-3.5 py-1.5 rounded-lg bg-[var(--bg-card-subtle)] border border-[var(--border-main)] text-xs font-mono text-[var(--text-secondary)]">
                  <div className="flex items-center gap-3">
                    <span>Scrubber:</span>
                    <span className="font-semibold text-[var(--text-main)]">+55 min</span>
                    <span className="text-[var(--border-subtle)]">|</span>
                    <span className="text-slate-900 dark:text-slate-100 font-semibold">Pred: 164.2 mg/dL</span>
                    <span className="text-[var(--border-subtle)]">|</span>
                    <span>90% Bounds: [150.2 – 178.2]</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-slate-800 dark:text-slate-200 font-semibold">Truth: 162.0 mg/dL</span>
                    <span className="text-[var(--text-muted)]">(Δ -2.2)</span>
                  </div>
                </div>

                <div className="h-80 w-full bg-[var(--bg-canvas)] rounded-xl border border-[var(--border-main)] p-4 flex flex-col justify-between">
                  <div className="flex justify-between items-center text-xs text-slate-700 dark:text-slate-300 font-mono border-b border-slate-200 dark:border-slate-800 pb-1">
                    <span>Hyperglycemia Threshold (180 mg/dL)</span>
                    <span className="px-1.5 py-0.2 rounded bg-slate-100 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-[10px]">ADA Target &lt; 180</span>
                  </div>
                  <div className="flex-1 flex items-center justify-center text-center">
                    <div className="space-y-1">
                      <span className="text-sm font-semibold text-[var(--text-main)] block">Candidate S PyTorch Streaming Active</span>
                      <span className="text-xs text-[var(--text-secondary)] block max-w-lg mx-auto">
                        5-minute interval streaming from parquet engine with Ridge K=5 adapted weights.
                      </span>
                    </div>
                  </div>
                  <div className="flex justify-between text-xs text-[var(--text-muted)] font-mono border-t border-[var(--border-main)] pt-2">
                    <span>0m</span>
                    <span>30m</span>
                    <span>60m (Peak)</span>
                    <span>90m</span>
                    <span>120m</span>
                    <span>180m</span>
                  </div>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-2 border-t border-[var(--border-main)]">
                  <div className="bg-[var(--bg-card-subtle)] p-3 rounded-lg border border-[var(--border-main)] text-center">
                    <span className="text-xs text-[var(--text-secondary)] block mb-0.5">Predicted Peak Excursion</span>
                    <span className="text-xl font-bold font-mono text-[var(--text-main)]">164.2 mg/dL</span>
                    <span className="text-[11px] text-emerald-600 dark:text-emerald-400 block mt-0.5">Within Target</span>
                  </div>
                  <div className="bg-[var(--bg-card-subtle)] p-3 rounded-lg border border-[var(--border-main)] text-center">
                    <span className="text-xs text-[var(--text-secondary)] block mb-0.5">Time to Peak</span>
                    <span className="text-xl font-bold font-mono text-[var(--text-main)]">55 min</span>
                    <span className="text-[11px] text-[var(--text-muted)] block mt-0.5">Absorption Kinetics</span>
                  </div>
                  <div className="bg-[var(--bg-card-subtle)] p-3 rounded-lg border border-[var(--border-main)] text-center">
                    <span className="text-xs text-[var(--text-secondary)] block mb-0.5">Late Lipid Mean (120–180m)</span>
                    <span className="text-xl font-bold font-mono text-sky-600 dark:text-sky-400">138.4 mg/dL</span>
                    <span className="text-[11px] text-[var(--text-muted)] block mt-0.5">Sustained Plateau</span>
                  </div>
                  <div className="bg-[var(--bg-card-subtle)] p-3 rounded-lg border border-[var(--border-main)] text-center">
                    <span className="text-xs text-[var(--text-secondary)] block mb-0.5">Time Above 180</span>
                    <span className="text-xl font-bold font-mono text-emerald-600 dark:text-emerald-400">0 min (0%)</span>
                    <span className="text-[11px] text-emerald-600 dark:text-emerald-400 block mt-0.5">Clinical Safety</span>
                  </div>
                </div>
              </div>

            </div>
          )}

          {/* TAB 2: WHAT-IF MEAL SANDBOX */}
          {activeTab === "whatif" && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                
                <div className="lg:col-span-5 clean-card p-6 space-y-5">
                  <div className="border-b border-[var(--border-main)] pb-3 flex items-center justify-between">
                    <div>
                      <h2 className="text-base font-semibold text-[var(--text-main)]">What-If Counterfactual Sandbox</h2>
                      <p className="text-xs text-[var(--text-secondary)] mt-0.5">Simulate modified carbohydrate, fat, protein, or exercise interventions</p>
                    </div>
                    <button onClick={() => setIsCustomMealOpen(true)} className="px-2.5 py-1 rounded-lg border border-[var(--border-main)] bg-[var(--bg-card-subtle)] text-xs font-medium text-[var(--text-main)] hover:border-[var(--border-subtle)] transition">
                      + Custom Meal
                    </button>
                  </div>

                  <div className="space-y-2">
                    <label className="text-xs font-semibold uppercase tracking-wider text-[var(--text-secondary)] block">
                      Regional Indian Clinical Presets:
                    </label>
                    <div className="grid grid-cols-2 gap-2">
                      <button onClick={() => selectDish("roti_dal_sabzi")} className={`text-left p-3 rounded-lg border transition ${activeDishName.includes("Roti") ? "border-slate-900 dark:border-slate-100 bg-slate-100 dark:bg-slate-800" : "border-[var(--border-main)] bg-[var(--bg-card-subtle)]"}`}>
                        <div className="text-xs font-medium text-[var(--text-main)]">Roti, Dal &amp; Sabzi</div>
                        <div className="text-[11px] text-[var(--text-secondary)] mt-0.5">48g C • 12g F • 16g P</div>
                      </button>
                      <button onClick={() => selectDish("masala_dosa")} className={`text-left p-3 rounded-lg border transition ${activeDishName.includes("Dosa") ? "border-slate-900 dark:border-slate-100 bg-slate-100 dark:bg-slate-800" : "border-[var(--border-main)] bg-[var(--bg-card-subtle)]"}`}>
                        <div className="text-xs font-medium text-[var(--text-main)]">Masala Dosa + Sambar</div>
                        <div className="text-[11px] text-[var(--text-secondary)] mt-0.5">62g C • 18g F • 10g P</div>
                      </button>
                      <button onClick={() => selectDish("chicken_biryani")} className={`text-left p-3 rounded-lg border transition ${activeDishName.includes("Biryani") ? "border-slate-900 dark:border-slate-100 bg-slate-100 dark:bg-slate-800" : "border-[var(--border-main)] bg-[var(--bg-card-subtle)]"}`}>
                        <div className="text-xs font-medium text-[var(--text-main)]">Chicken Biryani</div>
                        <div className="text-[11px] text-[var(--text-secondary)] mt-0.5">68g C • 22g F • 32g P</div>
                      </button>
                      <button onClick={() => selectDish("rajma_chawal")} className={`text-left p-3 rounded-lg border transition ${activeDishName.includes("Rajma") ? "border-slate-900 dark:border-slate-100 bg-slate-100 dark:bg-slate-800" : "border-[var(--border-main)] bg-[var(--bg-card-subtle)]"}`}>
                        <div className="text-xs font-medium text-[var(--text-main)]">Rajma Chawal</div>
                        <div className="text-[11px] text-[var(--text-secondary)] mt-0.5">72g C • 14g F • 20g P</div>
                      </button>
                    </div>
                  </div>

                  <div className="bg-[var(--bg-card-subtle)] p-3 rounded-lg border border-[var(--border-main)] space-y-2">
                    <div className="flex justify-between text-xs text-[var(--text-main)]">
                      <span className="font-semibold">{activeDishName}</span>
                      <span className="font-mono font-semibold">{totalKcal} kcal</span>
                    </div>
                    <div className="w-full h-2 rounded-full overflow-hidden flex bg-[var(--border-main)]">
                      <div className="bg-slate-900 dark:bg-slate-100 h-full transition-all duration-300" style={{ width: `${cPct}%` }}></div>
                      <div className="bg-slate-600 dark:bg-slate-400 h-full transition-all duration-300" style={{ width: `${pPct}%` }}></div>
                      <div className="bg-slate-400 dark:bg-slate-600 h-full transition-all duration-300" style={{ width: `${fPct}%` }}></div>
                    </div>
                    <div className="flex justify-between text-[11px] font-mono text-[var(--text-secondary)]">
                      <span>Carbs ({cPct}%)</span>
                      <span>Protein ({pPct}%)</span>
                      <span>Fat ({fPct}%)</span>
                    </div>
                  </div>

                  <div className="space-y-4 pt-1">
                    <div>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-[var(--text-secondary)] font-medium">Carbohydrates</span>
                        <span className="font-mono font-semibold text-[var(--text-main)]">{carbs} g</span>
                      </div>
                      <input type="range" min={10} max={140} value={carbs} onChange={(e) => setCarbs(Number(e.target.value))} className="w-full accent-slate-900 dark:accent-slate-100" />
                    </div>

                    <div>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-[var(--text-secondary)] font-medium">Dietary Fat</span>
                        <span className="font-mono font-semibold text-[var(--text-main)]">{fat} g</span>
                      </div>
                      <input type="range" min={0} max={60} value={fat} onChange={(e) => setFat(Number(e.target.value))} className="w-full accent-slate-900 dark:accent-slate-100" />
                    </div>

                    <div>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-[var(--text-secondary)] font-medium">Protein</span>
                        <span className="font-mono font-semibold text-[var(--text-main)]">{protein} g</span>
                      </div>
                      <input type="range" min={0} max={60} value={protein} onChange={(e) => setProtein(Number(e.target.value))} className="w-full accent-slate-900 dark:accent-slate-100" />
                    </div>

                    <div>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-[var(--text-secondary)] font-medium">Portion Scaling</span>
                        <span className="font-mono font-semibold text-[var(--text-main)]">{portion}%</span>
                      </div>
                      <input type="range" min={25} max={200} step={25} value={portion} onChange={(e) => setPortion(Number(e.target.value))} className="w-full accent-slate-900 dark:accent-slate-100" />
                    </div>

                    <div>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-[var(--text-secondary)] font-medium">Portion Estimation Uncertainty (±δ)</span>
                        <span className="font-mono font-semibold text-[var(--text-main)]">
                          {portionUncertainty === 0 ? "±0% (Nominal)" : `±${portionUncertainty}% (Interval Bound)`}
                        </span>
                      </div>
                      <input type="range" min={0} max={50} step={5} value={portionUncertainty} onChange={(e) => setPortionUncertainty(Number(e.target.value))} className="w-full accent-slate-900 dark:accent-slate-100" />
                      <span className="text-[10px] text-[var(--text-muted)] block mt-0.5">Conformal robust bounds [L_robust, U_robust] with ≥90% finite-sample coverage</span>
                    </div>
                  </div>

                  {/* Pharmacological Insulin Therapy Card */}
                  <div className="p-4 rounded-xl border border-[var(--border-main)] bg-[var(--bg-card-subtle)] space-y-4">
                    <div className="flex items-center justify-between border-b border-[var(--border-main)] pb-2.5">
                      <div className="flex items-center gap-2">
                        <svg className="w-4 h-4 text-[var(--text-main)]" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"/></svg>
                        <span className="text-xs font-semibold uppercase tracking-wider text-[var(--text-main)]">Insulin Therapy (Bolus &amp; Basal)</span>
                      </div>
                      <span className="text-[10px] px-2 py-0.5 rounded font-mono font-semibold bg-[var(--bg-card)] text-[var(--text-main)] border border-[var(--border-main)]">
                        PHARMACOLOGY
                      </span>
                    </div>

                    <div className="space-y-3.5">
                      <div>
                        <div className="flex justify-between text-xs mb-1">
                          <span className="text-[var(--text-secondary)] font-medium">Rapid-Acting Bolus Injection</span>
                          <span className="font-mono font-semibold text-[var(--text-main)]">{bolusUnits.toFixed(1)} U</span>
                        </div>
                        <input type="range" min={0} max={15} step={0.5} value={bolusUnits} onChange={(e) => setBolusUnits(Number(e.target.value))} className="w-full accent-slate-900 dark:accent-slate-100" />
                      </div>

                      <div>
                        <div className="flex justify-between text-xs mb-1">
                          <span className="text-[var(--text-secondary)] font-medium">Bolus Timing Relative to Meal</span>
                          <span className="font-mono font-semibold text-[var(--text-main)]">
                            {bolusTime > 0 ? `+${bolusTime} min (post-bolus)` : bolusTime < 0 ? `${bolusTime} min (pre-bolus)` : "0 min (at meal)"}
                          </span>
                        </div>
                        <input type="range" min={-30} max={60} step={5} value={bolusTime} onChange={(e) => setBolusTime(Number(e.target.value))} className="w-full accent-slate-900 dark:accent-slate-100" />
                        <div className="flex justify-between text-[10px] font-mono text-[var(--text-muted)] mt-0.5">
                          <span>-30m (pre-bolus)</span>
                          <span>0m (meal)</span>
                          <span>+60m (post-bolus)</span>
                        </div>
                      </div>

                      <div>
                        <div className="flex justify-between text-xs mb-1">
                          <span className="text-[var(--text-secondary)] font-medium">Basal Rate Differential (ΔR_b)</span>
                          <span className="font-mono font-semibold text-[var(--text-main)]">
                            {basalDiff >= 0 ? `+${basalDiff.toFixed(1)}` : basalDiff.toFixed(1)} U/hr
                          </span>
                        </div>
                        <input type="range" min={-1} max={1} step={0.1} value={basalDiff} onChange={(e) => setBasalDiff(Number(e.target.value))} className="w-full accent-slate-900 dark:accent-slate-100" />
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-2.5 pt-2 border-t border-[var(--border-main)]">
                      <div className="p-2.5 rounded-lg bg-[var(--bg-card)] border border-[var(--border-main)] text-center">
                        <span className="text-[11px] text-[var(--text-secondary)] block">Active IOB (+60m)</span>
                        <span className="text-sm font-bold font-mono text-[var(--text-main)]">{activeIOB60.toFixed(2)} U</span>
                        <span className="text-[10px] text-[var(--text-muted)] block mt-0.5">Insulin on Board</span>
                      </div>
                      <div className="p-2.5 rounded-lg bg-[var(--bg-card)] border border-[var(--border-main)] text-center">
                        <span className="text-[11px] text-[var(--text-secondary)] block">Net Deflection (ΔG_ins)</span>
                        <span className="text-sm font-bold font-mono text-[var(--text-main)]">{netDeflection60.toFixed(1)} mg/dL</span>
                        <span className="text-[10px] text-[var(--text-muted)] block mt-0.5">Analytical Gamma</span>
                      </div>
                    </div>
                  </div>

                  <div className="pt-3 border-t border-[var(--border-main)] space-y-2.5">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold uppercase tracking-wider text-[var(--text-secondary)]">Behavioral Interventions</span>
                      <span className="text-[11px] px-2 py-0.2 rounded font-mono font-semibold bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 border border-slate-300 dark:border-slate-700">
                        ASSUMPTION
                      </span>
                    </div>

                    <label className="flex items-center justify-between p-3 rounded-lg border border-[var(--border-main)] bg-[var(--bg-card-subtle)] cursor-pointer hover:border-[var(--border-subtle)] transition">
                      <div className="space-y-0.5">
                        <div className="text-xs font-medium text-[var(--text-main)] flex items-center gap-1.5">
                          <span>Post-Meal 15-Minute Brisk Walk</span>
                          <span className="text-[var(--text-secondary)] font-mono font-semibold">-18 mg/dL</span>
                        </div>
                        <div className="text-[11px] text-[var(--text-secondary)]">Elevates METs to 3.2 at +30m postprandial</div>
                      </div>
                      <input type="checkbox" checked={walking} onChange={(e) => setWalking(e.target.checked)} className="w-4 h-4 rounded accent-slate-900 dark:accent-slate-100" />
                    </label>

                    <label className="flex items-center justify-between p-3 rounded-lg border border-[var(--border-main)] bg-[var(--bg-card-subtle)] cursor-pointer hover:border-[var(--border-subtle)] transition">
                      <div className="space-y-0.5">
                        <div className="text-xs font-medium text-[var(--text-main)] flex items-center gap-1.5">
                          <span>Food Sequencing (Protein/Veg First)</span>
                          <span className="text-[var(--text-secondary)] font-mono font-semibold">-15 mg/dL</span>
                        </div>
                        <div className="text-[11px] text-[var(--text-secondary)]">Delays gastric emptying rate via GLP-1</div>
                      </div>
                      <input type="checkbox" checked={sequencing} onChange={(e) => setSequencing(e.target.checked)} className="w-4 h-4 rounded accent-slate-900 dark:accent-slate-100" />
                    </label>
                  </div>
                </div>

                <div className="lg:col-span-7 clean-card p-4 sm:p-6 space-y-5">
                  <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[var(--border-main)] pb-3">
                    <div>
                      <h2 className="text-base font-semibold text-[var(--text-main)]">Comparative Digital Twin Response</h2>
                      <p className="text-xs text-[var(--text-secondary)] mt-0.5">Baseline excursion vs counterfactual modified scenario</p>
                    </div>
                    <div className="flex items-center gap-3 text-xs">
                      <span className="flex items-center gap-1.5 text-[var(--text-secondary)]">
                        <span className="w-3 h-0.5 bg-slate-400 inline-block"></span> Baseline
                      </span>
                      <span className="flex items-center gap-1.5 text-[var(--text-secondary)]">
                        <span className="w-3 h-0.5 bg-[var(--text-main)] inline-block"></span> Counterfactual
                      </span>
                      {portionUncertainty > 0 && (
                        <span className="flex items-center gap-1.5 text-[var(--text-secondary)]">
                          <span className="w-3 h-2 bg-slate-400/20 border border-dashed border-slate-400 rounded-sm inline-block"></span> Robust Ribbon (±{portionUncertainty}%)
                        </span>
                      )}
                    </div>
                  </div>

                  {/* SVG Chart Visualizer with Dual-Band Robust Ribbon */}
                  <div className="h-72 sm:h-80 bg-[var(--bg-canvas)] rounded-xl border border-[var(--border-main)] p-4 flex flex-col justify-between">
                    <div className="flex justify-between text-xs text-[var(--text-muted)] font-mono">
                      <span>Pharmacological Superposition (ISF: {activeISF.toFixed(1)} mg/dL/U)</span>
                      <span className="text-[var(--text-main)] font-semibold">Portion: {portion}% {portionUncertainty > 0 ? `(±${portionUncertainty}%)` : ""}</span>
                    </div>

                    <div className="relative w-full h-44 flex items-center justify-center">
                      <svg className="w-full h-full" viewBox="0 0 520 160" preserveAspectRatio="none">
                        {/* Grid lines */}
                        <line x1="20" y1="20" x2="500" y2="20" stroke="var(--border-main)" strokeWidth="0.8" strokeDasharray="3,3" />
                        <line x1="20" y1="60" x2="500" y2="60" stroke="var(--border-main)" strokeWidth="0.8" strokeDasharray="3,3" />
                        <line x1="20" y1="100" x2="500" y2="100" stroke="var(--border-main)" strokeWidth="0.8" strokeDasharray="3,3" />
                        <line x1="20" y1="140" x2="500" y2="140" stroke="var(--border-main)" strokeWidth="0.8" strokeDasharray="3,3" />

                        {/* Robust Conformal Ribbon Envelope if portionUncertainty > 0 */}
                        {portionUncertainty > 0 && (
                          <polygon
                            points={[
                              ...robustUpper.map((val, idx) => `${20 + idx * 40},${Math.max(10, Math.min(150, 160 - ((val - 70) / 150) * 140))}`),
                              ...robustLower.slice().reverse().map((val, idx) => `${20 + (12 - idx) * 40},${Math.max(10, Math.min(150, 160 - ((val - 70) / 150) * 140))}`)
                            ].join(" ")}
                            fill="currentColor"
                            fillOpacity={0.06}
                            stroke="var(--border-subtle)"
                            strokeWidth="1"
                            strokeDasharray="4,4"
                          />
                        )}

                        {/* Baseline Excursion Curve (Slate 400) */}
                        <path
                          d={nominalPred.map((val, idx) => {
                            const x = 20 + idx * 40;
                            const y = Math.max(10, Math.min(150, 160 - ((val - 70) / 150) * 140));
                            return `${idx === 0 ? "M" : "L"} ${x} ${y}`;
                          }).join(" ")}
                          fill="none"
                          stroke="#94a3b8"
                          strokeWidth="2"
                        />

                        {/* Counterfactual Excursion Curve */}
                        <path
                          d={counterfactualTrajectory.map((val, idx) => {
                            const x = 20 + idx * 40;
                            const y = Math.max(10, Math.min(150, 160 - ((val - 70) / 150) * 140));
                            return `${idx === 0 ? "M" : "L"} ${x} ${y}`;
                          }).join(" ")}
                          fill="none"
                          stroke="var(--text-main)"
                          strokeWidth="2.5"
                        />

                        {/* Data Points */}
                        {counterfactualTrajectory.map((val, idx) => {
                          const x = 20 + idx * 40;
                          const y = Math.max(10, Math.min(150, 160 - ((val - 70) / 150) * 140));
                          return (
                            <circle key={idx} cx={x} cy={y} r="3" fill="var(--text-main)" />
                          );
                        })}
                      </svg>
                    </div>

                    <div className="flex justify-between text-xs text-[var(--text-muted)] font-mono border-t border-[var(--border-main)] pt-1">
                      <span>0m</span>
                      <span>30m</span>
                      <span>60m</span>
                      <span>90m</span>
                      <span>120m</span>
                      <span>150m</span>
                      <span>180m</span>
                    </div>
                  </div>

                  {/* 4-Column Deltas Grid */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <div className="bg-[var(--bg-card-subtle)] p-3 rounded-lg border border-[var(--border-main)]">
                      <div className="flex items-center justify-between text-xs mb-1">
                        <span className="text-[var(--text-secondary)] truncate">Δ Peak Glycemia</span>
                        <span className="text-[9px] font-mono font-semibold bg-[var(--bg-card)] border border-[var(--border-main)] px-1 py-0.2 rounded text-[var(--text-main)]">
                          MODEL
                        </span>
                      </div>
                      <div className="text-lg sm:text-xl font-bold font-mono text-[var(--text-main)]">
                        {deltaPeakValue > 0 ? `+${deltaPeakValue}` : deltaPeakValue} mg/dL
                      </div>
                      <span className="text-[10px] text-[var(--text-muted)] mt-1 block truncate">Excursion max delta</span>
                    </div>

                    <div className="bg-[var(--bg-card-subtle)] p-3 rounded-lg border border-[var(--border-main)]">
                      <div className="flex items-center justify-between text-xs mb-1">
                        <span className="text-[var(--text-secondary)] truncate">Δ Delayed Mean</span>
                        <span className="text-[9px] font-mono font-semibold bg-[var(--bg-card)] border border-[var(--border-main)] px-1 py-0.2 rounded text-[var(--text-main)]">
                          MODEL
                        </span>
                      </div>
                      <div className="text-lg sm:text-xl font-bold font-mono text-[var(--text-main)]">
                        {fatDelta.toFixed(1)} mg/dL
                      </div>
                      <span className="text-[10px] text-[var(--text-muted)] mt-1 block truncate">Late lipid plateau</span>
                    </div>

                    <div className="bg-[var(--bg-card-subtle)] p-3 rounded-lg border border-[var(--border-main)]">
                      <div className="flex items-center justify-between text-xs mb-1">
                        <span className="text-[var(--text-secondary)] truncate">Behavioral</span>
                        <span className="text-[9px] font-mono font-semibold bg-[var(--bg-card)] border border-[var(--border-main)] px-1 py-0.2 rounded text-[var(--text-main)]">
                          ASSUMPTION
                        </span>
                      </div>
                      <div className="text-lg sm:text-xl font-bold font-mono text-[var(--text-main)]">
                        {exerciseDelta} mg/dL
                      </div>
                      <span className="text-[10px] text-[var(--text-muted)] mt-1 block truncate">Exercise scalar</span>
                    </div>

                    <div className="bg-[var(--bg-card-subtle)] p-3 rounded-lg border border-[var(--border-main)]">
                      <div className="flex items-center justify-between text-xs mb-1">
                        <span className="text-[var(--text-secondary)] truncate">Insulin ΔG</span>
                        <span className="text-[9px] font-mono font-semibold bg-[var(--bg-card)] border border-[var(--border-main)] px-1 py-0.2 rounded text-[var(--text-main)]">
                          PHARMA
                        </span>
                      </div>
                      <div className="text-lg sm:text-xl font-bold font-mono text-[var(--text-main)]">
                        {netDeflection60.toFixed(1)} mg/dL
                      </div>
                      <span className="text-[10px] text-[var(--text-muted)] mt-1 block truncate">Gamma clearance</span>
                    </div>
                  </div>

                </div>

              </div>
            </div>
          )}

          {/* TAB 3: CHRONOLOGICAL MEAL TIMELINE (Refero Design Style) */}
          {activeTab === "timeline" && (
            <div className="space-y-6">
              
              <div className="clean-card p-4 flex flex-wrap items-center justify-between gap-4 text-xs">
                <div className="flex flex-wrap items-center gap-3">
                  <div className="flex items-center gap-1.5">
                    <span className="text-[var(--text-secondary)]">Date range:</span>
                    <input type="text" value="February 2026 (Clinical Protocol)" className="bg-[var(--bg-card-subtle)] border border-[var(--border-main)] text-[var(--text-main)] rounded px-2.5 py-1 text-xs outline-none" readOnly />
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="text-[var(--text-secondary)]">Meal Type:</span>
                    <select className="bg-[var(--bg-card-subtle)] border border-[var(--border-main)] text-[var(--text-main)] rounded px-2.5 py-1 text-xs outline-none">
                      <option>All Postprandial Excursions</option>
                      <option>Breakfast Excursions</option>
                      <option>Lunch Excursions</option>
                      <option>Dinner Excursions</option>
                    </select>
                  </div>
                  <button className="px-4 py-1 rounded bg-[var(--text-main)] text-[var(--bg-card)] font-semibold shadow-sm hover:opacity-90 transition">
                    FILTER
                  </button>
                </div>
                <div>
                  <button onClick={() => triggerToast("Exporting postprandial parquet log to CSV...")} className="text-slate-900 dark:text-slate-100 underline hover:opacity-80">
                    Want to export to a spreadsheet?
                  </button>
                </div>
              </div>

              <div className="clean-card overflow-hidden">
                <div className="p-4 border-b border-[var(--border-main)] flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-[var(--text-main)]">Recorded 180-Min Excursion Sessions</h3>
                  <span className="text-xs text-[var(--text-secondary)] font-mono">Total Meals: 54 Ingested</span>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead className="bg-[var(--bg-card-subtle)] text-[var(--text-secondary)] border-b border-[var(--border-main)]">
                      <tr>
                        <th className="py-2.5 px-4 font-semibold">Excursion Type</th>
                        <th className="py-2.5 px-4 font-semibold">Carbs (g)</th>
                        <th className="py-2.5 px-4 font-semibold">Fat (g)</th>
                        <th className="py-2.5 px-4 font-semibold">Protein (g)</th>
                        <th className="py-2.5 px-4 font-semibold">Observed Peak</th>
                        <th className="py-2.5 px-4 font-semibold">Duration</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[var(--border-main)] text-[var(--text-main)]">
                      <tr>
                        <td className="py-2.5 px-4 font-medium">Standard Indian Mixed Meal</td>
                        <td className="py-2.5 px-4 font-mono">48.0g</td>
                        <td className="py-2.5 px-4 font-mono">12.0g</td>
                        <td className="py-2.5 px-4 font-mono">16.0g</td>
                        <td className="py-2.5 px-4 font-mono text-slate-900 dark:text-slate-100 font-semibold">162.0 mg/dL</td>
                        <td className="py-2.5 px-4 text-[var(--text-secondary)]">180 min</td>
                      </tr>
                      <tr>
                        <td className="py-2.5 px-4 font-medium">High Carbohydrate Breakfast</td>
                        <td className="py-2.5 px-4 font-mono">68.0g</td>
                        <td className="py-2.5 px-4 font-mono">8.0g</td>
                        <td className="py-2.5 px-4 font-mono">10.0g</td>
                        <td className="py-2.5 px-4 font-mono text-slate-900 dark:text-slate-100 font-semibold">188.5 mg/dL</td>
                        <td className="py-2.5 px-4 text-[var(--text-secondary)]">180 min</td>
                      </tr>
                      <tr>
                        <td className="py-2.5 px-4 font-medium">High Lipid Delayed Plateau</td>
                        <td className="py-2.5 px-4 font-mono">42.0g</td>
                        <td className="py-2.5 px-4 font-mono">28.0g</td>
                        <td className="py-2.5 px-4 font-mono">22.0g</td>
                        <td className="py-2.5 px-4 font-mono text-slate-800 dark:text-slate-200 font-semibold">154.0 mg/dL</td>
                        <td className="py-2.5 px-4 text-[var(--text-secondary)]">180 min</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="space-y-4">
                <div className="text-xs font-semibold uppercase tracking-wider text-[var(--text-secondary)]">
                  Chronological Timeline Feed
                </div>

                <div className="space-y-2">
                  <div className="bg-[var(--bg-card-subtle)] px-4 py-1.5 rounded-lg text-xs font-semibold text-[var(--text-secondary)] border border-[var(--border-main)]">
                    February 13, 2026 — Clinical Ingest Stream
                  </div>

                  <div className="clean-card p-4 flex items-center justify-between gap-4">
                    <div className="flex items-center gap-4">
                      <div className="text-xs font-mono text-[var(--text-secondary)] text-right w-16">
                        <div className="font-bold text-[var(--text-main)]">08:30</div>
                        <div>11:30</div>
                      </div>
                      <div className="w-1 h-10 rounded-full bg-slate-900 dark:bg-slate-100"></div>
                      <div>
                        <div className="text-xs font-semibold text-[var(--text-main)]">Breakfast: 2 Rotis with Dal &amp; Mixed Veg Sabzi</div>
                        <div className="text-[11px] text-[var(--text-secondary)]">Nutrients: 48g Carbs • 12g Fat • 16g Protein | Peak: 164.2 mg/dL at +55m</div>
                        <div className="text-[10px] text-[var(--text-muted)]">Verified Continuous 5-Min Telemetry Buffer</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-[var(--bg-card-subtle)] text-[var(--text-secondary)] border border-[var(--border-main)]">
                        180 min
                      </span>
                    </div>
                  </div>

                  <div className="clean-card p-4 flex items-center justify-between gap-4">
                    <div className="flex items-center gap-4">
                      <div className="text-xs font-mono text-[var(--text-secondary)] text-right w-16">
                        <div className="font-bold text-[var(--text-main)]">13:15</div>
                        <div>16:15</div>
                      </div>
                      <div className="w-1 h-10 rounded-full bg-slate-900 dark:bg-slate-100"></div>
                      <div>
                        <div className="text-xs font-semibold text-[var(--text-main)]">Lunch: Masala Dosa with Sambar &amp; Chutney</div>
                        <div className="text-[11px] text-[var(--text-secondary)]">Nutrients: 62g Carbs • 18g Fat • 10g Protein | Peak: 178.0 mg/dL at +45m</div>
                        <div className="text-[10px] text-[var(--text-muted)]">Post-meal walking intervention recorded (15 min)</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-[var(--bg-card-subtle)] text-[var(--text-secondary)] border border-[var(--border-main)]">
                        180 min
                      </span>
                    </div>
                  </div>
                </div>
              </div>

            </div>
          )}

          {/* TAB 4: PATIENT PROFILE */}
          {activeTab === "profile" && (
            <div className="space-y-6">
              
              {/* Header with Edit Twin Biomarkers Action */}
              <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl border border-[var(--border-main)] bg-[var(--bg-card)]">
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-base font-semibold text-[var(--text-main)]">Clinical Metabolic Panel &amp; Digital Twin Phenotype</h2>
                    <span className="text-[10px] px-2 py-0.5 rounded font-mono font-semibold bg-[var(--bg-card-subtle)] text-[var(--text-main)] border border-[var(--border-main)]">
                      ICD-10 E11.9
                    </span>
                  </div>
                  <p className="text-xs text-[var(--text-secondary)] mt-0.5">Full metabolic lab panel, anthropometrics, lipid profile, and 1800-Rule sensitivity priors</p>
                </div>
                <button
                  onClick={openBiomarkersModal}
                  className="px-3.5 py-1.5 rounded-lg border border-[var(--border-main)] bg-[var(--bg-card-subtle)] hover:border-[var(--text-main)] text-xs font-semibold text-[var(--text-main)] shadow-sm transition flex items-center gap-2"
                >
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"/></svg>
                  <span>Edit Twin Biomarkers</span>
                </button>
              </div>

              {/* 4-Card Primary Metabolic Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                
                {/* Card 1: Anthropometrics & Baseline */}
                <div className="clean-card p-5 space-y-3">
                  <div className="flex items-center justify-between border-b border-[var(--border-main)] pb-2">
                    <span className="text-xs font-semibold uppercase tracking-wider text-[var(--text-main)]">Anthropometrics</span>
                    <span className="font-mono text-xs font-bold text-[var(--text-main)]">{patientId}</span>
                  </div>
                  <div className="space-y-1.5 text-xs">
                    <div className="flex justify-between py-1 border-b border-[var(--border-main)]"><span className="text-[var(--text-secondary)]">Diagnosis:</span> <span className="text-[var(--text-main)] font-semibold">{currentPatient.diagnosis}</span></div>
                    <div className="flex justify-between py-1 border-b border-[var(--border-main)]"><span className="text-[var(--text-secondary)]">Age &amp; Sex:</span> <span className="text-[var(--text-main)]">{currentPatient.age}</span></div>
                    <div className="flex justify-between py-1 border-b border-[var(--border-main)]"><span className="text-[var(--text-secondary)]">Weight:</span> <span className="font-mono text-[var(--text-main)] font-semibold">{currentPatient.weight.toFixed(1)} kg</span></div>
                    <div className="flex justify-between py-1 border-b border-[var(--border-main)]"><span className="text-[var(--text-secondary)]">Height:</span> <span className="font-mono text-[var(--text-main)]">{currentPatient.height.toFixed(1)} cm</span></div>
                    <div className="flex justify-between py-1 border-b border-[var(--border-main)]"><span className="text-[var(--text-secondary)]">BMI:</span> <span className="font-mono text-[var(--text-main)] font-semibold">{currentPatient.bmi}</span></div>
                    <div className="flex justify-between py-1"><span className="text-[var(--text-secondary)]">HbA1c:</span> <span className="font-mono text-[var(--text-main)] font-bold">{currentPatient.hba1c}</span></div>
                  </div>
                </div>

                {/* Card 2: Glycemic & Insulin Resistance */}
                <div className="clean-card p-5 space-y-3">
                  <div className="flex items-center justify-between border-b border-[var(--border-main)] pb-2">
                    <span className="text-xs font-semibold uppercase tracking-wider text-[var(--text-main)]">Insulin Resistance</span>
                    <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-[var(--bg-card-subtle)] text-[var(--text-main)] border border-[var(--border-main)]">HOMA</span>
                  </div>
                  <div className="space-y-1.5 text-xs">
                    <div className="flex justify-between py-1 border-b border-[var(--border-main)]"><span className="text-[var(--text-secondary)]">Fasting Glucose:</span> <span className="font-mono text-[var(--text-main)] font-semibold">{currentPatient.fasting}</span></div>
                    <div className="flex justify-between py-1 border-b border-[var(--border-main)]"><span className="text-[var(--text-secondary)]">Fasting Insulin:</span> <span className="font-mono text-[var(--text-main)] font-semibold">{currentPatient.fastingInsulin} µU/mL</span></div>
                    <div className="flex justify-between py-1 border-b border-[var(--border-main)]"><span className="text-[var(--text-secondary)]">HOMA-IR Score:</span> <span className="font-mono text-[var(--text-main)] font-bold">{currentPatient.homa}</span></div>
                    <div className="pt-1.5">
                      <span className="text-[11px] text-[var(--text-secondary)] block mb-1">Resistance Classification:</span>
                      <span className="text-xs font-semibold text-[var(--text-main)] block px-2 py-1 rounded bg-[var(--bg-card-subtle)] border border-[var(--border-main)]">
                        {currentPatient.homa > 2.9
                          ? "Significant Insulin Resistance (>2.9)"
                          : currentPatient.homa > 1.9
                          ? "Early Insulin Resistance (1.9–2.9)"
                          : "Normal Insulin Sensitivity (<1.9)"}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Card 3: Full Lipid Panel */}
                <div className="clean-card p-5 space-y-3">
                  <div className="flex items-center justify-between border-b border-[var(--border-main)] pb-2">
                    <span className="text-xs font-semibold uppercase tracking-wider text-[var(--text-main)]">Lipid Panel</span>
                    <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-[var(--bg-card-subtle)] text-[var(--text-main)] border border-[var(--border-main)]">FASTING</span>
                  </div>
                  <div className="space-y-1.5 text-xs">
                    <div className="flex justify-between py-1 border-b border-[var(--border-main)]"><span className="text-[var(--text-secondary)]">Triglycerides:</span> <span className="font-mono text-[var(--text-main)] font-semibold">{currentPatient.triglycerides} mg/dL</span></div>
                    <div className="flex justify-between py-1 border-b border-[var(--border-main)]"><span className="text-[var(--text-secondary)]">HDL Cholesterol:</span> <span className="font-mono text-[var(--text-main)] font-semibold">{currentPatient.hdl} mg/dL</span></div>
                    <div className="flex justify-between py-1 border-b border-[var(--border-main)]"><span className="text-[var(--text-secondary)]">LDL Cholesterol:</span> <span className="font-mono text-[var(--text-main)] font-semibold">{currentPatient.ldl} mg/dL</span></div>
                    <div className="flex justify-between py-1"><span className="text-[var(--text-secondary)]">TG / HDL Ratio:</span> <span className="font-mono text-[var(--text-main)] font-bold">{(currentPatient.triglycerides / (currentPatient.hdl || 1)).toFixed(1)}</span></div>
                  </div>
                </div>

                {/* Card 4: 1800-Rule Clinical Priors */}
                <div className="clean-card p-5 space-y-3">
                  <div className="flex items-center justify-between border-b border-[var(--border-main)] pb-2">
                    <span className="text-xs font-semibold uppercase tracking-wider text-[var(--text-main)]">1800-Rule Priors</span>
                    <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-[var(--bg-card-subtle)] text-[var(--text-main)] border border-[var(--border-main)]">ESTIMATED</span>
                  </div>
                  <div className="space-y-1.5 text-xs">
                    <div className="flex justify-between py-1 border-b border-[var(--border-main)]"><span className="text-[var(--text-secondary)]">Total Daily Dose (TDD):</span> <span className="font-mono text-[var(--text-main)] font-bold">{currentPatient.tdd.toFixed(1)} U</span></div>
                    <div className="flex justify-between py-1 border-b border-[var(--border-main)]"><span className="text-[var(--text-secondary)]">Insulin Sensitivity (ISF):</span> <span className="font-mono text-[var(--text-main)] font-bold">{currentPatient.isf.toFixed(1)} mg/dL/U</span></div>
                    <div className="flex justify-between py-1 border-b border-[var(--border-main)]"><span className="text-[var(--text-secondary)]">Carb Ratio (CIR):</span> <span className="font-mono text-[var(--text-main)] font-bold">{currentPatient.cir.toFixed(1)} g/U</span></div>
                    <div className="text-[10px] text-[var(--text-muted)] font-mono pt-1">
                      ISF = 1800 / (0.55 × Weight)
                    </div>
                  </div>
                </div>

              </div>

              {/* Secondary Clinical Records Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                
                {/* Synthetic EHR Records */}
                <div className="clean-card p-5 space-y-3">
                  <div className="flex items-center justify-between border-b border-[var(--border-main)] pb-2">
                    <span className="text-xs font-semibold uppercase tracking-wider text-[var(--text-main)]">Prescribed Regimen &amp; Comorbidities</span>
                    <span className="text-[10px] px-2 py-0.5 rounded font-mono font-semibold bg-[var(--bg-card-subtle)] text-[var(--text-main)] border border-[var(--border-main)]">
                      SYNTHETIC EHR (D14)
                    </span>
                  </div>
                  <div className="space-y-2.5 text-xs">
                    <div className="p-3 bg-[var(--bg-card-subtle)] rounded-lg border border-[var(--border-main)]">
                      <span className="text-[var(--text-secondary)] block font-medium">Prescribed Medications:</span>
                      <span className="text-[var(--text-main)] font-semibold mt-0.5 block">{currentPatient.meds}</span>
                    </div>
                    <div className="p-3 bg-[var(--bg-card-subtle)] rounded-lg border border-[var(--border-main)]">
                      <span className="text-[var(--text-secondary)] block font-medium">Diagnosed Comorbidities:</span>
                      <span className="text-[var(--text-main)] font-semibold mt-0.5 block">{currentPatient.comorbidities}</span>
                    </div>
                  </div>
                </div>

                {/* Few-Shot Adaptation Table */}
                <div className="clean-card p-5 space-y-3">
                  <div className="flex items-center justify-between border-b border-[var(--border-main)] pb-2">
                    <span className="text-xs font-semibold uppercase tracking-wider text-[var(--text-main)]">Few-Shot Personalization</span>
                    <span className="text-[10px] px-2 py-0.5 rounded font-mono font-semibold bg-[var(--bg-card-subtle)] text-[var(--text-main)] border border-[var(--border-main)]">
                      K = 5 MEALS
                    </span>
                  </div>
                  <div className="p-3 bg-[var(--bg-card-subtle)] rounded-lg border border-[var(--border-main)] space-y-1.5 text-xs font-mono">
                    <div className="flex justify-between text-[var(--text-secondary)]"><span>Zero-Shot (K=0):</span> <span className="text-[var(--text-main)]">12.95 mg/dL</span></div>
                    <div className="flex justify-between text-[var(--text-secondary)]"><span>1-Shot (K=1):</span> <span className="text-[var(--text-main)]">10.84 mg/dL</span></div>
                    <div className="flex justify-between text-[var(--text-secondary)]"><span>3-Shot (K=3):</span> <span className="text-[var(--text-main)]">9.45 mg/dL</span></div>
                    <div className="flex justify-between text-[var(--text-main)] font-bold border-t border-[var(--border-main)] pt-1.5">
                      <span>5-Shot Adapted (K=5):</span> <span>8.92 mg/dL</span>
                    </div>
                  </div>
                </div>

              </div>

            </div>
          )}

          {/* TAB 5: SENSOR STRESS AUDIT */}
          {activeTab === "audit" && (
            <div className="space-y-6">
              <div className="clean-card p-6 space-y-5">
                <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[var(--border-main)] pb-3">
                  <div>
                    <h2 className="text-base font-semibold text-[var(--text-main)]">Sensor Degradation &amp; Stress Testing (D0–D7)</h2>
                    <p className="text-xs text-[var(--text-secondary)] mt-0.5">Audit digital twin reliability under realistic wear failures and signal dropouts</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-[var(--text-secondary)]">Active Scenario:</span>
                    <span className="text-xs font-mono font-semibold bg-[var(--bg-card-subtle)] border border-slate-900 dark:border-slate-100 text-slate-900 dark:text-slate-100 px-3 py-1 rounded-lg">
                      {degradation}
                    </span>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                  {[
                    { id: "D0", label: "D0: Nominal Stream", desc: "No dropouts, continuous 5-min telemetry", status: "HIGH" },
                    { id: "D1_15m", label: "D1: Dropout 15m", desc: "Minor CGM retrospective gap", status: "MODERATE" },
                    { id: "D1_30m", label: "D1: Dropout 30m", desc: "Noticeable 30-min CGM gap", status: "MODERATE" },
                    { id: "D1_45m", label: "D1: Dropout 45m", desc: "Major CGM sensor silence", status: "LOW" },
                    { id: "D2", label: "D2: Low Sampling (15m)", desc: "Decimated to 15-min cadence", status: "MODERATE" },
                    { id: "D3", label: "D3: No HR / METs", desc: "Wearable battery failure", status: "MODERATE" },
                    { id: "D4", label: "D4: 50% Decimated CGM", desc: "Sparse glucose telemetry", status: "LOW" },
                    { id: "D7", label: "D7: Extreme Dropout (90m)", desc: "Severe CGM sensor failure", status: "LOW" },
                  ].map((item) => (
                    <button
                      key={item.id}
                      onClick={() => handleDegradation(item.id)}
                      className={`p-4 rounded-lg border text-left transition ${
                        degradation === item.id
                          ? "bg-[var(--bg-card)] border-slate-900 dark:border-slate-100 shadow-sm"
                          : "bg-[var(--bg-card-subtle)] border-[var(--border-main)] hover:border-[var(--border-subtle)]"
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-semibold text-[var(--text-main)]">{item.label}</span>
                        <span className={`text-[10px] px-1.5 py-0.2 rounded font-mono font-semibold ${
                          item.status === "HIGH" ? "bg-slate-900 text-white dark:bg-white dark:text-slate-900" : item.status === "MODERATE" ? "bg-slate-200 text-slate-800 dark:bg-slate-800 dark:text-slate-200" : "bg-slate-100 text-slate-600 dark:bg-slate-900 dark:text-slate-400 border border-slate-300 dark:border-slate-700"
                        }`}>
                          {item.status}
                        </span>
                      </div>
                      <span className="text-[11px] text-[var(--text-secondary)] block">{item.desc}</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* TAB 6: DOCTRONIC AI DOCTOR PERSONA & SETTINGS */}
          {activeTab === "settings" && (
            <div className="space-y-8 max-w-4xl">
              
              <div className="space-y-3 pt-2">
                <h1 className="text-3xl font-serif text-[var(--text-main)]">Dr. Connie</h1>
                <p className="text-xs text-[var(--text-secondary)]">aegis.endocrinology.twin@happiesthealth.org</p>
                <div className="flex items-center gap-2 pt-1">
                  <button onClick={() => triggerToast("Connecting to clinical protocol support...")} className="px-3 py-1 rounded-full border border-[var(--border-main)] bg-[var(--bg-card)] hover:border-[var(--border-subtle)] text-xs text-[var(--text-main)] flex items-center gap-1.5 transition">
                    <span>✉</span> Contact us
                  </button>
                  <button onClick={() => triggerToast("Opening clinical guideline resources...")} className="px-3 py-1 rounded-full border border-[var(--border-main)] bg-[var(--bg-card)] hover:border-[var(--border-subtle)] text-xs text-[var(--text-main)] flex items-center gap-1.5 transition">
                    <span>?</span> Resources
                  </button>
                  <button onClick={() => triggerToast("Feedback submitted to team Aegis.")} className="px-3 py-1 rounded-full border border-[var(--border-main)] bg-[var(--bg-card)] hover:border-[var(--border-subtle)] text-xs text-[var(--text-main)] flex items-center gap-1.5 transition">
                    <span>☆</span> Feedback
                  </button>
                </div>
              </div>

              <div className="h-px bg-[var(--border-main)]"></div>

              <div className="space-y-8 text-xs">
                
                {/* Response Style Row (Doctronic Step 1, 2, 3) */}
                <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-start">
                  <div className="md:col-span-4 flex items-center gap-2.5 text-sm font-medium text-[var(--text-main)]">
                    <svg className="w-5 h-5 text-[var(--text-secondary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                    <span>Response style</span>
                  </div>

                  <div className="md:col-span-8 relative">
                    <button
                      onClick={() => setIsStylePopoverOpen((p) => !p)}
                      className="w-full flex items-center justify-between p-3 rounded-xl border border-[var(--border-main)] bg-[var(--bg-card)] text-left hover:border-[var(--border-subtle)] transition"
                    >
                      <span className="font-medium text-[var(--text-main)]">{doctorResponseStyle}</span>
                      <svg className="w-4 h-4 text-[var(--text-secondary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"/></svg>
                    </button>

                    {isStylePopoverOpen && (
                      <div className="absolute top-full mt-2 left-0 right-0 z-50 bg-[var(--bg-card)] rounded-xl border border-[var(--border-main)] shadow-xl overflow-hidden p-1.5 space-y-1">
                        {[
                          { name: "Default", desc: "Aegis standard clinical medical tone with professionalism and physiological context" },
                          { name: "Just the facts", desc: "Clinical precision without the bedside manner (numeric metrics, deltas, and ADA ranges only)" },
                          { name: "The wise professor", desc: "Detailed mechanistic endocrinology explanations with metabolic physiology context" },
                          { name: "Supportive", desc: "Empathetic preventive wellness guidance, post-meal walking prompts, and positive reinforcement" },
                          { name: "Your friendly neighbor", desc: "Warm, approachable conversation free of heavy clinical jargon" },
                        ].map((style) => (
                          <div
                            key={style.name}
                            onClick={() => {
                              setDoctorResponseStyle(style.name);
                              setIsStylePopoverOpen(false);
                              triggerToast("Your settings have been updated");
                            }}
                            className={`p-2.5 rounded-lg cursor-pointer transition ${
                              doctorResponseStyle === style.name ? "bg-emerald-500/10 text-[var(--text-main)]" : "hover:bg-[var(--bg-card-subtle)] text-[var(--text-secondary)]"
                            }`}
                          >
                            <div className="flex items-center justify-between font-semibold">
                              <span>{style.name}</span>
                              {doctorResponseStyle === style.name && <span className="text-emerald-500">✓</span>}
                            </div>
                            <div className="text-[11px] mt-0.5">{style.desc}</div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                {/* Time Zone */}
                <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-start">
                  <div className="md:col-span-4 flex items-center gap-2.5 text-sm font-medium text-[var(--text-main)]">
                    <svg className="w-5 h-5 text-[var(--text-secondary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
                    <span>Clinical Time Zone</span>
                  </div>
                  <div className="md:col-span-8">
                    <div className="flex items-center gap-2 p-3 rounded-xl border border-[var(--border-main)] bg-[var(--bg-card)]">
                      <svg className="w-4 h-4 text-[var(--text-muted)]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
                      <input type="text" defaultValue="Asia / Kolkata (GMT+5:30)" className="w-full bg-transparent text-[var(--text-main)] outline-none font-medium" onChange={(e) => triggerToast(`Time zone updated to ${e.target.value}`)} />
                    </div>
                  </div>
                </div>

                {/* Memory & Sync */}
                <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-start">
                  <div className="md:col-span-4 flex items-center gap-2.5 text-sm font-medium text-[var(--text-main)]">
                    <svg className="w-5 h-5 text-[var(--text-secondary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/></svg>
                    <span>Twin Memory</span>
                  </div>
                  <div className="md:col-span-8 space-y-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-semibold text-[var(--text-main)]">Reference patient chat history</div>
                        <div className="text-[11px] text-[var(--text-secondary)]">Let Aegis reference previous endocrinology consultations when predicting response.</div>
                      </div>
                      <span className="font-semibold text-[var(--text-main)] px-2.5 py-1 rounded bg-[var(--bg-card-subtle)] border border-[var(--border-main)]">On</span>
                    </div>

                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-semibold text-[var(--text-main)]">Reference synthetic medical records</div>
                        <div className="text-[11px] text-[var(--text-secondary)]">Let Aegis reference shared EHR biomarkers (HbA1c, fasting glucose) when calibrating Ridge weights.</div>
                      </div>
                      <span className="font-semibold text-[var(--text-main)] px-2.5 py-1 rounded bg-[var(--bg-card-subtle)] border border-[var(--border-main)]">On</span>
                    </div>
                  </div>
                </div>

              </div>

              <div className="pt-8 border-t border-[var(--border-main)] space-y-4">
                <div className="flex justify-center">
                  <button onClick={() => triggerToast("Clinician session reset.")} className="px-8 py-2 rounded-full border border-[var(--border-main)] bg-[var(--bg-card)] text-xs font-semibold text-[var(--text-main)] hover:border-[var(--border-subtle)] transition">
                    Reset Session
                  </button>
                </div>
                <p className="text-center text-[11px] text-[var(--text-muted)] max-w-xl mx-auto">
                  Always review digital twin trajectories with licensed endocrinologists. Aegis is an AI research prototype, not a certified medical device, and does not provide prescription or acute titration decisions.
                </p>
              </div>

            </div>
          )}

        </main>

      </div>

      {/* 4. Command Palette Modal */}
      {isPaletteOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-sm flex items-start justify-center pt-24 px-4">
          <div className="w-full max-w-xl bg-[var(--bg-card)] rounded-xl border border-[var(--border-main)] shadow-2xl overflow-hidden">
            <div className="p-3.5 border-b border-[var(--border-main)] flex items-center gap-3 bg-[var(--bg-card-subtle)]">
              <input
                type="text"
                autoFocus
                value={paletteQuery}
                onChange={(e) => { setPaletteQuery(e.target.value); setPaletteIndex(0); }}
                placeholder="Search actions, twins, meal presets, or theme..."
                className="bg-transparent text-[var(--text-main)] placeholder-[var(--text-muted)] text-xs outline-none flex-1 font-sans"
              />
              <kbd className="text-[11px] font-mono bg-[var(--bg-card)] text-[var(--text-secondary)] px-2 py-0.5 rounded border border-[var(--border-main)]">ESC</kbd>
            </div>
            <div className="max-h-80 overflow-y-auto p-2 space-y-1">
              {filteredActions.length === 0 ? (
                <div className="text-xs text-[var(--text-muted)] text-center py-6">No matching actions</div>
              ) : (
                filteredActions.map((item, idx) => (
                  <div
                    key={item.id}
                    onClick={() => { item.run(); setIsPaletteOpen(false); }}
                    className={`flex items-center justify-between p-2.5 rounded-lg cursor-pointer transition text-xs ${
                      idx === paletteIndex ? "bg-slate-900 text-white dark:bg-white dark:text-slate-900 border border-transparent" : "bg-[var(--bg-card-subtle)] border border-transparent text-[var(--text-secondary)] hover:text-[var(--text-main)] hover:border-[var(--border-main)]"
                    }`}
                  >
                    <div className="flex items-center gap-2.5">
                      <span className={`w-1.5 h-1.5 rounded-full ${idx === paletteIndex ? "bg-white dark:bg-slate-900" : "bg-slate-400"}`}></span>
                      <span>{item.title}</span>
                    </div>
                    <span className={`font-mono text-[11px] px-2 py-0.5 rounded border ${
                      idx === paletteIndex ? "bg-slate-800 text-slate-200 dark:bg-slate-200 dark:text-slate-800 border-transparent" : "bg-[var(--bg-card)] text-[var(--text-secondary)] border-[var(--border-main)]"
                    }`}>{item.key}</span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* 5. Custom Meal Modal */}
      {isCustomMealOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-md bg-[var(--bg-card)] rounded-xl border border-[var(--border-main)] shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-[var(--border-main)] pb-3">
              <h3 className="text-sm font-semibold text-[var(--text-main)]">Build Custom Nutritional Input</h3>
              <button onClick={() => setIsCustomMealOpen(false)} className="text-[var(--text-secondary)] hover:text-[var(--text-main)] text-xs">✕</button>
            </div>
            <div className="space-y-3 text-xs">
              <div>
                <label className="text-[var(--text-secondary)] font-medium block mb-1">Meal Name:</label>
                <input
                  type="text"
                  value={customName}
                  onChange={(e) => setCustomName(e.target.value)}
                  className="w-full bg-[var(--bg-card-subtle)] border border-[var(--border-main)] text-[var(--text-main)] rounded-lg p-2.5 outline-none focus:border-slate-900 dark:focus:border-slate-100"
                />
              </div>
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="text-[var(--text-secondary)] font-medium block mb-1">Carbs (g):</label>
                  <input
                    type="number"
                    value={customCarbs}
                    onChange={(e) => setCustomCarbs(Number(e.target.value))}
                    className="w-full bg-[var(--bg-card-subtle)] border border-[var(--border-main)] text-[var(--text-main)] rounded-lg p-2 font-mono outline-none focus:border-slate-900 dark:focus:border-slate-100"
                  />
                </div>
                <div>
                  <label className="text-[var(--text-secondary)] font-medium block mb-1">Fat (g):</label>
                  <input
                    type="number"
                    value={customFat}
                    onChange={(e) => setCustomFat(Number(e.target.value))}
                    className="w-full bg-[var(--bg-card-subtle)] border border-[var(--border-main)] text-[var(--text-main)] rounded-lg p-2 font-mono outline-none focus:border-slate-900 dark:focus:border-slate-100"
                  />
                </div>
                <div>
                  <label className="text-[var(--text-secondary)] font-medium block mb-1">Protein (g):</label>
                  <input
                    type="number"
                    value={customProtein}
                    onChange={(e) => setCustomProtein(Number(e.target.value))}
                    className="w-full bg-[var(--bg-card-subtle)] border border-[var(--border-main)] text-[var(--text-main)] rounded-lg p-2 font-mono outline-none focus:border-slate-900 dark:focus:border-slate-100"
                  />
                </div>
              </div>
            </div>
            <div className="flex justify-end gap-2.5 pt-3 border-t border-[var(--border-main)]">
              <button
                onClick={() => setIsCustomMealOpen(false)}
                className="px-3.5 py-1.5 rounded-lg border border-[var(--border-main)] bg-[var(--bg-card-subtle)] text-[var(--text-secondary)] hover:text-[var(--text-main)] text-xs font-medium"
              >
                Cancel
              </button>
              <button
                onClick={applyCustomMeal}
                className="px-4 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-white dark:bg-white dark:hover:bg-slate-100 dark:text-slate-900 text-xs font-semibold shadow-sm transition"
              >
                Apply to Sandbox
              </button>
            </div>
          </div>
        </div>
      {/* EDIT TWIN BIOMARKERS MODAL */}
      {isBiomarkersModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-xl bg-[var(--bg-card)] rounded-xl border border-[var(--border-main)] shadow-2xl p-6 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-[var(--border-main)] pb-3">
              <div>
                <h3 className="text-sm font-semibold text-[var(--text-main)]">Edit Digital Twin Clinical Biomarkers</h3>
                <p className="text-xs text-[var(--text-secondary)] mt-0.5">Update patient laboratory biomarkers, physiological anthropometrics, and sensitivity overrides</p>
              </div>
              <button onClick={() => setIsBiomarkersModalOpen(false)} className="text-[var(--text-secondary)] hover:text-[var(--text-main)] text-xs">✕</button>
            </div>

            <div className="space-y-4 text-xs">
              {/* Physical Anthropometrics & Glycemia */}
              <div>
                <label className="text-[11px] font-semibold uppercase tracking-wider text-[var(--text-secondary)] block mb-2">Anthropometrics &amp; Glycemia</label>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div>
                    <label className="text-[var(--text-secondary)] block mb-1">Weight (kg):</label>
                    <input
                      type="number"
                      step="0.5"
                      value={editWeight}
                      onChange={(e) => setEditWeight(parseFloat(e.target.value) || 0)}
                      className="w-full bg-[var(--bg-card-subtle)] border border-[var(--border-main)] text-[var(--text-main)] rounded-lg p-2 font-mono outline-none focus:border-slate-900 dark:focus:border-slate-100"
                    />
                  </div>
                  <div>
                    <label className="text-[var(--text-secondary)] block mb-1">Height (cm):</label>
                    <input
                      type="number"
                      step="0.5"
                      value={editHeight}
                      onChange={(e) => setEditHeight(parseFloat(e.target.value) || 0)}
                      className="w-full bg-[var(--bg-card-subtle)] border border-[var(--border-main)] text-[var(--text-main)] rounded-lg p-2 font-mono outline-none focus:border-slate-900 dark:focus:border-slate-100"
                    />
                  </div>
                  <div>
                    <label className="text-[var(--text-secondary)] block mb-1">Fasting Gluc (mg/dL):</label>
                    <input
                      type="number"
                      step="1"
                      value={editFastingGlucose}
                      onChange={(e) => setEditFastingGlucose(parseFloat(e.target.value) || 0)}
                      className="w-full bg-[var(--bg-card-subtle)] border border-[var(--border-main)] text-[var(--text-main)] rounded-lg p-2 font-mono outline-none focus:border-slate-900 dark:focus:border-slate-100"
                    />
                  </div>
                  <div>
                    <label className="text-[var(--text-secondary)] block mb-1">Fasting Ins (µU/mL):</label>
                    <input
                      type="number"
                      step="0.1"
                      value={editFastingInsulin}
                      onChange={(e) => setEditFastingInsulin(parseFloat(e.target.value) || 0)}
                      className="w-full bg-[var(--bg-card-subtle)] border border-[var(--border-main)] text-[var(--text-main)] rounded-lg p-2 font-mono outline-none focus:border-slate-900 dark:focus:border-slate-100"
                    />
                  </div>
                </div>
              </div>

              {/* Lipid Panel & Glycated Hemoglobin */}
              <div>
                <label className="text-[11px] font-semibold uppercase tracking-wider text-[var(--text-secondary)] block mb-2">Lipid Panel &amp; Glycated Hemoglobin</label>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div>
                    <label className="text-[var(--text-secondary)] block mb-1">HbA1c (%):</label>
                    <input
                      type="number"
                      step="0.1"
                      value={editHbA1c}
                      onChange={(e) => setEditHbA1c(parseFloat(e.target.value) || 0)}
                      className="w-full bg-[var(--bg-card-subtle)] border border-[var(--border-main)] text-[var(--text-main)] rounded-lg p-2 font-mono outline-none focus:border-slate-900 dark:focus:border-slate-100"
                    />
                  </div>
                  <div>
                    <label className="text-[var(--text-secondary)] block mb-1">Triglycerides (mg/dL):</label>
                    <input
                      type="number"
                      step="1"
                      value={editTriglycerides}
                      onChange={(e) => setEditTriglycerides(parseFloat(e.target.value) || 0)}
                      className="w-full bg-[var(--bg-card-subtle)] border border-[var(--border-main)] text-[var(--text-main)] rounded-lg p-2 font-mono outline-none focus:border-slate-900 dark:focus:border-slate-100"
                    />
                  </div>
                  <div>
                    <label className="text-[var(--text-secondary)] block mb-1">HDL (mg/dL):</label>
                    <input
                      type="number"
                      step="1"
                      value={editHDL}
                      onChange={(e) => setEditHDL(parseFloat(e.target.value) || 0)}
                      className="w-full bg-[var(--bg-card-subtle)] border border-[var(--border-main)] text-[var(--text-main)] rounded-lg p-2 font-mono outline-none focus:border-slate-900 dark:focus:border-slate-100"
                    />
                  </div>
                  <div>
                    <label className="text-[var(--text-secondary)] block mb-1">LDL (mg/dL):</label>
                    <input
                      type="number"
                      step="1"
                      value={editLDL}
                      onChange={(e) => setEditLDL(parseFloat(e.target.value) || 0)}
                      className="w-full bg-[var(--bg-card-subtle)] border border-[var(--border-main)] text-[var(--text-main)] rounded-lg p-2 font-mono outline-none focus:border-slate-900 dark:focus:border-slate-100"
                    />
                  </div>
                </div>
              </div>

              {/* Sensitivity Overrides */}
              <div>
                <label className="text-[11px] font-semibold uppercase tracking-wider text-[var(--text-secondary)] block mb-2">Sensitivity Factor Overrides (Optional)</label>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-[var(--text-secondary)] block mb-1">ISF Override (mg/dL per Unit):</label>
                    <input
                      type="number"
                      step="0.1"
                      placeholder="Auto (1800-rule)"
                      value={editISF}
                      onChange={(e) => setEditISF(e.target.value)}
                      className="w-full bg-[var(--bg-card-subtle)] border border-[var(--border-main)] text-[var(--text-main)] rounded-lg p-2 font-mono outline-none focus:border-slate-900 dark:focus:border-slate-100"
                    />
                  </div>
                  <div>
                    <label className="text-[var(--text-secondary)] block mb-1">CIR Override (g Carbs per Unit):</label>
                    <input
                      type="number"
                      step="0.1"
                      placeholder="Auto (500-rule)"
                      value={editCIR}
                      onChange={(e) => setEditCIR(e.target.value)}
                      className="w-full bg-[var(--bg-card-subtle)] border border-[var(--border-main)] text-[var(--text-main)] rounded-lg p-2 font-mono outline-none focus:border-slate-900 dark:focus:border-slate-100"
                    />
                  </div>
                </div>
              </div>

              {/* Live Preview */}
              <div className="p-3.5 rounded-lg border border-[var(--border-main)] bg-[var(--bg-card-subtle)] space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-[var(--text-main)]">Live Derived Physiological Parameters:</span>
                  <span className="text-[10px] font-mono font-semibold bg-[var(--bg-card)] border border-[var(--border-main)] px-1.5 py-0.2 rounded text-[var(--text-secondary)]">
                    PREVIEW
                  </span>
                </div>
                <div className="grid grid-cols-3 gap-2 text-center text-xs">
                  <div className="p-2 rounded bg-[var(--bg-card)] border border-[var(--border-main)]">
                    <span className="text-[11px] text-[var(--text-secondary)] block">Body Mass Index</span>
                    <span className="font-mono font-bold text-[var(--text-main)]">{modalBMI || "--"}</span>
                  </div>
                  <div className="p-2 rounded bg-[var(--bg-card)] border border-[var(--border-main)]">
                    <span className="text-[11px] text-[var(--text-secondary)] block">HOMA-IR Index</span>
                    <span className="font-mono font-bold text-[var(--text-main)]">{modalHOMA || "--"}</span>
                  </div>
                  <div className="p-2 rounded bg-[var(--bg-card)] border border-[var(--border-main)]">
                    <span className="text-[11px] text-[var(--text-secondary)] block">1800-Rule ISF</span>
                    <span className="font-mono font-bold text-[var(--text-main)]">{modalISF ? `${modalISF} mg/dL/U` : "--"}</span>
                  </div>
                </div>
                <div className="text-[11px] font-mono text-[var(--text-muted)] text-center pt-1">
                  TDD: {modalTDD} U • CIR: {modalCIR} g/U
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-2.5 pt-3 border-t border-[var(--border-main)]">
              <button
                onClick={() => setIsBiomarkersModalOpen(false)}
                className="px-3.5 py-1.5 rounded-lg border border-[var(--border-main)] bg-[var(--bg-card-subtle)] text-[var(--text-secondary)] hover:text-[var(--text-main)] text-xs font-medium"
              >
                Cancel
              </button>
              <button
                onClick={saveBiomarkers}
                className="px-4 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-white dark:bg-white dark:hover:bg-slate-100 dark:text-slate-900 text-xs font-semibold shadow-sm transition"
              >
                Save Changes
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
