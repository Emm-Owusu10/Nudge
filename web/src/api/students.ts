import { apiRequest } from "./client";
import type { FlagFactor, QueueItem } from "./flags";

export interface StudentDetail {
  id: number;
  student_number: string;
  full_name: string;
  programme: string;
}

export interface WindowRate {
  rate: number | null;
  sessions_counted: number;
}

export interface Indicators {
  student_id: number;
  as_of: string;
  attendance_recent: WindowRate;
  attendance_earlier: WindowRate;
  missing_assignments: { missing: number; considered: number };
  grades: { recent_average: number | null; earlier_average: number | null };
}

export interface StudentFlag {
  id: number;
  student_id: number;
  as_of: string;
  level: QueueItem["level"];
  status: "open" | "dismissed";
  factors: FlagFactor[];
  created_at: string;
  dismissal_reason: string | null;
  dismissed_at: string | null;
}

export function getStudent(token: string, studentId: number): Promise<StudentDetail> {
  return apiRequest<StudentDetail>(`/students/${studentId}`, { token });
}

export function getIndicators(token: string, studentId: number, asOf: string): Promise<Indicators> {
  return apiRequest<Indicators>(`/students/${studentId}/indicators?as_of=${asOf}`, { token });
}

export function listStudentFlags(token: string, studentId: number): Promise<StudentFlag[]> {
  return apiRequest<StudentFlag[]>(`/students/${studentId}/flags`, { token });
}