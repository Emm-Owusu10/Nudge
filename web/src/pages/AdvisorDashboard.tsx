import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Layout from "../components/Layout";
import StudentSearch from "../components/StudentSearch";
import { ApiError } from "../api/client";
import {
  dismissFlag,
  evaluateStudent,
  listDismissedDetails,
  listOpenFlags,
  listStudents,
  type DismissedDetail,
  type QueueItem,
} from "../api/flags";
import { useAuth } from "../auth/AuthContext";

const DEFAULT_AS_OF = "2026-10-19";

const LEVEL_STYLE: Record<QueueItem["level"], string> = {
  "priority review": "badge badge-priority",
  "review recommended": "badge badge-review",
  monitor: "badge badge-monitor",
};

type QueueView = "open" | "dismissed";

export default function AdvisorDashboard() {
  const { user } = useAuth();
  const token = sessionStorage.getItem("ei_access_token") ?? "";

  const [asOf, setAsOf] = useState(DEFAULT_AS_OF);
  const [view, setView] = useState<QueueView>("open");
  const [items, setItems] = useState<QueueItem[]>([]);
  const [dismissed, setDismissed] = useState<Record<number, DismissedDetail>>({});
  const [loading, setLoading] = useState(true);
  const [progress, setProgress] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reasonFor, setReasonFor] = useState<Record<number, string>>({});

  const loadQueue = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const rows = await listOpenFlags(token, asOf, view);
      setItems(rows);
      if (view === "dismissed") {
        const studentIds = [...new Set(rows.map((row) => row.student_id))];
        setDismissed(await listDismissedDetails(token, studentIds, asOf));
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load the queue.");
    } finally {
      setLoading(false);
    }
  }, [token, asOf, view]);

  useEffect(() => {
    loadQueue();
  }, [loadQueue]);

  async function handleEvaluateAll() {
    setError(null);
    try {
      const students = await listStudents(token);
      for (let index = 0; index < students.length; index += 1) {
        setProgress(`Evaluating ${index + 1} of ${students.length}…`);
        await evaluateStudent(token, students[index].id, asOf);
      }
      setProgress(null);
      await loadQueue();
    } catch (err) {
      setProgress(null);
      setError(err instanceof ApiError ? err.message : "Evaluation stopped unexpectedly.");
    }
  }

  async function handleDismiss(flagId: number) {
    const reason = (reasonFor[flagId] ?? "").trim();
    if (!reason) {
      setError("A reason is required to dismiss a flag.");
      return;
    }
    try {
      await dismissFlag(token, flagId, reason);
      setItems((current) => current.filter((item) => item.flag_id !== flagId));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not dismiss the flag.");
    }
  }

  const isDismissedView = view === "dismissed";

  return (
    <Layout title="Advisor dashboard">
      <StudentSearch token={token} />

      <div className="card toolbar">
        <div>
          <h2>Flag queue</h2>
          <div className="view-toggle" role="tablist">
            <button
              role="tab"
              aria-selected={view === "open"}
              className={`button small ${view === "open" ? "primary" : "secondary"}`}
              onClick={() => setView("open")}
            >
              Open
            </button>
            <button
              role="tab"
              aria-selected={view === "dismissed"}
              className={`button small ${view === "dismissed" ? "primary" : "secondary"}`}
              onClick={() => setView("dismissed")}
            >
              Dismissed
            </button>
          </div>
          <p className="muted">
            {isDismissedView
              ? "Dismissed flags are kept as a record of the advisor's decision. They are read-only."
              : "Flags describe patterns for human review. They do not predict outcomes."}
          </p>
        </div>
        <div className="toolbar-actions">
          <label className="field inline">
            <span>Evaluation date</span>
            <input type="date" value={asOf} onChange={(e) => setAsOf(e.target.value)} />
          </label>
          <button className="button primary small" onClick={handleEvaluateAll} disabled={!!progress}>
            {progress ?? "Evaluate all students"}
          </button>
        </div>
      </div>

      {error && <p className="error card">{error}</p>}

      <div className="card">
        {loading ? (
          <p className="muted">Loading queue…</p>
        ) : items.length === 0 ? (
          <p className="muted">
            {isDismissedView
              ? `No dismissed flags for ${asOf}.`
              : `No open flags for ${asOf}. Choose “Evaluate all students” to run the rules for this date.`}
          </p>
        ) : (
          <table className="queue">
            <thead>
              <tr>
                <th>Student</th>
                <th>Level</th>
                <th>Reasons</th>
                <th>{isDismissedView ? "Dismissal" : "Dismiss"}</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.flag_id}>
                  <td>
                    <strong>{item.student_number}</strong>
                    <div className="muted">{item.full_name}</div>
                    <Link to={`/advisor/students/${item.student_id}`}>View student</Link>
                  </td>
                  <td>
                    <span className={LEVEL_STYLE[item.level]}>{item.level}</span>
                  </td>
                  <td>
                    <ul className="reasons">
                      {item.factors.map((factor) => (
                        <li key={factor.code}>{factor.message}</li>
                      ))}
                    </ul>
                  </td>
                  <td>
                    {isDismissedView ? (
                      <div>
                        <p>{dismissed[item.flag_id]?.dismissal_reason ?? "No reason recorded"}</p>
                        {dismissed[item.flag_id]?.dismissed_at && (
                          <p className="muted small-print">
                            {new Date(dismissed[item.flag_id].dismissed_at as string).toLocaleDateString()}
                          </p>
                        )}
                      </div>
                    ) : (
                      <>
                        <input
                          className="reason-input"
                          placeholder="Reason"
                          value={reasonFor[item.flag_id] ?? ""}
                          onChange={(e) =>
                            setReasonFor((current) => ({ ...current, [item.flag_id]: e.target.value }))
                          }
                        />
                        <button
                          className="button secondary small"
                          onClick={() => handleDismiss(item.flag_id)}
                        >
                          Dismiss
                        </button>
                      </>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <p className="muted small-print">Signed in as {user?.username}.</p>
    </Layout>
  );
}