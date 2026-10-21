import { useEffect, useState, type FormEvent } from "react";
import Layout from "../components/Layout";
import { ApiError } from "../api/client";
import { listStudents, type Student } from "../api/flags";
import { listAllCourses, type Course } from "../api/courses";
import {
  createCourse,
  createStudent,
  enrolStudent,
  listAuditLog,
  updateCourse,
  updateStudent,
  type AuditEntry,
} from "../api/admin";
import { useAuth } from "../auth/AuthContext";

const DEFAULT_TERM = "2026-S1";

export default function AdminDashboard() {
  const { user } = useAuth();
  const token = sessionStorage.getItem("ei_access_token") ?? "";

  const [students, setStudents] = useState<Student[]>([]);
  const [courses, setCourses] = useState<Course[]>([]);
  const [auditEntries, setAuditEntries] = useState<AuditEntry[]>([]);
  const [auditStudentId, setAuditStudentId] = useState<number | null>(null);
  const [message, setMessage] = useState<{ kind: "ok" | "error"; text: string } | null>(null);

  async function refresh() {
    try {
      const [studentRows, courseRows] = await Promise.all([
        listStudents(token),
        listAllCourses(token),
      ]);
      setStudents(studentRows);
      setCourses(courseRows);
    } catch (err) {
      setMessage({ kind: "error", text: err instanceof ApiError ? err.message : "Could not load data." });
    }
  }

  async function refreshAudit(studentId: number | null) {
    try {
      setAuditEntries(await listAuditLog(token, studentId));
    } catch (err) {
      setMessage({ kind: "error", text: err instanceof ApiError ? err.message : "Could not load the audit log." });
    }
  }

  useEffect(() => {
    refresh();
    refreshAudit(null);
    // Load once on sign-in; each section refreshes after its own changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  function report(kind: "ok" | "error", text: string) {
    setMessage({ kind, text });
  }

  return (
    <Layout title="Administration">
      {message && <p className={message.kind === "error" ? "error card" : "card success"}>{message.text}</p>}

      <div className="grid-two">
        <CreateStudentForm
          token={token}
          onDone={async (text) => {
            report("ok", text);
            await refresh();
            await refreshAudit(auditStudentId);
          }}
          onError={(text) => report("error", text)}
        />
        <CreateCourseForm
          token={token}
          onDone={async (text) => {
            report("ok", text);
            await refresh();
            await refreshAudit(auditStudentId);
          }}
          onError={(text) => report("error", text)}
        />
      </div>

      <div className="grid-two">
        <CorrectStudentForm
          token={token}
          students={students}
          onDone={async (text) => {
            report("ok", text);
            await refresh();
            await refreshAudit(auditStudentId);
          }}
          onError={(text) => report("error", text)}
        />
        <CorrectCourseForm
          token={token}
          courses={courses}
          onDone={async (text) => {
            report("ok", text);
            await refresh();
            await refreshAudit(auditStudentId);
          }}
          onError={(text) => report("error", text)}
        />
      </div>

      <EnrolForm
        token={token}
        students={students}
        courses={courses}
        onDone={async (text) => {
          report("ok", text);
          await refreshAudit(auditStudentId);
        }}
        onError={(text) => report("error", text)}
      />

      <div className="card section">
        <div className="toolbar">
          <h3>Audit log</h3>
          <label className="field inline">
            <span>Filter by student</span>
            <select
              value={auditStudentId ?? ""}
              onChange={(e) => {
                const next = e.target.value ? Number(e.target.value) : null;
                setAuditStudentId(next);
                refreshAudit(next);
              }}
            >
              <option value="">All students</option>
              {students.map((student) => (
                <option key={student.id} value={student.id}>
                  {student.student_number}
                </option>
              ))}
            </select>
          </label>
        </div>
        <p className="muted small-print">The most recent 100 entries. Times are shown in local time.</p>
        <table className="queue">
          <thead>
            <tr>
              <th>When</th>
              <th>User</th>
              <th>Action</th>
              <th>Resource</th>
              <th>Record</th>
              <th>Student</th>
            </tr>
          </thead>
          <tbody>
            {auditEntries.map((entry) => (
              <tr key={entry.id}>
                <td>{new Date(entry.created_at).toLocaleString()}</td>
                <td>{entry.user_id}</td>
                <td>{entry.action}</td>
                <td>{entry.resource.replace(/_/g, " ")}</td>
                <td>{entry.resource_id ?? "-"}</td>
                <td>{entry.student_id ?? "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="muted small-print">Signed in as {user?.username}.</p>
    </Layout>
  );
}

interface SectionProps {
  token: string;
  onDone: (text: string) => Promise<void>;
  onError: (text: string) => void;
}

function errorText(err: unknown): string {
  return err instanceof ApiError ? err.message : "Something went wrong. Please try again.";
}

function CreateStudentForm({ token, onDone, onError }: SectionProps) {
  const [number, setNumber] = useState("");
  const [name, setName] = useState("");
  const [programme, setProgramme] = useState("");

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    try {
      const created = await createStudent(token, {
        student_number: number.trim(),
        full_name: name.trim(),
        programme: programme.trim(),
      });
      setNumber("");
      setName("");
      setProgramme("");
      await onDone(`Created student ${created.student_number}.`);
    } catch (err) {
      onError(errorText(err));
    }
  }

  return (
    <form className="card stack" onSubmit={handleSubmit}>
      <h3>Add a student</h3>
      <label className="field"><span>Student number</span><input value={number} onChange={(e) => setNumber(e.target.value)} required maxLength={20} /></label>
      <label className="field"><span>Full name</span><input value={name} onChange={(e) => setName(e.target.value)} required maxLength={120} /></label>
      <label className="field"><span>Programme</span><input value={programme} onChange={(e) => setProgramme(e.target.value)} required maxLength={120} /></label>
      <button className="button primary small" type="submit">Create student</button>
    </form>
  );
}

function CreateCourseForm({ token, onDone, onError }: SectionProps) {
  const [code, setCode] = useState("");
  const [title, setTitle] = useState("");

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    try {
      const created = await createCourse(token, { code: code.trim(), title: title.trim() });
      setCode("");
      setTitle("");
      await onDone(`Created course ${created.code}.`);
    } catch (err) {
      onError(errorText(err));
    }
  }

  return (
    <form className="card stack" onSubmit={handleSubmit}>
      <h3>Add a course</h3>
      <label className="field"><span>Course code</span><input value={code} onChange={(e) => setCode(e.target.value)} required maxLength={20} /></label>
      <label className="field"><span>Title</span><input value={title} onChange={(e) => setTitle(e.target.value)} required maxLength={200} /></label>
      <button className="button primary small" type="submit">Create course</button>
    </form>
  );
}

function CorrectStudentForm({ token, students, onDone, onError }: SectionProps & { students: Student[] }) {
  const [studentId, setStudentId] = useState<number | "">("");
  const [name, setName] = useState("");
  const [programme, setProgramme] = useState("");

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (studentId === "") return;
    const body: { full_name?: string; programme?: string } = {};
    if (name.trim()) body.full_name = name.trim();
    if (programme.trim()) body.programme = programme.trim();
    if (Object.keys(body).length === 0) {
      onError("Enter a new name or programme to correct.");
      return;
    }
    try {
      await updateStudent(token, studentId, body);
      setName("");
      setProgramme("");
      await onDone("Student record corrected. The student number cannot be changed.");
    } catch (err) {
      onError(errorText(err));
    }
  }

  return (
    <form className="card stack" onSubmit={handleSubmit}>
      <h3>Correct a student</h3>
      <label className="field">
        <span>Student</span>
        <select value={studentId} onChange={(e) => setStudentId(e.target.value ? Number(e.target.value) : "")} required>
          <option value="">Choose a student</option>
          {students.map((s) => (
            <option key={s.id} value={s.id}>{s.student_number} {s.full_name}</option>
          ))}
        </select>
      </label>
      <label className="field"><span>New full name (optional)</span><input value={name} onChange={(e) => setName(e.target.value)} maxLength={120} /></label>
      <label className="field"><span>New programme (optional)</span><input value={programme} onChange={(e) => setProgramme(e.target.value)} maxLength={120} /></label>
      <button className="button secondary small" type="submit">Save correction</button>
    </form>
  );
}

function CorrectCourseForm({ token, courses, onDone, onError }: SectionProps & { courses: Course[] }) {
  const [courseId, setCourseId] = useState<number | "">("");
  const [title, setTitle] = useState("");

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (courseId === "" || !title.trim()) {
      onError("Choose a course and enter the corrected title.");
      return;
    }
    try {
      await updateCourse(token, courseId, { title: title.trim() });
      setTitle("");
      await onDone("Course title corrected. The course code cannot be changed.");
    } catch (err) {
      onError(errorText(err));
    }
  }

  return (
    <form className="card stack" onSubmit={handleSubmit}>
      <h3>Correct a course title</h3>
      <label className="field">
        <span>Course</span>
        <select value={courseId} onChange={(e) => setCourseId(e.target.value ? Number(e.target.value) : "")} required>
          <option value="">Choose a course</option>
          {courses.map((c) => (
            <option key={c.id} value={c.id}>{c.code} {c.title}</option>
          ))}
        </select>
      </label>
      <label className="field"><span>New title</span><input value={title} onChange={(e) => setTitle(e.target.value)} required maxLength={200} /></label>
      <button className="button secondary small" type="submit">Save correction</button>
    </form>
  );
}

function EnrolForm({
  token,
  students,
  courses,
  onDone,
  onError,
}: SectionProps & { students: Student[]; courses: Course[] }) {
  const [studentId, setStudentId] = useState<number | "">("");
  const [courseId, setCourseId] = useState<number | "">("");
  const [term, setTerm] = useState(DEFAULT_TERM);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (studentId === "" || courseId === "") {
      onError("Choose a student and a course.");
      return;
    }
    try {
      await enrolStudent(token, studentId, courseId, term.trim());
      await onDone("Student enrolled.");
    } catch (err) {
      onError(errorText(err));
    }
  }

  return (
    <form className="card section stack" onSubmit={handleSubmit}>
      <h3>Enrol a student in a course</h3>
      <div className="toolbar-actions">
        <label className="field inline">
          <span>Student</span>
          <select value={studentId} onChange={(e) => setStudentId(e.target.value ? Number(e.target.value) : "")} required>
            <option value="">Choose a student</option>
            {students.map((s) => (
              <option key={s.id} value={s.id}>{s.student_number} {s.full_name}</option>
            ))}
          </select>
        </label>
        <label className="field inline">
          <span>Course</span>
          <select value={courseId} onChange={(e) => setCourseId(e.target.value ? Number(e.target.value) : "")} required>
            <option value="">Choose a course</option>
            {courses.map((c) => (
              <option key={c.id} value={c.id}>{c.code} {c.title}</option>
            ))}
          </select>
        </label>
        <label className="field inline">
          <span>Term</span>
          <input value={term} onChange={(e) => setTerm(e.target.value)} placeholder="2026-S1" required />
        </label>
      </div>
      <button className="button primary small" type="submit">Enrol</button>
    </form>
  );
}