import { useState, useMemo, useEffect } from "react";

export default function SimulationDashboard({ 
  recommendation, onBack, GLOBAL_CSS, result, user, setUser, setPage, goCalculator, setShowSignup 
}) {
  // --- BASELINE DATA ---
  const baseS1 = (result?.combined?.s1 * 12) || 10;
  const baseS2 = (result?.combined?.s2 * 12) || 20;
  const baseS3 = (result?.combined?.s3 * 12) || 15;
  const baseAnn = (result?.combined?.ann) || (baseS1 + baseS2 + baseS3) || 45;
  
  // --- SIMULATION STATES ---
  const [renewableShare, setRenewableShare] = useState(result?.renewable || 0);
  const [wfhShare, setWfhShare] = useState(0);
  const [employeeCount, setEmployeeCount] = useState(result?.employees || 50);
  const [onsiteServers, setOnsiteServers] = useState(result?.servers || 0);
  const [cloudPct, setCloudPct] = useState(result?.cloud !== "none" ? 50 : 0);
  const [fleetSize, setFleetSize] = useState((result?.bdown?.Diesel > 0 || result?.bdown?.Petrol > 0) ? 5 : 0);
  const [fuelUsage, setFuelUsage] = useState((result?.bdown?.Diesel || 0) * 10 + (result?.bdown?.Petrol || 0) * 10);
  const [timeHorizon, setTimeHorizon] = useState(50);

  // --- LOGICAL MODELING ---
  // We model the simulation as a series of multipliers against the baseline.
  const simulation = useMemo(() => {
    // 1. Scope 1: Driven by fleet and fuel.
    // If fleet is reduced or fuel is optimized, S1 drops.
    const s1Multiplier = (fleetSize > 0) ? (fuelUsage / Math.max(1, (result?.bdown?.Diesel || 10) * 10 + (result?.bdown?.Petrol || 10) * 10)) : 0.1;
    const simS1 = baseS1 * Math.max(0.05, s1Multiplier);

    // 2. Scope 2: Driven by Renewables and Server efficiency.
    // Base S2 is reduced by renewable share.
    // Server load is added/subtracted based on the difference from baseline.
    const s2RenewableImpact = (1 - (renewableShare / 100));
    const baseServers = result?.servers || 0;
    const serverDelta = (onsiteServers - baseServers) * 0.5; // Each server adds ~0.5 tCO2e/yr
    const simS2 = Math.max(0, (baseS2 + serverDelta) * s2RenewableImpact);

    // 3. Scope 3: Driven by Cloud migration and WFH.
    // Cloud migration reduces S2 (onsite) but increases S3 (indirect).
    // WFH reduces S2 (office) but might increase S3 (home office - usually smaller).
    const cloudImpact = (cloudPct / 100) * (baseS2 * 0.2); // Cloud is 80% more efficient than on-prem
    const wfhImpact = (wfhShare / 100) * (baseS2 * 0.15); // WFH reduces office energy
    const simS3 = Math.max(0.1, baseS3 + cloudImpact - wfhImpact);

    const simTotal = simS1 + simS2 + simS3;
    
    // Avoidance is Baseline - Simulated
    const avoidance = baseAnn - simTotal;
    const annualSavings = avoidance * 12500; // Proxy price: ₹12,500/tonne

    return { 
      s1: simS1, 
      s2: simS2, 
      s3: simS3, 
      total: simTotal, 
      avoidance: avoidance,
      savings: annualSavings 
    };
  }, [renewableShare, wfhShare, employeeCount, onsiteServers, cloudPct, fleetSize, fuelUsage, baseS1, baseS2, baseS3, baseAnn, result]);

  // --- 50 YEAR PROJECTION ---
  const projectionData = useMemo(() => {
    const points = [];
    const growthRate = 1.02; // 2% business growth
    const industryGrowth = 1.03; // 3% industry growth (doing nothing)
    for (let i = 0; i <= timeHorizon; i++) {
      const year = i;
      const baseline = baseAnn * Math.pow(growthRate, i);
      const simulated = simulation.total * Math.pow(growthRate, i);
      const industry = baseAnn * Math.pow(industryGrowth, i);
      points.push({ year, baseline, simulated, industry });
    }
    return points;
  }, [simulation.total, baseAnn, timeHorizon]);

  // --- SVG HELPERS ---
  const PieChart = ({ s1, s2, s3 }) => {
    const total = s1 + s2 + s3 || 1;
    const p1 = (s1 / total) * 100;
    const p2 = (s2 / total) * 100;
    const p3 = (s3 / total) * 100;

    return (
      <svg viewBox="0 0 100 100" style={{ width: 180, height: 180, transform: "rotate(-90deg)" }}>
        <circle cx="50" cy="50" r="40" fill="transparent" stroke="#2563EB" strokeWidth="20" strokeDasharray={`${p1} 100`} />
        <circle cx="50" cy="50" r="40" fill="transparent" stroke="#16A34A" strokeWidth="20" strokeDasharray={`${p2} 100`} strokeDashoffset={`-${p1}`} />
        <circle cx="50" cy="50" r="40" fill="transparent" stroke="#0891B2" strokeWidth="20" strokeDasharray={`${p3} 100`} strokeDashoffset={`-${p1 + p2}`} />
        <circle cx="50" cy="50" r="30" fill="var(--white)" />
      </svg>
    );
  };

  const BarGraph = ({ s1, s2, s3 }) => {
    const maxVal = Math.max(s1, s2, s3, 1);
    const h1 = (s1 / maxVal) * 100;
    const h2 = (s2 / maxVal) * 100;
    const h3 = (s3 / maxVal) * 100;

    return (
      <div style={{ display: "flex", alignItems: "flex-end", gap: 20, height: 120, paddingBottom: 20, borderBottom: "1px solid var(--line)" }}>
        <div style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center" }}>
          <div style={{ width: "100%", height: `${h1}%`, background: "#2563EB", borderRadius: "4px 4px 0 0" }} />
          <div style={{ fontSize: 10, marginTop: 8, color: "var(--muted)", fontFamily: "JetBrains Mono" }}>SCOPE 1</div>
        </div>
        <div style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center" }}>
          <div style={{ width: "100%", height: `${h2}%`, background: "#16A34A", borderRadius: "4px 4px 0 0" }} />
          <div style={{ fontSize: 10, marginTop: 8, color: "var(--muted)", fontFamily: "JetBrains Mono" }}>SCOPE 2</div>
        </div>
        <div style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center" }}>
          <div style={{ width: "100%", height: `${h3}%`, background: "#0891B2", borderRadius: "4px 4px 0 0" }} />
          <div style={{ fontSize: 10, marginTop: 8, color: "var(--muted)", fontFamily: "JetBrains Mono" }}>SCOPE 3</div>
        </div>
      </div>
    );
  };

  const LineChart = ({ data }) => {
    const w = 600; const h = 240;
    const pad = 40;
    const maxVal = Math.max(...data.map(d => d.industry)) * 1.1;
    
    const getPoints = (key) => data.map((d, i) => `${(i / timeHorizon) * (w - 2 * pad) + pad},${h - pad - (d[key] / maxVal) * (h - 2 * pad)}`).join(" ");

    return (
      <svg viewBox={`0 0 ${w} ${h}`} style={{ width: "100%", height: h }}>
        {/* Grids */}
        <line x1={pad} y1={h - pad} x2={w - pad} y2={h - pad} stroke="var(--line)" />
        <line x1={pad} y1={pad} x2={pad} y2={h - pad} stroke="var(--line)" />
        
        {/* Industry Projection (Do Nothing) - Red/Visible */}
        <polyline points={getPoints("industry")} fill="none" stroke="#EF4444" strokeWidth="1.5" strokeDasharray="5 3" />
        
        {/* Baseline (Current BAU) - Gray */}
        <polyline points={getPoints("baseline")} fill="none" stroke="#94A3B8" strokeWidth="1.5" strokeDasharray="2 2" />
        
        {/* Simulated Strategic Path - Green */}
        <polyline points={getPoints("simulated")} fill="none" stroke="#16A34A" strokeWidth="3" />
        
        <text x={pad} y={h - 10} fontSize="10" fill="var(--muted)" fontFamily="JetBrains Mono">YEAR 0</text>
        <text x={w - pad} y={h - 10} textAnchor="end" fontSize="10" fill="var(--muted)" fontFamily="JetBrains Mono">YEAR {timeHorizon}</text>
      </svg>
    );
  };

  return (
    <>
      <style>{GLOBAL_CSS}</style>
      <div style={{ background: "var(--off)", minHeight: "100vh", paddingTop: 80 }}>
        <div style={{ maxWidth: 1400, margin: "0 auto", padding: "0 40px 80px" }}>
          
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: 40 }}>
            <div>
              <button onClick={onBack} style={{ background: "none", border: "none", color: "var(--g600)", cursor: "pointer", fontSize: 13, marginBottom: 16, padding: 0 }}>[BACK] Dashboard</button>
              <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 11, letterSpacing: ".2em", textTransform: "uppercase", color: "var(--muted)", marginBottom: 8 }}>Strategic Planning</div>
              <h1 style={{ fontFamily: "Cormorant Garamond, serif", fontSize: 48, fontWeight: 300, color: "var(--ink)", margin: 0 }}>Impact Simulation</h1>
            </div>
            <div style={{ textAlign: "right" }}>
              <div style={{ fontSize: 13, color: "var(--muted)", marginBottom: 4 }}>Simulated Annual Savings</div>
              <div style={{ fontSize: 32, fontWeight: 600, color: "var(--g600)" }}>₹{Math.max(0, simulation.savings).toLocaleString()}</div>
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "420px 1fr", gap: 40 }}>
            
            <div style={{ background: "var(--white)", border: "1px solid var(--line)", borderRadius: 12, padding: 32, boxShadow: "var(--sh)" }}>
              <h3 style={{ fontFamily: "Syne, sans-serif", fontSize: 18, marginBottom: 24 }}>Strategic Parameters</h3>
              
              <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
                {[
                  { label: "Renewable Share", val: renewableShare, set: setRenewableShare, min: 0, max: 100, unit: "%" },
                  { label: "Work From Home", val: wfhShare, set: setWfhShare, min: 0, max: 100, unit: "%" },
                  { label: "Cloud Adoption", val: cloudPct, set: setCloudPct, min: 0, max: 100, unit: "%" },
                  { label: "Onsite Server Fleet", val: onsiteServers, set: setOnsiteServers, min: 0, max: 200, unit: "units" },
                  { label: "Fleet Size (Vehicles)", val: fleetSize, set: setFleetSize, min: 0, max: 50, unit: "qty" },
                  { label: "Monthly Fuel Use", val: fuelUsage, set: setFuelUsage, min: 0, max: 5000, unit: "L" },
                ].map(s => (
                  <div key={s.label}>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                      <label style={{ fontSize: 11, fontWeight: 600, color: "var(--muted)", textTransform: "uppercase", letterSpacing: ".1em" }}>{s.label}</label>
                      <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 12, color: "var(--ink)" }}>{s.val}{s.unit}</span>
                    </div>
                    <input type="range" min={s.min} max={s.max} value={s.val} onChange={e => s.set(Number(e.target.value))} style={{ width: "100%", accentColor: "#2563EB" }} />
                  </div>
                ))}
              </div>

              <div style={{ marginTop: 40, padding: 20, background: "var(--g50)", borderRadius: 8, border: "1px solid var(--line)" }}>
                <div style={{ fontSize: 10, fontFamily: "JetBrains Mono", color: "var(--muted)", textTransform: "uppercase", marginBottom: 8 }}>[METHODOLOGY]</div>
                <p style={{ fontSize: 12, color: "var(--ink2)", lineHeight: 1.5, margin: 0 }}>
                  This simulation utilizes a dynamic weight model. Scope 2 is weighted towards grid intensity, while Scope 3 tracks the elasticity of remote work and cloud infrastructure offloading.
                </p>
              </div>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: 32 }}>
              
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 32 }}>
                <div style={{ background: "var(--white)", border: "1px solid var(--line)", borderRadius: 12, padding: 32, boxShadow: "var(--sh)" }}>
                  <h4 style={{ fontSize: 11, fontFamily: "JetBrains Mono", color: "var(--muted)", textTransform: "uppercase", marginBottom: 20, textAlign: "center" }}>Scope Weight Distribution</h4>
                  <div style={{ display: "flex", justifyContent: "center", marginBottom: 24 }}>
                    <PieChart s1={simulation.s1} s2={simulation.s2} s3={simulation.s3} />
                  </div>
                  <BarGraph s1={simulation.s1} s2={simulation.s2} s3={simulation.s3} />
                </div>

                <div style={{ background: "var(--white)", border: "1px solid var(--line)", borderRadius: 12, padding: 32, boxShadow: "var(--sh)" }}>
                  <h4 style={{ fontSize: 11, fontFamily: "JetBrains Mono", color: "var(--muted)", textTransform: "uppercase", marginBottom: 20 }}>Projected Performance</h4>
                  <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
                    <div style={{ borderBottom: "1px solid var(--line)", paddingBottom: 16 }}>
                      <div style={{ fontSize: 11, color: "var(--muted)", textTransform: "uppercase" }}>Annual Avoidance</div>
                      <div style={{ fontSize: 28, fontWeight: 600, color: simulation.avoidance >= 0 ? "#16A34A" : "#EF4444" }}>
                        {simulation.avoidance >= 0 ? "-" : "+"}{Math.abs(simulation.avoidance).toFixed(1)} tCO2e
                      </div>
                    </div>
                    <div style={{ borderBottom: "1px solid var(--line)", paddingBottom: 16 }}>
                      <div style={{ fontSize: 11, color: "var(--muted)", textTransform: "uppercase" }}>50-Year Total Impact</div>
                      <div style={{ fontSize: 28, fontWeight: 600, color: simulation.avoidance >= 0 ? "#2563EB" : "#EF4444" }}>
                        {simulation.avoidance >= 0 ? "-" : "+"}{Math.abs(simulation.avoidance * 50).toFixed(0)} tonnes
                      </div>
                    </div>
                    <div>
                      <div style={{ fontSize: 11, color: "var(--muted)", textTransform: "uppercase" }}>Strategic Efficiency</div>
                      <div style={{ fontSize: 28, fontWeight: 600, color: "var(--ink)" }}>
                        {((1 - simulation.total / baseAnn) * 100).toFixed(1)}%
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div style={{ background: "var(--white)", border: "1px solid var(--line)", borderRadius: 12, padding: 32, boxShadow: "var(--sh)" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 32 }}>
                  <h4 style={{ fontSize: 11, fontFamily: "JetBrains Mono", color: "var(--muted)", textTransform: "uppercase", margin: 0 }}>Carbon Projection (50 Years)</h4>
                  <div style={{ display: "flex", gap: 16, fontSize: 10, fontFamily: "JetBrains Mono" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 6 }}><span style={{ width: 12, height: 2, background: "#EF4444", borderBottom: "1px dashed" }} /> INDUSTRY PROJECTION (DO NOTHING)</div>
                    <div style={{ display: "flex", alignItems: "center", gap: 6 }}><span style={{ width: 12, height: 2, background: "#16A34A" }} /> STRATEGIC PATH</div>
                  </div>
                </div>
                <LineChart data={projectionData} />
                <p style={{ fontSize: 12, color: "var(--muted)", marginTop: 16, textAlign: "center" }}>
                  Comparison of strategic implementation against industry-standard 3% annual baseline growth and internal 2% business-as-usual projection.
                </p>
              </div>

            </div>
          </div>
        </div>
      </div>
    </>
  );
}
