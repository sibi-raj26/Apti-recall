# AptiRecall — Deployment Guide

This document covers production deployment requirements for the AptiRecall backend and frontend. It focuses on operational readiness: database backup/restore, static/media handling, and a pre-deployment checklist.

---

## 1. Environment Configuration

Production deployment must supply required environment variables. See `.env.example` for the full list.

Critical variables:

- `DJANGO_SETTINGS_MODULE=backend.settings.production`
- `DJANGO_SECRET_KEY` — strong random secret; never reuse the development placeholder
- `ALLOWED_HOSTS` — comma-separated production hostnames
- `CORS_ALLOWED_ORIGINS` — comma-separated allowed frontend origins
- `CSRF_TRUSTED_ORIGINS` — comma-separated trusted origins for CSRF
- `DATABASE_URL` — PostgreSQL connection string
- `CELERY_BROKER_URL` — Redis broker URL
- `CELERY_RESULT_BACKEND` — Redis result backend URL
- `SECURE_SSL_REDIRECT` — set to `True` in production unless TLS is terminated elsewhere

Do not commit real secrets to version control.

---

## 2. Static Files

Production uses Django's static file collection flow:

```text
Django
  ↓
python manage.py collectstatic --noinput
  ↓
staticfiles/
  ↓
ManifestStaticFilesStorage
```

The Docker web entrypoint already runs `collectstatic` during container startup. Verify that the deployed environment serves the collected static files correctly through its web server or object-storage configuration.

---

## 3. Media Files

The current container setup uses a persistent Docker volume mounted at `/app/media`. This is suitable for local/prototype containerized operation.

For actual production deployment:

- Local container storage may not survive container replacement/redeployment on many hosting platforms.
- Production should use one of the following:
  - Platform-managed persistent file storage
  - S3-compatible object storage
  - Another durable managed file-storage service

Do not treat local Docker media storage as a production-grade backup or persistence solution.

---

## 4. Database — PostgreSQL

Production uses PostgreSQL. The application expects `DATABASE_URL` to point to a reachable PostgreSQL instance.

Migrations must be applied as part of deployment:

```bash
python manage.py migrate --noinput
```

The Docker web entrypoint runs migrations automatically at startup.

---

## 5. PostgreSQL Backup

Production deployment must configure scheduled PostgreSQL backups through the hosting provider or an approved PostgreSQL backup mechanism.

### Example backup command

```bash
pg_dump "$DATABASE_URL" > backup.sql
```

This is a generic example and must be adapted to the production environment.

### Backup frequency

Perform at least daily backups. Use more frequent backups if the recovery point objective requires a shorter interval.

### Retention

A reasonable baseline retention policy:

- daily backups retained for at least 7 days
- weekly backups retained for at least 4 weeks

Adjust retention to match institutional or business requirements.

### Verification

Backups should be periodically verified. The existence of a backup file does not prove that recovery will succeed.

---

## 6. PostgreSQL Restore

Restore operations must be tested against a separate or staging database before any production recovery action.

### Example restore command

```bash
psql "$DATABASE_URL" < backup.sql
```

### Production restore warnings

- Never blindly execute restore commands against production.
- Always test restore procedures in a non-production environment first.
- Production restore should follow an intentional recovery procedure.
- Depending on the restore method, existing production data may be overwritten.

---

## 7. Recovery Testing

Periodically verify the full recovery path:

1. Confirm the backup can be downloaded or accessed.
2. Confirm the backup is not corrupted.
3. Restore the backup to a separate PostgreSQL database.
4. Verify application migrations are compatible.
5. Verify important application data is present after restoration.
6. Verify the application can connect successfully after restoration.

Document each recovery test and its result.

---

## 8. Deployment Checklist

### Database

- [ ] PostgreSQL is configured and reachable
- [ ] `DATABASE_URL` is set correctly
- [ ] Migrations have been applied (`python manage.py migrate --noinput`)
- [ ] Scheduled backups are configured
- [ ] Backup restoration has been tested

### Static Files

- [ ] `python manage.py collectstatic --noinput` has completed successfully
- [ ] Static files are served correctly in production

### Media

- [ ] Durable media storage is configured
- [ ] Media persistence has been verified across container or instance replacement where applicable

### Security

- [ ] `DJANGO_SECRET_KEY` is set to a strong random value
- [ ] `ALLOWED_HOSTS` contains only production hostnames
- [ ] `CORS_ALLOWED_ORIGINS` contains only production frontend origins
- [ ] `CSRF_TRUSTED_ORIGINS` is set appropriately
- [ ] TLS/HTTPS is configured if `SECURE_SSL_REDIRECT=True`
- [ ] Health endpoint (`/api/health/`) is accessible as expected

### Application

- [ ] Web service starts and passes health check
- [ ] Celery worker connects to Redis and loads Django
- [ ] `/api/health/` returns HTTP 200 with the expected JSON response

---

## 9. Continuous Integration

CI validation is configured, but automatic production deployment is intentionally not enabled in Phase 15.5.

### CI runs on

- Push to `main`
- Pull requests targeting `main`

### Backend validation

CI splits backend tests into two explicit steps:

1. **Regression gate** — runs the maintained backend test suite excluding 12 known stale tests in `tests/test_api.py`. This step must pass completely. It is the strict CI gate for backend changes.
2. **Legacy validation** — runs only the 12 known stale tests in `tests/test_api.py` with `continue-on-error: true`. These tests are expected to fail because they expect unauthenticated access to endpoints that now require authentication. This step is informational and documents the known legacy debt without blocking the pipeline.

### Why legacy tests are separated

The 12 stale tests are in `tests/test_api.py::TestTopicAPI` and `tests/test_api.py::TestQuestionAPI`. They expect HTTP 200 for unauthenticated requests, but the current API contract requires authentication for topic and question endpoints. Rather than weakening authentication or deleting historical tests, CI treats them as separate legacy validation. The current API behavior remains protected.

### Frontend validation

- TypeScript type check
- Frontend test suite
- Production build

### Docker validation

- `docker compose config`
- Docker image build for web and Celery services

## 10. Future Work

- Configure scheduled PostgreSQL backups through the hosting provider.
- Configure durable production media storage (platform-managed storage or S3-compatible object storage).
- Enable automatic production deployment when the project is ready for that stage.

---

## 11. Production Deployment on Render

This section documents the first controlled production deployment of AptiRecall using Render. This deployment uses the existing Docker architecture without redesigning the application.

### Chosen platform

Render was chosen because it supports:

- Docker-based web services
- Managed PostgreSQL
- Managed Redis
- Background worker services
- Environment variable configuration
- HTTPS termination

### Required services

Deploy the following services on Render:

1. **Web service** — Django + Gunicorn backend API
2. **Worker service** — Celery worker
3. **PostgreSQL** — managed database instance
4. **Redis** — managed Redis instance

### Environment variables

Configure the following environment variables on Render. Never commit real secrets.

#### Web service

```text
DJANGO_SETTINGS_MODULE=backend.settings.production
DJANGO_SECRET_KEY=<strong-random-secret>
DEBUG=False
ALLOWED_HOSTS=<production-web-service-url>
CORS_ALLOWED_ORIGINS=<production-frontend-origin>
CSRF_TRUSTED_ORIGINS=<production-frontend-origin>
DATABASE_URL=<render-postgresql-url>
CELERY_BROKER_URL=<render-redis-url>
CELERY_RESULT_BACKEND=<render-redis-url>
SECURE_SSL_REDIRECT=True
```

#### Worker service

```text
DJANGO_SETTINGS_MODULE=backend.settings.production
DJANGO_SECRET_KEY=<same-as-web-service>
DEBUG=False
ALLOWED_HOSTS=<production-web-service-url>
DATABASE_URL=<render-postgresql-url>
CELERY_BROKER_URL=<render-redis-url>
CELERY_RESULT_BACKEND=<render-redis-url>
```

### Frontend deployment

The React/Vite frontend must be built and deployed separately. Options:

1. **Static hosting** — deploy the `frontend/dist` output to a static hosting service such as Netlify, Vercel, or Render Static Sites.
   - Set `VITE_API_URL=https://<backend-domain>/api` during the production build.
   - Ensure the backend `CORS_ALLOWED_ORIGINS` includes the deployed frontend origin.

2. **Served from Django** — alternatively, build the frontend and serve it through Django by placing the built assets in `staticfiles/`. This requires frontend build integration into the Docker image or deployment pipeline.

### Migration and static collection

The Docker web entrypoint automatically runs:

```bash
python manage.py migrate --noinput
python manage.py collectstatic --noinput
```

Verify migrations after first deploy:

```bash
python manage.py showmigrations
```

### Health check

After deployment, verify:

```bash
curl https://<backend-domain>/api/health/
```

Expected response:

```json
{"status":"ok","service":"AptiRecall API"}
```

### Smoke test

Perform a minimal smoke test after deployment:

1. Backend health endpoint returns HTTP 200.
2. Gunicorn is running.
3. Celery worker is connected to Redis and loads Django.
4. Frontend loads successfully.
5. User registration works.
6. User login works and returns JWT tokens.
7. Authenticated API call succeeds.
8. Logout succeeds.

### Security verification

After deployment, verify:

- `DEBUG=False`
- No secrets are exposed in logs
- HTTPS is active
- Secure cookies are enabled
- HSTS is active where applicable
- `ALLOWED_HOSTS` is restricted to production hostnames
- `CORS_ALLOWED_ORIGINS` is restricted to the production frontend origin
- `CSRF_TRUSTED_ORIGINS` is set correctly
- DRF throttling is active
- JWT refresh rotation is active

### Rollback

To roll back to a previous deployment version:

1. In the Render dashboard, locate the web service and worker service.
2. Select the previous successful deploy and promote it to the current version.
3. Inspect deployment logs to identify the failure cause.
4. Verify health endpoint after rollback:

   ```bash
   curl https://<backend-domain>/api/health/
   ```

5. Verify Celery worker is running and connected to Redis.

Database rollback limitations:

- Render does not automatically revert database migrations during rollback.
- If a migration causes issues, restore from a recent database backup using:

  ```bash
  psql "<DATABASE_URL>" < backup.sql
  ```

- Always test database restore procedures against a staging instance before applying to production.

### Render Blueprint

A Render Blueprint (`render.yaml`) is provided for reproducible infrastructure setup. Do not commit real secrets. Use Render environment variable references for all sensitive values.

