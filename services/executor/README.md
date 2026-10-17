# Executor Service

| Framework | FastAPI |
| --- | --- |
| Isolation | Per-run subprocess sandbox inside a locked-down pod (gVisor in production) |
| Pre-check | AST validation (early rejection only, not a security boundary) |

Runs untrusted learner code.

## Security model

Each run is a fresh `python -I -S -B` process with:

* **Clean environment:** no executor secret is inherited.
* **Private working directory:** deleted after the run.
* **Rlimits (Linux):** CPU, address space, file size 0, 64 file descriptors, no fork/threads.
* **Kill on limit:** the whole process group is killed at the wall-clock timeout or when output exceeds the cap.
* **Concurrency limit:** at most `EXECUTOR_MAX_CONCURRENT_RUNS` runs at once.

The pod/container is the real boundary:

* no service-account token
* only the executor's own key (`executor-secrets`)
* non-root, read-only root filesystem, all capabilities dropped
* deny-all egress NetworkPolicy
* `runtimeClassName: gvisor` in production (`infra/k8s/overlays/prod/executor-gvisor.yaml`)

Challenge tests run in a trusted harness. A run passes only when the harness prints a random per-run token after every test, so `exit()` / `SystemExit` / `os._exit` cannot fake a pass.

## API

| Endpoint | Method | Description |
| --- | --- | --- |
| `/execute` | POST | Run code. Body: `code`, optional `stdin`, `test_code` (adds `passed`) or `test_cases` |
| `/health` | GET | Liveness; reports whether auth is configured |

Requests must carry `X-Internal-API-Key`, `X-Internal-Timestamp` and `X-Internal-Signature`: HMAC-SHA256 of `"<timestamp>:/execute"`, signed with `EXECUTOR_SIGNING_SECRET`.

## Configuration

| Variable | Default | Notes |
| --- | --- | --- |
| `EXECUTOR_API_KEY` / `EXECUTOR_SIGNING_SECRET` | falls back to `INTERNAL_*` | Without a key every `/execute` call is rejected (503) |
| `EXECUTOR_ALLOW_UNAUTHENTICATED` | `false` | Tests/local only |
| `EXECUTOR_TIMEOUT_SECONDS` | `5` | Wall clock per run |
| `EXECUTOR_MEMORY_LIMIT_MB` | `128` | Address-space limit |
| `EXECUTOR_OUTPUT_LIMIT_BYTES` | `32768` | Per stream |
| `EXECUTOR_MAX_CODE_BYTES` | `65536` | |
| `EXECUTOR_MAX_CONCURRENT_RUNS` | `4` | |
| `EXECUTOR_WORK_DIR` | system temp | Must be writable (`/tmp` emptyDir in k8s) |

## Run locally

```bash
EXECUTOR_ALLOW_UNAUTHENTICATED=true uvicorn main:app --port 8011
pytest -q
```
