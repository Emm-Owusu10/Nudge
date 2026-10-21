import { apiRequest } from "./client";

export type InterventionType =
  | "meeting"
  | "study_plan"
  | "tutoring_referral"
  | "wellbeing_referral"
  | "other";

export type Outcome = "not_yet_reviewed" | "improving" | "no_change" | "referred_elsewhere";

export interface Intervention {
  id: number;
  student_id: number;
  flag_id: number | null;
  intervention_type: InterventionType;
  intervention_date: string;
  follow_up_due: string;
  notes: string | null;
  outcome: Outcome;
  outcome_recorded_at: string | null;
  created_at: string;
}

export interface NewIntervention {
  intervention_type: InterventionType;
  intervention_date: string;
  notes: string | null;
  flag_id: number | null;
}

export interface FollowUp {
  intervention_id: number;
  student_id: number;
  intervention_date: string;
  follow_up_due: string;
  is_due: boolean;
  outcome: Outcome;
  before: { attendance_recent: { rate: number | null; sessions_counted: number } };
  after: { attendance_recent: { rate: number | null; sessions_counted: number } };
}

export function listInterventions(token: string, studentId: number): Promise<Intervention[]> {
  return apiRequest<Intervention[]>(`/students/${studentId}/interventions`, { token });
}

export function createIntervention(
  token: string,
  studentId: number,
  body: NewIntervention,
): Promise<Intervention> {
  return apiRequest<Intervention>(`/students/${studentId}/interventions`, {
    method: "POST",
    body,
    token,
  });
}

export function recordOutcome(
  token: string,
  interventionId: number,
  outcome: Outcome,
): Promise<Intervention> {
  return apiRequest<Intervention>(`/interventions/${interventionId}/outcome`, {
    method: "POST",
    body: { outcome },
    token,
  });
}

export function getFollowUp(token: string, interventionId: number): Promise<FollowUp> {
  return apiRequest<FollowUp>(`/interventions/${interventionId}/follow-up`, { token });
}