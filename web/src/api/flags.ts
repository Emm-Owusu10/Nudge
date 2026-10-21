import { apiRequest } from "./client";

export interface FlagFactor {
  code: string;
  message: string;
}

export interface QueueItem {
  flag_id: number;
  student_id: number;
  student_number: string;
  full_name: string;
  level: "priority review" | "review recommended" | "monitor";
  status: "open" | "dismissed";
  as_of: string;
  factors: FlagFactor[];
  created_at: string;
}

export interface Student {
  id: number;
  student_number: string;
  full_name: string;
  programme: string;
}

export function listStudents(token: string): Promise<Student[]> {
  return apiRequest<Student[]>("/students?limit=100", { token });
}

export function listOpenFlags(
  token: string,
  asOf: string,
  status: "open" | "dismissed" = "open",
): Promise<QueueItem[]> {
  return apiRequest<QueueItem[]>(`/flags?as_of=${asOf}&status=${status}`, { token });
}

export function evaluateStudent(token: string, studentId: number, asOf: string): Promise<unknown> {
  return apiRequest(`/students/${studentId}/flags/evaluate?as_of=${asOf}`, {
    method: "POST",
    token,
  });
}

export function dismissFlag(token: string, flagId: number, reason: string): Promise<unknown> {
  return apiRequest(`/flags/${flagId}/dismiss`, {
    method: "POST",
    body: { reason },
    token,
  });
}

export interface DismissedDetail {
  flag_id: number;
  dismissal_reason: string | null;
  dismissed_at: string | null;
}

export async function listDismissedDetails(
  token: string,
  studentIds: number[],
  asOf: string,
): Promise<Record<number, DismissedDetail>> {
  const details: Record<number, DismissedDetail> = {};
  for (const studentId of studentIds) {
    const flags = await apiRequest<
      { id: number; as_of: string; status: string; dismissal_reason: string | null; dismissed_at: string | null }[]
    >(`/students/${studentId}/flags`, { token });
    for (const flag of flags) {
      if (flag.as_of === asOf && flag.status === "dismissed") {
        details[flag.id] = {
          flag_id: flag.id,
          dismissal_reason: flag.dismissal_reason,
          dismissed_at: flag.dismissed_at,
        };
      }
    }
  }
  return details;
}