export type Role = "advisor" | "lecturer" | "administrator";

export interface User {
  id: number;
  username: string;
  role: Role;
}

export interface TokenResponse {
  access_token: string;
  token_type: "bearer";
  expires_in: number;
}