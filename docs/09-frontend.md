# Frontend

The web interface is a React application written in TypeScript and built with Vite. It replaces the earlier Streamlit prototype, which has been removed. The interface holds no business rules. Every action is a call to the API, which checks the role and the lecturer's course scope on each request.

## Running the system

Two processes run together. Start them in separate PowerShell windows, with `.venv` active in the first.

**1. The API**, from the `backend` folder:

```powershell
uvicorn app.main:app --reload
```

It listens on `http://127.0.0.1:8000`. Interactive API documentation is at `http://127.0.0.1:8000/docs`.

**2. The web interface**, from the `web` folder:

```powershell
npm run dev -- --port 5173 --strictPort
```

Open `http://localhost:5173`. The port matters. The API accepts browser requests only from port 5173, so Vite must not switch to another port. If you see a CORS error in the browser console, check the port first.

Node.js 20 or later is required. This project was built with Node 22.14.

## Signing in

Every role signs in on the same page. After a successful sign-in, the interface sends the user to the dashboard for their role:

| Role | Lands on | Account created by |
|---|---|---|
| Advisor | `/advisor` | `python manage.py create-user --role advisor` |
| Lecturer | `/lecturer` | `python manage.py create-user --role lecturer`, then `assign-course` |
| Administrator | `/admin` | `python manage.py create-user --role administrator` |

Passwords are never entered on the command line. Accounts are created with `manage.py`, which hides the password as it is typed.

A user who opens a page for a different role is redirected to their own dashboard. This only changes what is shown. The API rejects any request the role is not allowed to make, so the redirect cannot be used to bypass the rules.

The session token is stored in `sessionStorage`. It persists across page refreshes in the same tab and is cleared when the tab closes or the user signs out. Tokens expire after 60 minutes, after which the user must sign in again.

## Dashboards

### Advisor

- **Find a student.** A search box filters the student list by number or name. Each match links to the student's detail page, including students with no flags.
- **Flag queue.** Shows open flags for an evaluation date, most urgent first. The date defaults to the demonstration date, 2026-10-19.
  - **Evaluate all students** runs the flag rules for every student on the chosen date. It sends one request per student, so the button shows progress.
  - **Dismiss** requires a reason. The flag leaves the open queue but remains in the database.
  - **Open / Dismissed** toggle. The dismissed view is read-only and shows each dismissal reason and date.
- **Student detail.** Four sections:
  - Indicators: attendance over the last and previous four weeks, missing assignments, and grade averages.
  - Flag history: every flag raised for the student, with its reasons.
  - Interventions: each intervention with its follow-up comparison. Attendance is shown at the intervention date and at the follow-up date. A note appears when the follow-up date has not arrived.
  - Outcome: advisors record `improving`, `no_change` or `referred_elsewhere`.
- **Record an intervention.** Choose a type, a date, optional notes, and optionally a linked open flag.

### Lecturer

- **My courses.** Lists only the courses the lecturer is linked to. Other courses are not shown, and the API would reject them anyway.
- **Roster.** Lists the students enrolled in the selected course for an academic term. The term defaults to `2026-S1` and can be changed.
- **Attendance.** Choose a session date and a status for each student, then save. Each student is saved separately. The summary reports how many saved, how many were already recorded for that date, and how many failed.
- **Assessments.** Enter one title and date for the batch, then a score for each student. Blank rows are skipped. Scores outside 0 to 100 are rejected before any request is sent.

### Administrator

- **Add a student** and **add a course**.
- **Correct a student** (name or programme) and **correct a course** (title). Student numbers and course codes cannot be changed, matching the API.
- **Enrol a student** in a course for a term.
- **Audit log.** The 100 most recent entries, optionally filtered by student. Each entry shows who acted, what they did, and to which record.

## Project structure

```
web/
  index.html
  src/
    main.tsx              Entry point; wraps the app in the router and the auth provider
    App.tsx               Routes, and the role check on each route
    index.css             Shared styles
    types.ts              Shared types (roles, the signed-in user, tokens)
    api/
      client.ts           One fetch wrapper. Adds the token, turns errors into ApiError
      flags.ts            Flag queue, evaluation, dismissal, and the student list
      students.ts         Student detail, indicators, flags for one student
      interventions.ts    Interventions, outcomes, follow-up comparison
      courses.ts          Lecturer courses, roster, and the full course list
      records.ts          Attendance and assessment entry
      admin.ts            Creating and correcting students and courses, enrolments, audit log
    auth/
      AuthContext.tsx     Sign-in state, session restore, sign-out
      roles.ts            Maps each role to its home page
    components/
      Layout.tsx          Header with the user name and sign-out button
      StudentSearch.tsx   Search panel used on the advisor dashboard
    pages/
      SignIn.tsx
      AdvisorDashboard.tsx
      StudentDetail.tsx
      LecturerDashboard.tsx
      AdminDashboard.tsx
```

### Where each responsibility lives

- **Rules and permissions:** the API, in `backend/app/`. The interface never repeats them.
- **HTTP and errors:** `api/client.ts` is the only file that calls `fetch`. Each page calls the helpers in `api/`, and the helpers call the client.
- **Who can see what:** `App.tsx` decides which pages a signed-in user may open. The API decides which records they may read or change.

## Build and checks

From the `web` folder:

```powershell
npm run build
```

This type-checks the code and produces a production bundle. It must finish without errors before the interface is demonstrated.

## Known limitations of the interface

- Lists are loaded in one request of up to 100 items. A larger school would need server-side search and paging.
- The flag queue evaluates students one request at a time. Evaluating a large cohort would be slow and would need a batch endpoint.
- The dismissed view is read-only. A dismissal cannot be undone from the interface.
- Dates are shown in the browser's local format. They are compared and stored as calendar dates, not as times.
- The interface is designed for a desktop browser. It has not been tested on phones.
- The development server is for local use. Production deployment would need a build served over HTTPS, and the CORS origin list would need updating.