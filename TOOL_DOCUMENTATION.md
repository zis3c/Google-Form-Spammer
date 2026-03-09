# google-form-spammer - Capabilities & Awareness

## 1. What This Tool Does

google-form-spammer is a high-speed, asynchronous Google Forms submission tool. It is capable of sending 1,000+ fake responses in under 10 seconds.

It works by launching dozens of async workers simultaneously. These workers automatically discover every question in your form (including Text, MCQ, Checkboxes, Date, and Time fields) and fill them with randomly generated or custom-configured answers. Because it sends direct POST requests to Google's `formResponse` endpoint without ever loading a browser, it bypasses standard client-side protections and can saturate a form's response sheet in under a minute.

It also rotates User-Agent headers to mimic legitimate browser traffic and handles 429 Rate Limit responses gracefully, retrying automatically to maximize throughput.

---

## 2. How to Stop This Spam *(For Form Creators)*

If you are a form creator and want to block this tool, you need to enable specific security settings in Google Forms. This tool only works against **public, anonymous** forms. The moment you require authentication, it becomes completely ineffective.

### A. Require Google Sign-In *(Most Effective)*
- Go to your Google Form **Settings** tab.
- Under **Responses**, turn ON **"Limit to 1 response"**.
- **Why it works:** This forces every respondent to sign in with a real Google account before submitting. This tool does not authenticate with Google, so it is instantly and completely blocked.

### B. Add a File Upload Question
- In your form editor, add a new question and select **"File upload"** as the type.
- **Why it works:** Google automatically requires sign-in for any form that accepts file uploads. The spammer cannot bypass the login screen, so all submissions are rejected.

### C. Collect Verified Emails
- Go to **Settings → Responses → Collect email addresses**.
- Choose **"Verified"**.
- **Why it works:** Verified email collection requires the respondent to be signed in, blocking all anonymous script-based submissions.

---

## Summary

This tool only affects forms that are open to the public without any authentication requirement. As soon as you add a sign-in requirement (by limiting responses, adding a file upload question, or collecting verified emails), this tool becomes completely useless against your form.
