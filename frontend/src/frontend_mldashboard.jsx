/**
 * MLDashboard.jsx
 * ================
 * Complete ML recommendation dashboard for Carbonaire.
 * Drop into your frontend/src/components/ directory.
 *
 * Features implemented:
 *   1. ML primary recommendation + confidence + priority
 *   2. Top-3 recommendations (de-duplicated, primary highlighted)
 *   3. Scope-wise recommendations (Scope 1 / 2 / 3)
 *   4. Personalization (user history tracking)
 *   5. Previous vs current comparison (delta tracking)
 *   6. XAI — explainable reason for each recommendation
 *   7. Priority colour system (red / orange / green)
 *   8. Dominant scope highlight
 *   9. Continuous learning status bar
 *
 * Props:
 *   mlData          — the `ml` object from /api/run response
 *   personalization — the `personalization` object from /api/run response (null if not logged in)
 *   learningStatus  — from GET /api/user/learning-status
 *   user            — current user object (null if not logged in)
 *   onLogin         — callback to open login modal
 */

import { useState, useEffect } from "react";

// ─── Colour helpers ───────────────────────────────────────────

const PRIORITY_STYLES = {
  HIGH: { border: "#DC2626", bg: "#FEF2F2", text: "#991B1B", dot: "#DC2626", label: "High priority" },
  MEDIUM: { border: "#D97706", bg: "#FFFBEB", text: "#92400E", dot: "#D97706", label: "Medium priority" },
  LOW: { border: "#16A34A", bg: "#F0FDF4", text: "#14532D", dot: "#16A34A", label: "Low priority" },
  MAINTAIN: { border: "#2563EB", bg: "#EFF6FF", text: "#1E3A8A", dot: "#2563EB", label: "Maintain" },
};

function priorityStyle(level) {
  return PRIORITY_STYLES[level] || PRIORITY_STYLES.LOW;
}

// ─── Sub-components ───────────────────────────────────────────

function PriorityBadge({ level, label, score }) {
  const s = priorityStyle(level);
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 5,
      background: s.bg, color: s.text, border: `1px solid ${s.border}`,
      borderRadius: 20, padding: "2px 10px", fontSize: 11, fontWeight: 600,
    }}>
      <span style={{ width: 6, height: 6, borderRadius: "50%", background: s.dot, flexShrink: 0 }} />
      {label || s.label} {score ? `(${score}/10)` : ""}
    </span>
  );
}

function ConfidenceBar({ pct, colour }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <div style={{ flex: 1, height: 5, background: "#E5E7EB", borderRadius: 3, overflow: "hidden" }}>
        <div style={{ width: `${pct}%`, height: "100%", background: colour || "#3B82F6", borderRadius: 3, transition: "width .5s" }} />
      </div>
      <span style={{ fontSize: 11, color: "#6B7280", minWidth: 32 }}>{pct}%</span>
    </div>
  );
}

function ScopeIcon({ scope }) {
  const icons = { scope1: "🔥", scope2: "⚡", scope3: "☁️" };
  return <span style={{ fontSize: 16 }}>{icons[scope] || "📊"}</span>;
}

function DeltaChip({ delta }) {
  const up = delta.direction === "increased";
  const good = delta.is_positive;
  const colour = good ? "#16A34A" : "#DC2626";
  return (
    <div style={{
      background: good ? "#F0FDF4" : "#FEF2F2",
      border: `1px solid ${colour}20`,
      borderRadius: 8, padding: "8px 12px",
      display: "flex", justifyContent: "space-between", alignItems: "center",
    }}>
      <span style={{ fontSize: 12, color: "#374151" }}>{delta.label}</span>
      <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
        <span style={{ fontSize: 11, color: "#6B7280" }}>
          {delta.prev_value} → {delta.curr_value} {delta.unit}
        </span>
        <span style={{ fontSize: 12, fontWeight: 600, color: colour }}>
          {up ? "↑" : "↓"} {delta.abs_pct}%
        </span>
      </div>
    </div>
  );
}

// ─── SECTION 1: ML Primary Recommendation ────────────────────

function PrimaryRecommendation({ ml }) {
  if (!ml?.ml_available) return null;
  const s = priorityStyle(ml.ml_priority_level);
  return (
    <div style={{
      border: `2px solid ${s.border}`, borderRadius: 12,
      background: s.bg, padding: "16px 20px", marginBottom: 16,
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 10 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{
            background: s.border, color: "#fff", borderRadius: 6,
            padding: "2px 8px", fontSize: 10, fontWeight: 700, letterSpacing: "0.06em",
          }}>AI RECOMMENDATION</span>
          <PriorityBadge level={ml.ml_priority_level} score={ml.ml_priority_score} />
        </div>
        <span style={{ fontSize: 12, color: "#6B7280" }}>
          {ml.ml_confidence}% confident
        </span>
      </div>
      <div style={{ fontWeight: 600, fontSize: 15, color: s.text, marginBottom: 6, textTransform: "capitalize" }}>
        {ml.ml_primary_recommendation?.replace(/_/g, " ")}
      </div>
      <p style={{ fontSize: 13, color: "#374151", lineHeight: 1.6, margin: "0 0 10px" }}>
        {ml.ml_primary_message}
      </p>
      {ml.ml_explanation && (
        <div style={{ background: "#fff8", borderLeft: `3px solid ${s.border}`, padding: "8px 12px", borderRadius: "0 6px 6px 0" }}>
          <span style={{ fontSize: 11, fontWeight: 600, color: s.text, display: "block", marginBottom: 2 }}>
            WHY THIS RECOMMENDATION
          </span>
          <span style={{ fontSize: 12, color: "#4B5563", lineHeight: 1.5 }}>
            {ml.ml_explanation}
          </span>
        </div>
      )}
    </div>
  );
}

// ─── SECTION 2: Top-3 Recommendations ───────────────────────

function Top3Recommendations({ ml }) {
  const top3 = ml?.ml_top3_recommendations;
  if (!top3?.length) return null;

  return (
    <div style={{ marginBottom: 16 }}>
      <div style={{ fontSize: 11, fontWeight: 600, color: "#6B7280", letterSpacing: "0.06em", marginBottom: 10 }}>
        ALL RECOMMENDATIONS — RANKED BY PRIORITY
      </div>
      {top3.map((rec, i) => {
        const s = priorityStyle(rec.priority_level);
        return (
          <div key={rec.recommendation} style={{
            border: rec.is_primary ? `1.5px solid ${s.border}` : "1px solid #E5E7EB",
            borderRadius: 10, padding: "12px 14px", marginBottom: 8,
            background: rec.is_primary ? s.bg : "#FAFAFA",
            position: "relative",
          }}>
            {rec.is_primary && (
              <span style={{
                position: "absolute", top: -9, left: 12,
                background: s.border, color: "#fff",
                fontSize: 9, fontWeight: 700, padding: "1px 7px", borderRadius: 10,
                letterSpacing: "0.06em",
              }}>TOP PICK</span>
            )}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 5 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{
                  width: 20, height: 20, borderRadius: "50%",
                  background: rec.is_primary ? s.border : "#D1D5DB",
                  color: rec.is_primary ? "#fff" : "#6B7280",
                  fontSize: 10, fontWeight: 700,
                  display: "flex", alignItems: "center", justifyContent: "center",
                }}>{i + 1}</span>
                <span style={{ fontWeight: 600, fontSize: 13, color: "#111827", textTransform: "capitalize" }}>
                  {rec.recommendation.replace(/_/g, " ")}
                </span>
              </div>
              <PriorityBadge level={rec.priority_level} label={rec.priority_label} />
            </div>
            <ConfidenceBar pct={rec.confidence} colour={s.border} />
            {rec.explanation && (
              <p style={{ fontSize: 11, color: "#6B7280", margin: "8px 0 0", lineHeight: 1.5 }}>
                {rec.explanation}
              </p>
            )}
          </div>
        );
      })}
    </div>
  );
}

// ─── SECTION 3: Scope-wise Recommendations ──────────────────

function ScopeRecommendations({ ml }) {
  const scopes = ml?.ml_scope_recommendations;
  if (!scopes) return null;
  const [open, setOpen] = useState(null);

  const items = [
    { key: "scope1", label: "Scope 1", sub: "Direct emissions" },
    { key: "scope2", label: "Scope 2", sub: "Electricity & energy" },
    { key: "scope3", label: "Scope 3", sub: "Value chain & cloud" },
  ];

  return (
    <div style={{ marginBottom: 16 }}>
      <div style={{ fontSize: 11, fontWeight: 600, color: "#6B7280", letterSpacing: "0.06em", marginBottom: 10 }}>
        SCOPE-WISE ACTION PLAN
      </div>
      {items.map(({ key, label, sub }) => {
        const rec = scopes[key];
        if (!rec) return null;
        const s = priorityStyle(rec.priority_level);
        const isOpen = open === key;
        return (
          <div key={key} style={{ border: "1px solid #E5E7EB", borderRadius: 10, marginBottom: 8, overflow: "hidden" }}>
            <button
              onClick={() => setOpen(isOpen ? null : key)}
              style={{
                width: "100%", background: isOpen ? s.bg : "#fff",
                border: "none", padding: "11px 14px", cursor: "pointer",
                display: "flex", alignItems: "center", gap: 10, textAlign: "left",
              }}
            >
              <ScopeIcon scope={key} />
              <div style={{ flex: 1 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <span style={{ fontWeight: 600, fontSize: 13, color: "#111827" }}>{label}</span>
                  <span style={{ fontSize: 11, color: "#6B7280" }}>{rec.scope_pct}% of total</span>
                </div>
                <span style={{ fontSize: 12, color: s.border, fontWeight: 500 }}>{rec.action}</span>
              </div>
              <PriorityBadge level={rec.priority_level} label={rec.priority_label} />
              <span style={{ fontSize: 12, color: "#9CA3AF" }}>{isOpen ? "▲" : "▼"}</span>
            </button>
            {isOpen && (
              <div style={{ padding: "0 14px 14px", background: s.bg }}>
                <p style={{ fontSize: 12, color: "#374151", lineHeight: 1.6, margin: "8px 0 0" }}>
                  {rec.detail}
                </p>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

// ─── SECTION 4+9: Personalization & Comparison ──────────────

function PersonalizationPanel({ personalization, user, onLogin }) {
  if (!user) {
    return (
      <div style={{
        border: "1.5px dashed #D1D5DB", borderRadius: 10, padding: "14px 16px",
        marginBottom: 16, background: "#F9FAFB", textAlign: "center",
      }}>
        <div style={{ fontSize: 14, color: "#374151", marginBottom: 6 }}>
          🔐 Log in to track your progress over time
        </div>
        <p style={{ fontSize: 12, color: "#6B7280", margin: "0 0 10px" }}>
          Get personalized comparisons like "You reduced electricity by 12% since last month"
        </p>
        <button onClick={onLogin} style={{
          background: "#1D4ED8", color: "#fff", border: "none",
          borderRadius: 8, padding: "7px 18px", fontSize: 13, cursor: "pointer",
        }}>Log in / Sign up</button>
      </div>
    );
  }

  if (!personalization?.has_previous) {
    return (
      <div style={{
        border: "1px solid #E5E7EB", borderRadius: 10, padding: "12px 14px",
        marginBottom: 16, background: "#F0FDF4",
      }}>
        <span style={{ fontSize: 13, color: "#166534" }}>
          ✅ First assessment saved! Run again after changes to see your progress.
        </span>
      </div>
    );
  }

  const p = personalization;
  const emDir = p.emission_direction;
  const emGood = emDir === "decreased";

  return (
    <div style={{ border: "1px solid #E5E7EB", borderRadius: 12, marginBottom: 16, overflow: "hidden" }}>
      <div style={{
        background: emGood ? "#F0FDF4" : "#FEF2F2",
        borderBottom: "1px solid #E5E7EB",
        padding: "10px 14px",
        display: "flex", justifyContent: "space-between", alignItems: "center",
      }}>
        <span style={{ fontWeight: 600, fontSize: 13, color: emGood ? "#166534" : "#991B1B" }}>
          {emGood ? "📉" : "📈"} Emissions {emDir} by {Math.abs(p.emission_delta_pct)}% since last run
        </span>
        <span style={{ fontSize: 11, color: "#6B7280" }}>vs {p.prev_assessment_date}</span>
      </div>
      <div style={{ padding: "10px 14px" }}>
        <div style={{ display: "flex", gap: 12, marginBottom: 10 }}>
          <div style={{ flex: 1, background: "#F9FAFB", borderRadius: 8, padding: "8px 12px", textAlign: "center" }}>
            <div style={{ fontSize: 11, color: "#6B7280" }}>Previous</div>
            <div style={{ fontWeight: 700, fontSize: 18, color: "#374151" }}>{p.prev_tco2e}</div>
            <div style={{ fontSize: 10, color: "#9CA3AF" }}>tCO₂e/month</div>
          </div>
          <div style={{ display: "flex", alignItems: "center", fontSize: 18 }}>→</div>
          <div style={{ flex: 1, background: emGood ? "#F0FDF4" : "#FEF2F2", borderRadius: 8, padding: "8px 12px", textAlign: "center" }}>
            <div style={{ fontSize: 11, color: "#6B7280" }}>Current</div>
            <div style={{ fontWeight: 700, fontSize: 18, color: emGood ? "#166534" : "#991B1B" }}>{p.curr_tco2e}</div>
            <div style={{ fontSize: 10, color: "#9CA3AF" }}>tCO₂e/month</div>
          </div>
        </div>
        {p.deltas?.slice(0, 4).map(d => <DeltaChip key={d.field} delta={d} />)}
        {p.deltas?.length > 4 && (
          <p style={{ fontSize: 11, color: "#6B7280", textAlign: "center", marginTop: 6 }}>
            +{p.deltas.length - 4} more changes
          </p>
        )}
      </div>
    </div>
  );
}

// ─── SECTION 8: Dominant Scope ───────────────────────────────

function DominantScope({ ml }) {
  const dom = ml?.ml_dominant_scope;
  if (!dom) return null;
  return (
    <div style={{
      display: "flex", alignItems: "center", gap: 10,
      background: dom.bg || "#EFF6FF",
      border: `1px solid ${dom.colour || "#2563EB"}30`,
      borderRadius: 10, padding: "10px 14px", marginBottom: 16,
    }}>
      <ScopeIcon scope={dom.key} />
      <div>
        <div style={{ fontWeight: 600, fontSize: 13, color: dom.colour || "#1D4ED8" }}>
          Main emission source: {dom.scope} ({dom.pct?.toFixed(1)}%)
        </div>
        <div style={{ fontSize: 11, color: "#6B7280" }}>{dom.description}</div>
      </div>
    </div>
  );
}

// ─── SECTION 5: Continuous Learning Bar ─────────────────────

function LearningStatus({ status }) {
  if (!status) return null;
  return (
    <div style={{
      border: "1px solid #E5E7EB", borderRadius: 10, padding: "10px 14px", marginBottom: 16,
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
        <span style={{ fontSize: 12, fontWeight: 600, color: "#374151" }}>🤖 Continuous Learning</span>
        <span style={{ fontSize: 11, color: "#6B7280" }}>
          {status.samples_until_retrain} samples until next retrain
        </span>
      </div>
      <div style={{ height: 5, background: "#E5E7EB", borderRadius: 3, overflow: "hidden" }}>
        <div style={{
          width: `${status.progress_pct}%`, height: "100%",
          background: "linear-gradient(90deg, #3B82F6, #06B6D4)",
          borderRadius: 3, transition: "width .5s",
        }} />
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", marginTop: 4 }}>
        <span style={{ fontSize: 10, color: "#9CA3AF" }}>
          {status.logged_samples} real samples logged
        </span>
        <span style={{ fontSize: 10, color: "#9CA3AF" }}>
          Next retrain at {status.next_retrain_at}
        </span>
      </div>
    </div>
  );
}

// ─── Cluster Badge ────────────────────────────────────────────

function ClusterBadge({ ml }) {
  if (!ml?.ml_cluster_description) return null;
  return (
    <div style={{
      background: "#F8FAFC", border: "1px solid #CBD5E1",
      borderRadius: 10, padding: "9px 14px", marginBottom: 16,
      display: "flex", alignItems: "center", gap: 8,
    }}>
      <span style={{ fontSize: 13 }}>🏷️</span>
      <div>
        <div style={{ fontSize: 10, color: "#94A3B8", fontWeight: 600, letterSpacing: "0.06em" }}>
          EMISSION ARCHETYPE
        </div>
        <div style={{ fontSize: 12, color: "#334155" }}>{ml.ml_cluster_description}</div>
      </div>
    </div>
  );
}

// ─── MAIN EXPORT ─────────────────────────────────────────────

export default function MLDashboard({
  mlData,
  personalization,
  learningStatus,
  user,
  onLogin,
}) {
  if (!mlData) return null;

  return (
    <div style={{ fontFamily: "system-ui, -apple-system, sans-serif", maxWidth: 640 }}>

      {/* 8. Dominant scope */}
      <DominantScope ml={mlData} />

      {/* 1. ML primary recommendation + XAI */}
      <PrimaryRecommendation ml={mlData} />

      {/* 2. Top-3 (de-duplicated) */}
      <Top3Recommendations ml={mlData} />

      {/* 3. Scope-wise action plan */}
      <ScopeRecommendations ml={mlData} />

      {/* Cluster archetype */}
      <ClusterBadge ml={mlData} />

      {/* 4+9. Personalization + comparison */}
      <PersonalizationPanel
        personalization={personalization}
        user={user}
        onLogin={onLogin}
      />

      {/* 5. Continuous learning */}
      <LearningStatus status={learningStatus} />
    </div>
  );
}

// ─── Usage example ────────────────────────────────────────────
/*
import MLDashboard from "./components/MLDashboard";

// After calling POST /api/run:
const { ml, personalization } = apiResponse;

// After calling GET /api/user/learning-status:
const learningStatus = learningStatusResponse;

<MLDashboard
  mlData={ml}
  personalization={personalization}
  learningStatus={learningStatus}
  user={currentUser}
  onLogin={() => setLoginModalOpen(true)}
/>
*/
