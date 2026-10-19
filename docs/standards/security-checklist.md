# Security Checklist (mandatory review items)

| # | Check | Criterion |
|---|---|---|
| S1 | Admin API authentication | `/admin/**` always goes through the `require_admin` dependency |
| S2 | SQL injection | No string-concatenated SQL; use parameter binding only |
| S3 | No personal data in logs | Do not record names, e-mail addresses, phone numbers, etc. in logs or the audit log (customer ID only) |
| S4 | **Free-text input** | Free input such as reasons and memos has a length limit (for example 200 characters) and whitespace trimming, and the raw text is not written to the access log |
| S5 | Input validation | Amounts are positive integers, and the maximum length of strings is enforced in the schema |
| S6 | Secrets | Do not hard-code tokens or passwords in code, documents or logs (a demo token is marked as an exception) |
| S7 | Permission changes | A change that relaxes admin permissions or approval rules must always be marked as needing a separate approval |
