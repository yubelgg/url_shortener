# Failure Modes Documentation

## Overview
This document describes known failure scenarios for the URL Shortener service and how the system handles each one.

## Failure Modes

### 1. Database Connection Failure
- **Trigger:** PostgreSQL is down or unreachable
- **Symptom:** `/health` returns `{"status": "degraded"}` with database error details
- **Impact:** All endpoints return 503 Service Unavailable
- **Recovery:** Restart PostgreSQL. The app reconnects automatically on the next request via `before_request` hook.

### 2. Invalid User Input (400)
- **Trigger:** Missing required fields, wrong data types, or empty JSON body
- **Examples:**
  - `POST /users` with no `username` or `email`
  - `POST /urls` with no `original_url`
  - `POST /users` with `username` as a number instead of string
- **Response:** `{"error": "descriptive message"}` with 400 status
- **Impact:** Request rejected. No data written to database.

### 3. Resource Not Found (404)
- **Trigger:** Requesting a user, URL, or event that doesn't exist
- **Examples:**
  - `GET /users/999999`
  - `GET /urls/999999`
  - `PUT /users/999999`
- **Response:** `{"error": "User not found"}` or `{"error": "URL not found"}` with 404 status
- **Impact:** None. Database unchanged.

### 4. Duplicate Data (400)
- **Trigger:** Creating a user with a username or email that already exists
- **Response:** `{"error": "Username or email already exists"}` with 400 status
- **Impact:** Request rejected. Database integrity maintained via unique constraints.

### 5. Short Code Collision (500)
- **Trigger:** `generate_short_code()` produces a duplicate code 10 times in a row
- **Likelihood:** Extremely low (62^6 = ~56 billion possible codes)
- **Response:** `{"error": "Could not generate unique short_code"}` with 500 status
- **Impact:** URL not created. User can retry.

### 6. Unhandled Exception (500)
- **Trigger:** Any unexpected error not caught by route handlers
- **Response:** `{"error": "An unexpected error occurred", "type": "ExceptionClassName"}` with 500 status
- **Impact:** Error is logged via traceback. User gets clean JSON instead of a stack trace.

### 7. Application Process Crash
- **Trigger:** Out of memory, segfault, or manual kill
- **Recovery:** Docker restart policy (`restart: always`) automatically restarts the container.
- **Downtime:** Typically 2-5 seconds during restart.

### 8. Database Connection Leak
- **Trigger:** Request handler fails mid-execution
- **Prevention:** Flask's `teardown_appcontext` hook closes the database connection after every request, even on failure.

## Error Handling Architecture
All errors return consistent JSON responses. The `app/errors.py` module defines custom exception classes (`ValidationError`, `NotFoundError`, `InternalError`, `ServiceUnavailableError`) registered as global Flask error handlers. This ensures users never see raw stack traces or HTML error pages.

## Health Check
`GET /health` performs a database connectivity check. Returns `{"status": "ok"}` when healthy or `{"status": "degraded"}` with diagnostic details when issues are detected.