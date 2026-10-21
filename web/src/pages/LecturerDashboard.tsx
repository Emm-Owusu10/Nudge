import { useEffect, useState, type FormEvent } from "react";
import Layout from "../components/Layout";
import { ApiError } from "../api/client";
import { listMyCourses, listRoster, type Course, type RosterStudent } from "../api/courses";
import {
  recordAssessment,
  recordAttendance,
  type AttendanceStatus,
} from "../api/records";
import { useAuth } from "../auth/AuthContext";

const DEFAULT_TERM = "2026-S1";
const DEFAULT_DATE = "2026-10-19";
const ATTENDANCE_OPTIONS: AttendanceStatus[] = ["present", "absent", "late", "excused"];

type Mode = "attendance" | "assessments";

export default function LecturerDashboard() {
  const { user } = useAuth();
  const token = sessionStorage.getItem("ei_access_token") ?? "";

  const [courses, setCourses] = useState<Course[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [term, setTerm] = useState(DEFAULT_TERM);
  const [roster, setRoster] = useState<RosterStudent[]>([]);
  const [loadingCourses, setLoadingCourses] = useState(true);
  const [loadingRoster, setLoadingRoster] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [mode, setMode] = useState<Mode>("attendance");
  const [saving, setSaving] = useState(false);
  const [summary, setSummary] = useState<string | null>(null);
  const [rowMessages, setRowMessages] = useState<Record<number, string>>({});

  // Attendance state
  const [sessionDate, setSessionDate] = useState(DEFAULT_DATE);
  const [attendance, setAttendance] = useState<Record<number, AttendanceStatus>>({});

  // Assessment state
  const [assessmentTitle, setAssessmentTitle] = useState("");
  const [assessedOn, setAssessedOn] = useState(DEFAULT_DATE);
  const [scores, setScores] = useState<Record<number, string>>({});

  useEffect(() => {
    listMyCourses(token)
      .then((list) => {
        setCourses(list);
        if (list.length > 0) setSelectedId(list[0].id);
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : "Could not load your courses."))
      .finally(() => setLoadingCourses(false));
  }, [token]);

  useEffect(() => {
    if (selectedId === null) return;
    setLoadingRoster(true);
    setError(null);
    listRoster(token, selectedId, term)
      .then(setRoster)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Could not load the roster."))
      .finally(() => setLoadingRoster(false));
  }, [token, selectedId, term]);

  // Changing course or term clears the entry forms so values can't be saved to the wrong course.
  useEffect(() => {
    setAttendance({});
    setScores({});
    setRowMessages({});
    setSummary(null);
  }, [selectedId, term]);

  const selectedCourse = courses.find((course) => course.id === selectedId);

  async function saveAttendance(event: FormEvent) {
    event.preventDefault();
    if (selectedId === null) return;
    setSaving(true);
    setSummary(null);
    const messages: Record<number, string> = {};
    let saved = 0;
    let alreadyRecorded = 0;
    let failed = 0;

    for (const student of roster) {
      const status = attendance[student.id] ?? "present";
      try {
        await recordAttendance(token, student.id, selectedId, sessionDate, status);
        messages[student.id] = "Saved";
        saved += 1;
      } catch (err) {
        if (err instanceof ApiError && err.status === 409) {
          messages[student.id] = "Already recorded for this date";
          alreadyRecorded += 1;
        } else {
          messages[student.id] = err instanceof ApiError ? err.message : "Could not save";
          failed += 1;
        }
      }
    }

    setRowMessages(messages);
    setSummary(`Saved ${saved}. Already recorded ${alreadyRecorded}. Failed ${failed}.`);
    setSaving(false);
  }

  async function saveAssessments(event: FormEvent) {
    event.preventDefault();
    if (selectedId === null) return;
    if (!assessmentTitle.trim()) {
      setSummary("Enter a title for this assessment first.");
      return;
    }

    const entries = roster.filter((student) => (scores[student.id] ?? "").trim() !== "");
    if (entries.length === 0) {
      setSummary("Enter at least one score.");
      return;
    }

    setSaving(true);
    setSummary(null);
    const messages: Record<number, string> = {};
    let saved = 0;
    let failed = 0;

    for (const student of entries) {
      const raw = (scores[student.id] ?? "").trim();
      const score = Number(raw);
      if (!Number.isInteger(score) || score < 0 || score > 100) {
        messages[student.id] = "Score must be a whole number from 0 to 100";
        failed += 1;
        continue;
      }
      try {
        await recordAssessment(token, student.id, selectedId, assessmentTitle.trim(), assessedOn, score);
        messages[student.id] = "Saved";
        saved += 1;
      } catch (err) {
        messages[student.id] = err instanceof ApiError ? err.message : "Could not save";
        failed += 1;
      }
    }

    setRowMessages(messages);
    setSummary(`Saved ${saved}. Failed ${failed}. Students left blank were skipped.`);
    setSaving(false);
  }

  return (
    <Layout title="Lecturer dashboard">
      <div className="card">
        <h2>My courses</h2>
        <p className="muted">
          Courses you teach. You can see and update records only for students enrolled in these courses.
        </p>

        {loadingCourses ? (
          <p className="muted">Loading your courses…</p>
        ) : courses.length === 0 ? (
          <p className="muted">You are not linked to any courses yet. Ask an administrator to assign you.</p>
        ) : (
          <div className="course-list">
            {courses.map((course) => (
              <button
                key={course.id}
                className={`button small ${course.id === selectedId ? "primary" : "secondary"}`}
                onClick={() => setSelectedId(course.id)}
              >
                {course.code} · {course.title}
              </button>
            ))}
          </div>
        )}
      </div>

      {error && <p className="error card">{error}</p>}

      {selectedCourse && (
        <div className="card section">
          <div className="toolbar">
            <div>
              <h3>
                {selectedCourse.code}: {selectedCourse.title}
              </h3>
              <div className="view-toggle" role="tablist">
                <button
                  role="tab"
                  aria-selected={mode === "attendance"}
                  className={`button small ${mode === "attendance" ? "primary" : "secondary"}`}
                  onClick={() => setMode("attendance")}
                >
                  Attendance
                </button>
                <button
                  role="tab"
                  aria-selected={mode === "assessments"}
                  className={`button small ${mode === "assessments" ? "primary" : "secondary"}`}
                  onClick={() => setMode("assessments")}
                >
                  Assessments
                </button>
              </div>
            </div>
            <label className="field inline">
              <span>Academic term</span>
              <input value={term} onChange={(e) => setTerm(e.target.value)} placeholder="2026-S1" />
            </label>
          </div>

          {loadingRoster ? (
            <p className="muted">Loading roster…</p>
          ) : roster.length === 0 ? (
            <p className="muted">No students are enrolled in this course for {term}.</p>
          ) : mode === "attendance" ? (
            <form onSubmit={saveAttendance} className="stack">
              <label className="field inline">
                <span>Session date</span>
                <input type="date" value={sessionDate} onChange={(e) => setSessionDate(e.target.value)} required />
              </label>
              <RosterTable
                roster={roster}
                messages={rowMessages}
                renderInput={(student) => (
                  <select
                    value={attendance[student.id] ?? "present"}
                    onChange={(e) =>
                      setAttendance((current) => ({
                        ...current,
                        [student.id]: e.target.value as AttendanceStatus,
                      }))
                    }
                  >
                    {ATTENDANCE_OPTIONS.map((option) => (
                      <option key={option} value={option}>
                        {option}
                      </option>
                    ))}
                  </select>
                )}
              />
              <button className="button primary small" type="submit" disabled={saving}>
                {saving ? "Saving…" : "Save attendance for this date"}
              </button>
              {summary && <p className="muted small-print">{summary}</p>}
            </form>
          ) : (
            <form onSubmit={saveAssessments} className="stack">
              <div className="toolbar-actions">
                <label className="field inline">
                  <span>Assessment title</span>
                  <input
                    value={assessmentTitle}
                    onChange={(e) => setAssessmentTitle(e.target.value)}
                    placeholder="For example Midterm"
                    maxLength={120}
                    required
                  />
                </label>
                <label className="field inline">
                  <span>Date</span>
                  <input type="date" value={assessedOn} onChange={(e) => setAssessedOn(e.target.value)} required />
                </label>
              </div>
              <RosterTable
                roster={roster}
                messages={rowMessages}
                renderInput={(student) => (
                  <input
                    className="score-input"
                    inputMode="numeric"
                    placeholder="0–100"
                    value={scores[student.id] ?? ""}
                    onChange={(e) =>
                      setScores((current) => ({ ...current, [student.id]: e.target.value }))
                    }
                  />
                )}
              />
              <button className="button primary small" type="submit" disabled={saving}>
                {saving ? "Saving…" : "Save scores"}
              </button>
              {summary && <p className="muted small-print">{summary}</p>}
            </form>
          )}
        </div>
      )}

      <p className="muted small-print">Signed in as {user?.username}.</p>
    </Layout>
  );
}

function RosterTable({
  roster,
  messages,
  renderInput,
}: {
  roster: RosterStudent[];
  messages: Record<number, string>;
  renderInput: (student: RosterStudent) => React.ReactNode;
}) {
  return (
    <table className="queue">
      <thead>
        <tr>
          <th>Student number</th>
          <th>Name</th>
          <th>Entry</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        {roster.map((student) => (
          <tr key={student.id}>
            <td>
              <strong>{student.student_number}</strong>
            </td>
            <td>{student.full_name}</td>
            <td>{renderInput(student)}</td>
            <td className="muted">{messages[student.id] ?? ""}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}