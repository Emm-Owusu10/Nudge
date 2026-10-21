import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listStudents, type Student } from "../api/flags";
import { ApiError } from "../api/client";

interface StudentSearchProps {
  token: string;
}

export default function StudentSearch({ token }: StudentSearchProps) {
  const [students, setStudents] = useState<Student[]>([]);
  const [query, setQuery] = useState("");
  const [error, setError] = useState<string | null>(null);

  // Load the student list once. Searching then filters it in the browser.
  useEffect(() => {
    listStudents(token)
      .then(setStudents)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Could not load students."));
  }, [token]);

  const term = query.trim().toLowerCase();
  const matches = term
    ? students.filter(
        (student) =>
          student.student_number.toLowerCase().includes(term) ||
          student.full_name.toLowerCase().includes(term),
      )
    : [];

  return (
    <div className="card section">
      <h3>Find a student</h3>
      <p className="muted small-print">
        Search by student number or name. Use this to open any student, including those without flags.
      </p>
      <input
        className="search-input"
        type="search"
        placeholder="For example DEMO-001 or Demo Student"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />

      {error && <p className="error">{error}</p>}

      {term && matches.length === 0 && !error && (
        <p className="muted">No students match “{query.trim()}”.</p>
      )}

      {matches.length > 0 && (
        <ul className="search-results">
          {matches.slice(0, 10).map((student) => (
            <li key={student.id}>
              <Link to={`/advisor/students/${student.id}`}>
                <strong>{student.student_number}</strong> {student.full_name}
              </Link>
              <span className="muted"> · {student.programme}</span>
            </li>
          ))}
        </ul>
      )}
      {matches.length > 10 && (
        <p className="muted small-print">Showing the first 10 of {matches.length} matches. Keep typing to narrow the results.</p>
      )}
    </div>
  );
}