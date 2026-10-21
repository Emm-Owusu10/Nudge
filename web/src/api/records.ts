import { apiRequest } from "./client";

export type AttendanceStatus = "present" | "absent" | "late" | "excused";

export function recordAttendance(
  token: string,
  studentId: number,
  courseId: number,
  sessionDate: string,
  status: AttendanceStatus,
): Promise<unknown> {
  return apiRequest(`/students/${studentId}/attendance`, {
    method: "POST",
    body: { course_id: courseId, session_date: sessionDate, status },
    token,
  });
}

export function recordAssessment(
  token: string,
  studentId: number,
  courseId: number,
  title: string,
  assessedOn: string,
  score: number,
): Promise<unknown> {
  return apiRequest(`/students/${studentId}/assessments`, {
    method: "POST",
    body: { course_id: courseId, title, assessed_on: assessedOn, score },
    token,
  });
}