# CLAUDE.md

Guidance for Claude Code (and humans) working in this repository.

## What this is

ClashCode is a gamified Python-learning platform: users solve level-based challenges in a Monaco editor, earn XP, buy cosmetics, chat in real time and get hints from an AI tutor.

| Path | What it is |
|---|---|
| `frontend/` | React 19 + Vite SPA (Zustand, TanStack Query, Tailwind 4) |
| `services/core/` | Django 5.2 + DRF monolith: auth, challenges, XP, store, payments (Razorpay), certificates, admin, Celery tasks |
| `services/chat/` | FastAPI WebSocket service: global chat (DynamoDB) + per-user notification/task push (Redis pub/sub) |
| `services/ai/` | FastAPI AI tutor (internal only): hints/analysis via Groq (OpenAI-compatible), RAG on Pinecone, LangGraph agent |
| `services/executor/` | FastAPI sandbox that runs untrusted learner code (internal only) |
| `services/analytics/` | Small FastAPI Prometheus proxy (internal only) |
| `infra/k8s/` | Kustomize `base` + `dev`/`prod` overlays, `jobs/` (migrations), `monitoring/`, `components/gvisor`, `external-secrets/` |
| `infra/terraform/` | `bootstrap/` (state bucket), `environments/{dev,prod}`, modules: VPC, EKS, ElastiCache, DynamoDB, ECR, IRSA |
| `challenges/content/*.md` (in core) | Level definitions (frontmatter + initial code + test code), loaded with `manage.py load_levels` |

Request flow:

- The browser reaches the ALB, which routes to core (`/api`) or chat (`/ws`, `/api/chat`).
- Code runs go core → Celery `default` queue → executor. Learner code and the level's `test_code` are sent separately; the executor's harness decides `passed`.
- Results come back to the browser through Redis pub/sub and chat's `/ws/tasks`.

## Commands

```bash
# Full local stack (needs services/.env, services/*/.env — copy the .env.example files)
cd services && docker compose up --build
cd services && docker compose -f docker-compose.yml -f docker-compose.dev.yml up   # hot reload

# Core (Django) tests — tests live inside each app (<app>/tests/), SQLite is used automatically
cd services/core && python manage.py test
cd services/core && TEST_DB=postgres python manage.py test          # against the configured Postgres
cd services/core && python manage.py makemigrations --check --dry-run

# FastAPI services (executor rlimit tests only run on Linux)
cd services/<ai|chat|executor> && pytest -q

# Lint / audit
ruff check services            # config in services/pyproject.toml
pip-audit -r services/<svc>/requirements.txt
cd frontend && npm run lint && npm run test:run && npm audit --audit-level=high && npm run build

# Manifests / Terraform
kubectl kustomize infra/k8s/overlays/prod
terraform -chdir=infra/terraform/environments/prod init -backend=false && terraform -chdir=infra/terraform/environments/prod validate

# Frontend dev server (proxies /api, /ws, /media to http://localhost)
cd frontend && npm run dev
```

## Conventions

- **Business logic lives in `services` modules** (`<app>/services.py` or `<app>/services/`), and views stay thin. Follow that pattern.
- **Service-to-service calls are signed.** Use `project.internal_auth.build_internal_headers(path)` (core) or `core.security.build_internal_headers(path)` (ai). Headers: `X-Internal-API-Key`, `X-Internal-Timestamp`, `X-Internal-Signature` = HMAC-SHA256 over `"<timestamp>:<path>"`.
- **The executor has its own credentials.** These are `EXECUTOR_API_KEY` / `EXECUTOR_SIGNING_SECRET`, and they fall back to `INTERNAL_*` in local dev. Use `build_executor_headers(path)`. Never give the executor any other secret.
- **Never decide "passed" from exit code or stderr.** Use `PistonExecutionService.run_challenge_tests()` and read its `passed`.
- **Check `ChallengeService.is_unlocked()`** before anything that runs, scores or hints a level.
- **XP changes go through `xpoint.services.XPService.add_xp`**, which locks the row and writes the ledger. Never write `profile.xp` directly.
- **Auth is JWT in HttpOnly cookies** (`access_token`, `refresh_token`). The frontend must not store tokens in `localStorage`, and WebSocket URLs never carry tokens. Revocations are mirrored to Redis (`authentication/revocation.py`) for chat.
- **Client IPs come from `project.client_ip.get_client_ip`** (respects `NUM_PROXIES`), never from raw `X-Forwarded-For`.
- **Dates use `timezone.localdate()`**, not `timezone.now().date()` (`TIME_ZONE` is Asia/Kolkata; `auto_now_add` dates are local).
- **Enqueue Celery tasks from signals with `transaction.on_commit`.**
- **Uploaded images go through `project.validators.validate_image_upload`.**
- **Python style:** ruff, line length 120. Tests use Django `APITestCase` / pytest.

## Production-readiness TODO

From the full audit on 2026-10-17; repo work completed 2026-10-18. Tick an item only when it is done **and verified**.
👤 = needs an action outside the repo (dashboard, cloud console, or a destructive git operation), so Claude can't do it alone.
A parent stays unticked while any of its 👤 steps is open.

### 🔴 Critical

- [ ] **C1 Leaked DB password** (`infra/k8s/overlays/dev/secrets.yaml` is public on GitHub)
  - [ ] 👤 Rotate the Supabase DB password
  - [x] Stop tracking the file (`git rm --cached`) and add a `secrets.example.yaml` for dev; scrub the real DB host/user from the `.env.example` files
  - [ ] 👤 Purge the file from git history and force-push (commands in the C1 notes below)
  - [x] Add gitleaks secret scanning to CI (working tree + PR commits)
- [ ] **C2 Executor leaks every secret**
  - [x] Remove the host runner and the broken Docker runner; one sandboxed runner with a clean env, rlimits, process-group kill and output caps
  - [x] Fix the AST pre-check (`__import__`, importlib, builtins, frame introspection). It's only an early warning, not a security boundary
  - [x] Core and AI send signed executor headers; the executor rejects every call (503) without a key unless `EXECUTOR_ALLOW_UNAUTHENTICATED=true`
  - [x] Executor gets its own `executor-secrets` (k8s) and an isolated network (compose)
  - [x] k8s hardening: no SA token, non-root, read-only rootfs, drop caps, deny-all egress NetworkPolicy, optional gVisor RuntimeClass
  - [ ] 👤 Install gVisor (`runsc`) on the EKS node group and enable `components/gvisor` in the prod overlay
- [x] **C3 Game integrity**
  - [x] Test harness with a per-run token, so `exit()` / `SystemExit` / `os._exit` can't pass a level
  - [x] Server-side unlock check on execute/submit/hints
  - [x] Row lock on `UserProgress` so concurrent submits can't double-award XP

### 🟠 High

- [x] **H1** Logout revokes the refresh token too (and works with an expired access token)
- [x] **H2** OAuth links accounts only on a *verified* email (GitHub + Google); provider tokens are no longer stored
- [x] **H3** Set DRF `NUM_PROXIES` and use one client-IP helper (throttles + audit log)
- [x] **H4** AI endpoints get their own throttle, hint-level validation on the stream endpoint, and a code size cap
- [x] **H5** AI Celery tasks publish a result on non-200 responses too
- [x] **H6** Razorpay webhook (`payment.captured` / `order.paid`); `Payment.user` becomes `SET_NULL` so financial records survive account deletion
- [x] **H7** Chat/WS: Origin allowlist, no tokens in query strings, revoked tokens and disabled users rejected
- [x] **H8** Ingress (and compose nginx) stop exposing `/ai`; admin URL configurable; prod `ALLOWED_HOSTS` explicit; `USE_X_FORWARDED_HOST` off by default; API schema staff-only outside dev
- [x] **H9** Frontend stops writing tokens to `localStorage` (and purges old ones); WebSockets use cookies
- [x] **H10** Execute/submit tasks register task metadata so the polling fallback works
- [ ] **H11** GitHub OIDC deploy role was assumable from any branch (`repo:...:*`)
  - [x] Trust policy limited to the `production` GitHub environment; both deploy jobs run in it
  - [ ] 👤 Apply `infra/aws-bootstrap/github-trust-policy.json` to the IAM role and add required reviewers to the `production` environment

### 🟡 Reliability and operations

- [x] **R1** gunicorn config (gthread workers/threads/timeouts) for core
- [x] **R2** `collectstatic` at image build; migrations run as a k8s Job before rollout
- [x] **R3** Pod `securityContext` everywhere; no SA tokens; NetworkPolicies actually included in kustomize
- [x] **R4** Per-service secrets (executor, chat, ai, analytics no longer get the whole `backend-secrets`)
- [x] **R5** Health: `/health/live/` (no deps) for liveness, `/health/` for readiness, no exception text in responses
- [x] **R6** Celery: correct route names, one worker deployment per queue, task time limits, `prefetch=1`, beat `Recreate`
- [x] **R7** Chat: one Redis pattern subscription per pod instead of one per user; atomic rate-limit window
- [x] **R8** Upload limits on avatar/banner/post/store images, and the file must really be a JPEG/PNG/GIF/WebP
- [x] **R9** Sentry sampling and PII configurable (low defaults) in every service
- [x] **R10** No mutable `:prod` image tag; ECR tags immutable
- [ ] **R11** Terraform: S3 remote state with locking, nodes in private subnets (+ NAT), restricted API endpoint, IMDSv2 hop limit 1, KMS secrets encryption, IRSA (chat, external-secrets), Redis replication group with AUTH + TLS, DynamoDB PITR, VPC CNI network policy
  - [x] Code written; `terraform validate` passes for prod, dev and bootstrap
  - [ ] 👤 Apply `infra/terraform/bootstrap`, run `terraform init -migrate-state` in prod, set `eks_public_access_cidrs`, review `terraform plan` (node group and Redis are **replaced**, NAT adds cost), then put the `redis_url` output into the secrets
- [x] **R12** Structured JSON logging (`LOG_FORMAT=json`) and baseline PrometheusRule alerts (`infra/k8s/monitoring`)

### 🧪 Testing and CI

- [x] **T1** CI runs the core Django test suite (+ an informational job on real Postgres)
- [x] **T2** CI Python version matches each service's Docker image (executor 3.12, others 3.11); Node 24
- [x] **T3** Trivy scans the image *before* it is pushed; Trivy action pinned by commit SHA
- [x] **T4** CI validates rendered manifests (kubeconform) and `terraform fmt/validate`; `makemigrations --check`
- [x] **T5** Tests cover the new security behaviour (sandbox, harness, unlock, webhook, logout, OAuth, chat auth, uploads)
- [x] **T6** Frontend tests for auth/token handling; the existing suite was repaired (it never ran)
- [x] **T7** Frontend sourcemaps hidden from the public bundle (`hidden` + deleted after Sentry upload)
- [ ] **T8** 👤 First CI run on GitHub: confirm the Linux-only executor tests (rlimits: fork, memory, file writes) and the core-on-Postgres job pass, then make the Postgres job blocking. Not runnable locally (no Docker/Linux here).

### 📦 Dependencies

- [x] **D1** Known CVEs fixed: Django 5.0 (EOL) → 5.2 LTS, DRF, Pillow, PyJWT, requests, python-dotenv, Starlette (via FastAPI), LangChain 0.3 → 1.x, razorpay 2.x (drops the `setuptools<81` pin), npm (vite, axios, react-router, firebase 13, vitest 4, …). `pip-audit` and `npm audit` are now CI gates.

### Also fixed along the way

- Daily check-in crashed (500) and streaks broke between 00:00 and 05:30 IST: UTC vs local dates. Now `timezone.localdate()` everywhere.
- The 6-hourly RAG prewarm beat job never ran (unregistered task name).
- The dev kustomize overlay could not build (referenced a file outside its root).
- The analytics image ran as root with unpinned, unused dependencies.
- GitHub sync task could fire before its push log was committed (now `on_commit`).

### 👤 Rollout checklist (in order)

1. Rotate the Supabase DB password **now**; then purge history (C1 notes).
2. Add the new keys to AWS Secrets Manager `clashcode/prod/backend`:
   - `EXECUTOR_API_KEY`, `EXECUTOR_SIGNING_SECRET` (new, different from `INTERNAL_*`)
   - `RAZORPAY_WEBHOOK_SECRET`, `CHAT_CORS_ORIGINS`, `AI_CORS_ORIGINS`, `SENTRY_DSN`
   - `DJANGO_ADMIN_URL`, `NUM_PROXIES=1`, `LOG_FORMAT=json`
   - Explicit `ALLOWED_HOSTS`

   Don't rotate `SECRET_KEY` casually: GitHub sync tokens are encrypted with a key derived from it.
3. Razorpay dashboard → Webhooks: `https://<api-host>/api/payments/webhook/`, events `payment.captured`, `order.paid`, `payment.failed`, with the secret from step 2.
4. Terraform (R11). Then install the AWS Load Balancer Controller with `--aws-region` and `--aws-vpc-id`, because IMDS is blocked for pods.
5. Install External Secrets and annotate its service account with the role from `terraform output external_secrets_irsa_role_arn`.
6. IAM trust policy and the GitHub `production` environment (H11).
7. gVisor on nodes, then enable `components/gvisor` (C2).
8. Local dev: add `EXECUTOR_API_KEY` and `EXECUTOR_SIGNING_SECRET` to `services/.env` (compose now requires them) and refresh your untracked `infra/k8s/overlays/dev/secrets.yaml` from the example.

### Notes

**C1 — purging the leaked file from history** (rewrites public history; everyone must re-clone afterwards):

```bash
pip install git-filter-repo
git filter-repo --path infra/k8s/overlays/dev/secrets.yaml --invert-paths
git push --force --all && git push --force --tags
```

Rotating the password matters more than the purge: forks and caches may already hold the old value.

**C3 — threat model.** The harness stops the trivial ways to fake a pass. User code still runs in the same Python process as the tests, so a determined attacker could tamper with it. Don't attach real-money value to completions without a stronger out-of-process judge.

**Executor isolation limits.** Runs share one Unix user inside the executor pod, so a run could read the pod's own environment (only the executor key) or another concurrent run's temporary files. The pod has no egress and no other secrets, so this is contained. Per-run users or microVMs would close it fully.
