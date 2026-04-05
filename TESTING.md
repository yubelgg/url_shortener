# API Testing Guide

## Setup Commands

```bash
# Install dependencies
uv sync

# Start the server
uv run run.py

# Seed the database (run once)
uv run seed.py
```

---

## Health Check

```bash
curl -s http://localhost:5001/health
```

Expected: `{"status": "ok"}`

---

## Users

### List all users (paginated)

```bash
curl -s http://localhost:5001/users
```

With pagination:

```bash
curl -s "http://localhost:5001/users?page=1&per_page=5"
```

### Get user by ID

```bash
curl -s http://localhost:5001/users/1
```

### Create a user

```bash
curl -s -X POST http://localhost:5001/users \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "testuser@example.com"}'
```

### Update a user

```bash
curl -s -X PUT http://localhost:5001/users/1 \
  -H "Content-Type: application/json" \
  -d '{"username": "updated_username"}'
```

### Bulk import users from CSV

```bash
curl -s -X POST http://localhost:5001/users/bulk \
  -F file=@users.csv
```

---

## URLs

### List all URLs

```bash
curl -s http://localhost:5001/urls
```

Filter by user:

```bash
curl -s "http://localhost:5001/urls?user_id=1"
```

### Get URL by ID

```bash
curl -s http://localhost:5001/urls/1
```

### Create a URL

```bash
curl -s -X POST http://localhost:5001/urls \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "original_url": "https://example.com/test", "title": "Test URL"}'
```

### Update a URL

```bash
curl -s -X PUT http://localhost:5001/urls/1 \
  -H "Content-Type: application/json" \
  -d '{"title": "Updated Title", "is_active": false}'
```

---

## Events

### List all events

```bash
curl -s http://localhost:5001/events
```

---

## Error Cases

### Get non-existent user (404)

```bash
curl -s http://localhost:5001/users/99999
```

### Create user with invalid data (400)

```bash
curl -s -X POST http://localhost:5001/users \
  -H "Content-Type: application/json" \
  -d '{"username": 123, "email": "bad@test.com"}'
```

### Create URL with non-existent user (404)

```bash
curl -s -X POST http://localhost:5001/urls \
  -H "Content-Type: application/json" \
  -d '{"user_id": 99999, "original_url": "https://example.com", "title": "Test"}'
```

---

## Route Summary

| Method | Route             | Description                     |
|--------|-------------------|---------------------------------|
| GET    | /health           | Health check                    |
| GET    | /users            | List users (paginated)          |
| GET    | /users/:id        | Get user by ID                  |
| POST   | /users            | Create user                     |
| PUT    | /users/:id        | Update user                     |
| POST   | /users/bulk       | Bulk import users from CSV      |
| GET    | /urls             | List URLs (filterable by user)  |
| GET    | /urls/:id         | Get URL by ID                   |
| POST   | /urls             | Create URL (generates short_code) |
| PUT    | /urls/:id         | Update URL                      |
| GET    | /events           | List all events                 |

## Test Strategies Implemented
# API Testing Guide

## Test Methods by Module

### Error Handling Tests (`test_error_coverage.py`)

#### TestErrorHandlerRegistration
- `test_400_bad_request()` - Tests 400 handler with missing required fields
- `test_500_unhandled_exception()` - Tests that unhandled exceptions return 500 with JSON error
- `test_404_missing_route()` - Tests that missing routes return 404 with JSON response
- `test_invalid_json_causes_400()` - Tests malformed JSON triggers error handler

#### TestErrorClassHierarchy
- `test_validation_error_is_api_error()` - Validates ValidationError inherits from APIError
- `test_not_found_error_is_api_error()` - Validates NotFoundError inherits from APIError
- `test_internal_error_is_api_error()` - Validates InternalError inherits from APIError
- `test_service_unavailable_error_is_api_error()` - Validates ServiceUnavailableError inherits from APIError
- `test_error_to_dict_includes_error_key()` - Validates all errors include "error" key

#### TestHealthCheckDegradation
- `test_health_returns_status_field()` - Tests health response has status field
- `test_health_returns_checks_field()` - Tests health response has checks field
- `test_health_database_check_structure()` - Tests database check has proper structure

#### TestErrorResponseFormat
- `test_404_error_format()` - Tests 404 errors have consistent JSON format
- `test_validation_error_format()` - Tests validation errors have consistent format
- `test_multiple_errors_same_format()` - Tests different error types return same format

#### TestHealthCheckEndpointDirectly
- `test_health_always_returns_200()` - Tests /health always returns HTTP 200
- `test_health_never_returns_error_status_code()` - Tests /health never returns 4xx or 5xx

---

### Health Endpoint Tests (`test_health.py`)

- `test_health()` - Tests /health endpoint returns 200 with status "ok"

---

### User Tests (`test_users.py`)

- `test_create_user()` - Tests POST /users creates user successfully
- `test_create_user_missing_fields()` - Tests POST /users with empty body returns 400
- `test_create_user_invalid_types()` - Tests POST /users with invalid types returns 400
- `test_create_duplicate_user()` - Tests POST /users with duplicate username returns 400
- `test_list_users()` - Tests GET /users returns paginated user list
- `test_list_users_pagination()` - Tests GET /users with pagination parameters
- `test_get_user()` - Tests GET /users/:id returns specific user
- `test_get_user_not_found()` - Tests GET /users/:id with invalid ID returns 404
- `test_update_user()` - Tests PUT /users/:id updates user
- `test_update_user_not_found()` - Tests PUT /users/:id with invalid ID returns 404

---

### Event Tests (`test_events.py`)

- `test_list_events()` - Tests GET /events returns all events
- `test_event_created_on_url_creation()` - Tests event created when URL is shortened

---

## Running Tests

### Run All Tests
```bash
uv run pytest tests/ -v
```

### Run Tests with Coverage Report
```bash
uv run pytest tests/ -v --cov=app.errors --cov=app.health --cov-report=term-missing
```

### Run Specific Test File
```bash
uv run pytest tests/test_error_coverage.py -v
uv run pytest tests/test_users.py -v
```

### Run Specific Test Class
```bash
uv run pytest tests/test_error_coverage.py::TestErrorHandlerRegistration -v
```

### Run Specific Test
```bash
uv run pytest tests/test_users.py::test_create_user -v
```

---

### With Docker (Recommended)

```bash
# Run all tests
docker exec -it url_shortener-app-1 uv run pytest tests/ -v

# Run tests with coverage report
docker exec -it url_shortener-app-1 uv run pytest tests/ -v --cov=app.errors --cov=app.health --cov-report=term-missing

# Run specific test file
docker exec -it url_shortener-app-1 uv run pytest tests/test_error_coverage.py -v

# Run specific test class
docker exec -it url_shortener-app-1 uv run pytest tests/test_error_coverage.py::TestErrorHandlerRegistration -v

# Run specific test
docker exec -it url_shortener-app-1 uv run pytest tests/test_users.py::test_create_user -v