import { useCallback, useEffect, useState, type FormEvent } from "react";
import { Link, useParams } from "react-router-dom";
import Layout from "../components/Layout";
import { ApiError } from "../api/client";
import {
  createIntervention,
  getFollowUp,
  listInterventions,
  recordOutcome,
  type FollowUp,
  type Intervention,
  type InterventionType,
  type Outcome,
} from "../api/interventions";
import {
  getIndicators,
  getStudent,
  listStudentFlags,
  type Indicators,
  type StudentDetail as Student,
  type StudentFlag,
} from "../api/students";
import { useAuth } from "../auth/AuthContext";

const DEFAULT_AS_OF = "2026-10-19";

const INTERVENTION_TYPES: { value: InterventionType; label: string }[] = [
  { value: "meeting", label: "Meeting" },
  { value: "study_plan", label: "Study plan" },
  { value: "tutoring_referral", label: "Tutoring referral" },
  { value: "wellbeing_referral", label: "Wellbeing referral" },
  { value: "other", label: "Other" },
];

const OUTCOMES: { value: Outcome; label: string }[] = [
  { value: "improving", label: "Improving" },
  { value: "no_change", label: "No change" },
  { value: "referred_elsewhere", label: "Referred elsewhere" },
];

function percent(value: number | null): string {
  return value === null ? "Not enough data" : `${Math.round(value * 100)}%`;
}

function label(value: string): string {
  return value.replace(/_/g, " ");
}

export default function StudentDetail() {
  const { id } = useParams();
  const studentId = Number(id);
  const token = sessionStorage.getItem("ei_access_token") ?? "";
  const { user } = useAuth();

  const [student, setStudent] = useState<Student | null>(null);
  const [indicators, setIndicators] = useState<Indicators | null>(null);
  const [flags, setFlags] = useState<StudentFlag[]>([]);
  const [interventions, setInterventions] = useState<Intervention[]>([]);
  const [followUps, setFollowUps] = useState<Record<number, FollowUp>>({});
  const [error, setError] = useState<string | null>(null);

  const loadInterventions = useCallback(async () => {
    const list = await listInterventions(token, studentId);
    setInterventions(list);
    const details = await Promise.all(list.map((item) => getFollowUp(token, item.id)));
    const byId: Record<number, FollowUp> = {};
    details.forEach((detail) => {
      byId[detail.intervention_id] = detail;
    });
    setFollowUps(byId);
  }, [token, studentId]);

  useEffect(() => {
    if (!Number.isInteger(studentId)) {
      setError("This student link is not valid.");
      return;
    }
    Promise.all([
      getStudent(token, studentId),
      getIndicators(token, studentId, DEFAULT_AS_OF),
      listStudentFlags(token, studentId),
      loadInterventions(),
    ])
      .then(([studentData, indicatorData, flagData]) => {
        setStudent(studentData);
        setIndicators(indicatorData);
        setFlags(flagData);
      })
      .catch((err) => {
        setError(err instanceof ApiError ? err.message : "Could not load this student.");
      });
  }, [studentId, token, loadInterventions]);

  return (
    <Layout title="Student detail">
      <p>
        <Link to="/advisor">← Back to the flag queue</Link>
      </p>

      {error && <p className="error card">{error}</p>}

      {student && (
        <>
          <div className="card">
            <h2>{student.full_name}</h2>
            <p className="muted">
              {student.student_number} · {student.programme}
            </p>
          </div>

          {indicators && (
            <div className="card section">
              <h3>Indicators as of {indicators.as_of}</h3>
              <div className="metrics">
                <Metric
                  label="Attendance, last 4 weeks"
                  value={percent(indicators.attendance_recent.rate)}
                  note={`${indicators.attendance_recent.sessions_counted} sessions counted`}
                />
                <Metric
                  label="Attendance, previous 4 weeks"
                  value={percent(indicators.attendance_earlier.rate)}
                  note={`${indicators.attendance_earlier.sessions_counted} sessions counted`}
                />
                <Metric
                  label="Missing assignments"
                  value={`${indicators.missing_assignments.missing} of ${indicators.missing_assignments.considered}`}
                  note="Among the five most recent"
                />
                <Metric
                  label="Recent average score"
                  value={
                    indicators.grades.recent_average === null
                      ? "Not enough data"
                      : indicators.grades.recent_average.toFixed(0)
                  }
                  note={
                    indicators.grades.earlier_average === null
                      ? "Earlier average not available"
                      : `Earlier average ${indicators.grades.earlier_average.toFixed(0)}`
                  }
                />
              </div>
            </div>
          )}

          <div className="card section">
            <h3>Flag history</h3>
            {flags.length === 0 ? (
              <p className="muted">No flags have been raised for this student.</p>
            ) : (
              <ul className="flag-list">
                {flags.map((flag) => (
                  <li key={flag.id}>
                    <div>
                      <span className={`badge ${levelClass(flag.level)}`}>{flag.level}</span>{" "}
                      <span className="muted">
                        as of {flag.as_of} · {flag.status}
                      </span>
                    </div>
                    <ul className="reasons">
                      {flag.factors.map((factor) => (
                        <li key={factor.code}>{factor.message}</li>
                      ))}
                    </ul>
                    {flag.status === "dismissed" && flag.dismissal_reason && (
                      <p className="muted">Dismissed: {flag.dismissal_reason}</p>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="card section">
            <h3>Interventions</h3>
            {interventions.length === 0 ? (
              <p className="muted">No interventions recorded yet.</p>
            ) : (
              <ul className="flag-list">
                {interventions.map((item) => (
                  <InterventionRow
                    key={item.id}
                    intervention={item}
                    followUp={followUps[item.id]}
                    token={token}
                    canRecordOutcome={user?.role === "advisor"}
                    onChanged={loadInterventions}
                    onError={setError}
                  />
                ))}
              </ul>
            )}
          </div>

          <NewInterventionForm
            token={token}
            studentId={studentId}
            flags={flags.filter((flag) => flag.status === "open")}
            onCreated={loadInterventions}
            onError={setError}
          />
        </>
      )}
    </Layout>
  );
}

function InterventionRow({
  intervention,
  followUp,
  token,
  canRecordOutcome,
  onChanged,
  onError,
}: {
  intervention: Intervention;
  followUp: FollowUp | undefined;
  token: string;
  canRecordOutcome: boolean;
  onChanged: () => Promise<void>;
  onError: (message: string) => void;
}) {
  const [outcome, setOutcome] = useState<Outcome>("improving");
  const [saving, setSaving] = useState(false);

  async function handleOutcome(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    try {
      await recordOutcome(token, intervention.id, outcome);
      await onChanged();
    } catch (err) {
      onError(err instanceof ApiError ? err.message : "Could not record the outcome.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <li>
      <div>
        <strong>{label(intervention.intervention_type)}</strong>{" "}
        <span className="muted">
          on {intervention.intervention_date} · follow-up due {intervention.follow_up_due}
        </span>
      </div>
      {intervention.notes && <p>{intervention.notes}</p>}
      <p className="muted">Outcome: {label(intervention.outcome)}</p>

      {followUp && (
        <div className="followup">
          {!followUp.is_due && (
            <p className="muted small-print">
              The follow-up date has not arrived. The after-values cover only part of the window.
            </p>
          )}
          <p>
            Attendance, last 4 weeks: <strong>{percent(followUp.before.attendance_recent.rate)}</strong>{" "}
            at the intervention, <strong>{percent(followUp.after.attendance_recent.rate)}</strong> at
            follow-up.
          </p>
        </div>
      )}

      {canRecordOutcome && (
        <form className="inline-form" onSubmit={handleOutcome}>
          <select value={outcome} onChange={(e) => setOutcome(e.target.value as Outcome)}>
            {OUTCOMES.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          <button className="button secondary small" type="submit" disabled={saving}>
            {saving ? "Saving…" : "Record outcome"}
          </button>
        </form>
      )}
    </li>
  );
}

function NewInterventionForm({
  token,
  studentId,
  flags,
  onCreated,
  onError,
}: {
  token: string;
  studentId: number;
  flags: StudentFlag[];
  onCreated: () => Promise<void>;
  onError: (message: string) => void;
}) {
  const [type, setType] = useState<InterventionType>("meeting");
  const [date, setDate] = useState(DEFAULT_AS_OF);
  const [notes, setNotes] = useState("");
  const [flagId, setFlagId] = useState<string>("");
  const [saving, setSaving] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    try {
      await createIntervention(token, studentId, {
        intervention_type: type,
        intervention_date: date,
        notes: notes.trim() || null,
        flag_id: flagId ? Number(flagId) : null,
      });
      setNotes("");
      setFlagId("");
      await onCreated();
    } catch (err) {
      onError(err instanceof ApiError ? err.message : "Could not record the intervention.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="card section">
      <h3>Record an intervention</h3>
      <form onSubmit={handleSubmit} className="stack">
        <label className="field">
          <span>Type</span>
          <select value={type} onChange={(e) => setType(e.target.value as InterventionType)}>
            {INTERVENTION_TYPES.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span>Date</span>
          <input type="date" value={date} onChange={(e) => setDate(e.target.value)} required />
        </label>
        <label className="field">
          <span>Linked flag (optional)</span>
          <select value={flagId} onChange={(e) => setFlagId(e.target.value)}>
            <option value="">No linked flag</option>
            {flags.map((flag) => (
              <option key={flag.id} value={flag.id}>
                {flag.level}, as of {flag.as_of}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span>Notes (optional)</span>
          <textarea value={notes} onChange={(e) => setNotes(e.target.value)} maxLength={2000} rows={3} />
        </label>
        <button className="button primary small" type="submit" disabled={saving}>
          {saving ? "Saving…" : "Record intervention"}
        </button>
      </form>
    </div>
  );
}

function Metric({ label, value, note }: { label: string; value: string; note: string }) {
  return (
    <div className="metric">
      <span className="muted">{label}</span>
      <strong>{value}</strong>
      <span className="muted small-print">{note}</span>
    </div>
  );
}

function levelClass(level: StudentFlag["level"]): string {
  if (level === "priority review") return "badge-priority";
  if (level === "review recommended") return "badge-review";
  return "badge-monitor";
}