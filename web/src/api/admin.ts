import { apiRequest } from "./client";
import type { Course } from "./courses";
import type { Student } from "./flags";

export interface AuditEntry {
  id: number;
  user_id: number;
  action: string;
  resource: string;
  resource_id: number | null;
  student_id: number | null;
  created_at: string;
}

export function createStudent(
  token: string,
  body: { student_number: string; full_name: string; programme: string },
): Promise<Student> {
  return apiRequest<Student>("/students", { method: "POST", body, token });
}

export function updateStudent(
  token: string,
  studentId: number,
  body: { full_name?: string; programme?: string },
): Promise<Student> {
  return apiRequest<Student>(`/students/${studentId}`, { method: "PATCH", body, token });
}

export function createCourse(
  token: string,
  body: { code: string; title: string },
): Promise<Course> {
  return apiRequest<Course>("/courses", { method: "POST", body, token });
}

export function updateCourse(token: string, courseId: number, body: { title: string }): Promise<Course> {
  return apiRequest<Course>(`/courses/${courseId}`, { method: "PATCH", body, token });
}

export function enrolStudent(
  token: string,
  studentId: number,
  courseId: number,
  academicTerm: string,
): Promise<unknown> {
  return apiRequest(`/students/${studentId}/enrolments`, {
    method: "POST",
    body: { course_id: courseId, academic_term: academicTerm },
    token,
  });
}

export function listAuditLog(token: string, studentId: number | null): Promise<AuditEntry[]> {
  const query = studentId === null ? "limit=100" : `limit=100&student_id=${studentId}`;
  return apiRequest<AuditEntry[]>(`/audit-logs?${query}`, { token });
}