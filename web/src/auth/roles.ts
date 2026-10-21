import type { Role } from "../types";

// Each role has one home page.
export function homePathFor(role: Role): string {
  switch (role) {
    case "advisor":
      return "/advisor";
    case "lecturer":
      return "/lecturer";
    case "administrator":
      return "/admin";
  }
}