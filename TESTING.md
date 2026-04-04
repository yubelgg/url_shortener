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
