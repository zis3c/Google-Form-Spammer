# FormForge - Capabilities & Awareness

## 1. What This Tool Does

FormForge automates Google Forms submissions. It parses a public form's structure, generates synthetic responses from configured weights, quotas, or random data, and posts them concurrently to Google's `formResponse` endpoint. Throughput is bounded by concurrency and rate limiting rather than by browser automation: a few hundred workers can submit thousands of responses in seconds, and the resulting response sheet is indistinguishable from ordinary entries.

Beyond volume, the quota engine lets an operator target an *exact* distribution — forcing a Likert scale to a chosen positivity rate, clustering numeric answers into one range, or fixing an option split — while still producing individually plausible records. Presets can be exported, reviewed, and replayed later, so a distribution is reproducible and diffable.

It rotates User-Agent headers to mimic ordinary browser traffic and retries 408/429/5xx responses with exponential backoff, so soft rate limits only slow it down instead of stopping it.

An HTTP 200 from `formResponse` does not by itself prove a response was stored: Google also answers with a page when a form is closed or a required answer is rejected. FormForge reads that page and classifies each attempt as verified, rejected, closed, or unverified, so a run report does not silently count refused submissions as successes. `--report run.jsonl` keeps one line per attempt (answers, verdict, error) plus a run summary, and the CLI compares configured quotas against the answers that were actually accepted.

---

## 2. How to Stop This *(For Form Creators)*

FormForge only works against **public, anonymous** forms. Adding any authentication requirement makes it completely ineffective.

### A. Require Google Sign-In *(Most Effective)*
- Go to your Google Form **Settings** tab.
- Under **Responses**, turn ON **"Limit to 1 response"**.
- **Why it works:** Every respondent must sign in with a real Google account. FormForge never authenticates, so its submissions are rejected outright.

### B. Add a File Upload Question
- In your form editor, add a question and select **"File upload"**.
- **Why it works:** Google requires sign-in for any form accepting uploads; there is no anonymous path to submit.

### C. Collect Verified Emails
- Go to **Settings → Responses → Collect email addresses** and choose **"Verified"**.
- **Why it works:** Verified collection requires a signed-in respondent, blocking scripted submissions.

### D. Treat Public Results With Suspicion
- If a public form's data matters, check response timestamps for bursts, duplicate User-Agent/geo patterns, and distributions that are implausibly clean. FormForge's quota engine makes distributions *exactly* as configured, which is itself a detectable signature.

---

## Summary

FormForge only affects forms open to the public with no authentication. Add a sign-in requirement — limit responses, upload files, or collect verified email — and the tool cannot submit anything. Distributions produced by its quota engine are exact by design, so implausible uniformity in a public form's results is a strong indicator of automated submission.