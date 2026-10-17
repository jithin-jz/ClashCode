# External Secrets Management

| Provider | AWS Secrets Manager |
| --- | --- |
| Operator | External Secrets (ESO) |
| Identity | IAM Roles for Service Accounts (IRSA) |

Syncs credentials from AWS Secrets Manager into Kubernetes Secrets.

## Architecture

1. **Source:** one JSON document in Secrets Manager, `clashcode/prod/backend`.
2. **Store:** `ClusterSecretStore` connects to AWS using the IRSA role of the `external-secrets` service account.
3. **Sync:** `external-secret.yaml` builds one Kubernetes Secret per service. Each service only receives the keys it needs:

| Secret | Used by | Contents |
| --- | --- | --- |
| `backend-secrets` | core, Celery workers, beat, migrate job | whole document |
| `executor-secrets` | executor | `EXECUTOR_API_KEY`, `EXECUTOR_SIGNING_SECRET`, `SENTRY_DSN` |
| `chat-secrets` | chat | JWT public key, Redis URL, DynamoDB table, region, CORS origins |
| `ai-secrets` | ai | internal + executor keys, LLM and Pinecone settings |

Every property referenced in `external-secret.yaml` must exist in the JSON document. Use `""` for values you don't use, such as `SENTRY_DSN`. Besides the backend keys, the document needs:

* `EXECUTOR_API_KEY`
* `EXECUTOR_SIGNING_SECRET`
* `CHAT_CORS_ORIGINS`
* `AI_CORS_ORIGINS`
* `RAZORPAY_WEBHOOK_SECRET`
* `SENTRY_DSN`

## Provisioning

1. **Data:** create or update `clashcode/prod/backend` (JSON) in `ap-south-1`.
2. **Identity:** `terraform apply` in `infra/terraform/environments/prod` creates the IRSA role. It allows `secretsmanager:GetSecretValue` and `secretsmanager:DescribeSecret` on `clashcode/prod/*`. Read its ARN with:
   ```bash
   terraform output external_secrets_irsa_role_arn
   ```
3. **Cluster:**
   ```bash
   # Deploy the operator
   kubectl apply -f https://github.com/external-secrets/external-secrets/releases/download/v0.10.7/external-secrets.yaml
   kubectl -n external-secrets annotate serviceaccount external-secrets \
     eks.amazonaws.com/role-arn=<external_secrets_irsa_role_arn> --overwrite

   # Store and per-service secrets
   kubectl apply -f cluster-secret-store.yaml
   kubectl apply -f external-secret.yaml
   ```

## Security rationale

* No static, long-lived AWS credentials in the cluster.
* A compromised pod only exposes its own service's secrets. The executor, which runs untrusted code, holds nothing but its own key.
* Rotation is automatic (`refreshInterval: 1h`), and every read is audited in CloudTrail.
