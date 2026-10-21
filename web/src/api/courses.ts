import { apiRequest } from "./client";

export interface Course {
  id: number;
  code: string;
  title: string;
}

export interface RosterStudent {
  id: number;
  student_number: string;
  full_name: string;
  programme: string;
}

export function listMyCourses(token: string): Promise<Course[]> {
  return apiRequest<Course[]>("/me/courses", { token });
}

export function listRoster(token: string, courseId: number, term: string): Promise<RosterStudent[]> {
  return apiRequest<RosterStudent[]>(
    `/courses/${courseId}/students?academic_term=${encodeURIComponent(term)}`,
    { token },
  );
}

export function listAllCourses(token: string): Promise<Course[]> {
  return apiRequest<Course[]>("/courses?limit=100", { token });
}