

\# TrustVault – Security Threat Model



\## 1. Project Overview



TrustVault is a Flask-based document management application. It provides authentication, document uploads, permission management, sharing, and audit-related functionality.



\## 2. Assets to Protect



\- User account credentials

\- Uploaded PDF documents

\- Document ownership information

\- Document permissions and sharing settings

\- Audit records

\- Application configuration and secret keys



\## 3. Threats and Mitigations



\### Threat 1 – Unauthorized Document Access

\*\*Risk:\*\* An unauthenticated or unauthorized user may attempt to access private documents.



\*\*Mitigation:\*\* Require authentication and verify document permissions before granting access.



\### Threat 2 – Privilege Escalation

\*\*Risk:\*\* A view-only user may attempt to edit, replace, or delete a document.



\*\*Mitigation:\*\* Enforce authorization checks on the server-side routes, not only in the frontend.



\*\*Verification:\*\* Manual tests showed HTTP 403 responses for viewer requests to replace, edit, and edit-PDF routes.



\### Threat 3 – Malicious File Upload

\*\*Risk:\*\* An attacker may upload an unsafe or unexpected file.



\*\*Mitigation:\*\* Validate uploaded file types, filenames, and upload handling. Store uploads safely and avoid executing uploaded content.



\### Threat 4 – Credential Exposure

\*\*Risk:\*\* Application credentials or secret keys may accidentally be exposed in source control.



\*\*Mitigation:\*\* Keep environment files and local configuration out of Git using `.gitignore`. Avoid hardcoding secrets.



\### Threat 5 – Session Abuse

\*\*Risk:\*\* An attacker may attempt to reuse or steal an authenticated session.



\*\*Mitigation:\*\* Use secure session configuration, protect authentication routes, and apply appropriate cookie settings.



\### Threat 6 – Audit Log Tampering

\*\*Risk:\*\* A malicious user may attempt to modify or hide records of document activity.



\*\*Mitigation:\*\* Restrict access to audit records and record important security-related actions.



\## 4. Security Testing



The project includes automated tests in `tests/test\_app.py`.



Previously observed test result:

\- 7 tests passed.



Manual authorization testing:

\- Viewer access to replace route: HTTP 403

\- Viewer access to edit route: HTTP 403

\- Viewer access to edit-PDF route: HTTP 403



A pattern-based secret scan found no matches. This is not a complete security audit.



\## 5. Remaining Security Improvements



\- Verify file-upload validation against malicious and oversized files.

\- Verify session and cookie security settings.

\- Test authorization for every document operation.

\- Verify audit events and protection against tampering.

\- Perform dependency and vulnerability checks.

\- Review deployment configuration before production use.



\## 6. Conclusion



TrustVault applies authentication and server-side permission checks to protect document operations. Automated and manual testing provide initial evidence of access-control behavior. Additional security testing is required before production deployment.



