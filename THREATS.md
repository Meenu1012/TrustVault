# TrustVault – Security Threat Model

## 1. Project Overview

TrustVault is a secure document management system developed using Python Flask.

The application provides user authentication, document uploading, viewing, downloading, sharing, editing, replacing, deletion and audit logging.

It uses server-side authorization and document-level permissions to control access to private documents.

This document identifies potential security threats, their impact, implemented protections and additional security tests required.

## 2. Assets to Protect

The important assets of TrustVault are:

- User account credentials.
- User authentication sessions.
- Uploaded PDF and TXT documents.
- Document ownership information.
- Document sharing permissions.
- Admin and normal user roles.
- Audit records and activity history.
- Application configuration and secret keys.
- Database and storage credentials.

## 3. Threats, Risks and Mitigations

### Threat 1 – Unauthorized Document Access

**Risk:**

An unauthenticated or unauthorized user may attempt to access another user's private document by directly entering its URL.

**Impact:**

Private documents may be exposed to unauthorized users.

**Mitigation:**

- Require authentication for protected document routes.
- Verify document ownership or explicit sharing permission.
- Perform permission checks on the server before returning document contents.
- Do not rely only on frontend restrictions.

**Verification:**

Manual testing was performed using accounts with different permissions. Unauthorized document requests returned HTTP 403 in the tested cases.

### Threat 2 – Privilege Escalation

**Risk:**

A normal user may attempt to access administrator-only functions or gain additional permissions.

**Impact:**

Unauthorized administrative operations or access to restricted information.

**Mitigation:**

- Enforce role checks on protected server-side routes.
- Restrict administrative operations to authorized administrators.
- Do not trust role information submitted by the browser.
- Validate permissions before performing sensitive operations.

**Verification:**

Administrator and normal-user access should be tested separately. Full verification of every administrative route remains necessary.

### Threat 3 – Unauthorized Document Editing

**Risk:**

A user with View Only permission may attempt to edit a TXT or PDF document.

**Impact:**

Document contents could be changed without authorization.

**Mitigation:**

- Check edit permission separately from view permission.
- Verify permissions before processing edit requests.
- Apply server-side checks to both TXT and PDF editing routes.

**Verification:**

Manual testing showed HTTP 403 responses for viewer requests to the tested edit and edit-PDF routes.

### Threat 4 – Unauthorized Document Replacement

**Risk:**

A user without Edit permission may attempt to replace an existing document.

**Impact:**

Original document contents may be overwritten or lost.

**Mitigation:**

- Verify ownership or explicit Edit permission before accepting replacement uploads.
- Reject replacement requests from unauthorized users.
- Keep the existing document record and sharing permissions during replacement.

**Verification:**

Manual testing showed that a View Only user was denied access to the tested replacement route.

### Threat 5 – Unauthorized Document Deletion

**Risk:**

A user may attempt to delete a document that they do not own or are not authorized to manage.

**Impact:**

Important documents may be permanently lost.

**Mitigation:**

- Verify document ownership and authorization before deletion.
- Restrict deletion operations to permitted users.
- Record deletion activities in the audit trail.

**Verification:**

Deletion authorization and audit logging require additional testing.

### Threat 6 – Insecure Direct Object Reference (IDOR)

**Risk:**

An attacker may change a document ID in a URL or request to access another user's document.

**Impact:**

Unauthorized viewing, downloading, editing, replacement or deletion.

**Mitigation:**

- Retrieve the requested document on the server.
- Check the current user's permissions for every protected operation.
- Never assume that knowing a document ID grants access.
- Apply authorization checks consistently across routes.

**Verification:**

Test different document IDs using owner, authorized recipient and unauthorized accounts. Complete route-by-route verification remains necessary.

### Threat 7 – Malicious File Upload

**Risk:**

An attacker may upload unsupported, unexpected or potentially malicious files.

**Impact:**

Unsafe files may be stored or exposed to users.

**Mitigation:**

- Validate permitted file extensions.
- Use secure filename handling.
- Enforce upload size limits.
- Avoid executing uploaded content.
- Return appropriate errors for invalid uploads.

**Verification:**

Unsupported extensions, empty filenames and oversized uploads should be tested before deployment.

### Threat 8 – Cross-Site Request Forgery (CSRF)

**Risk:**

An attacker may trick an authenticated user into submitting an unwanted request.

**Impact:**

Unauthorized sharing, document changes or other sensitive actions.

**Mitigation:**

- Use Flask-WTF CSRF protection.
- Include valid CSRF tokens in applicable forms.
- Reject requests with missing or invalid CSRF tokens.

**Verification:**

CSRF protection is configured in the application. Missing-token and invalid-token requests require additional testing.

### Threat 9 – Credential and Secret Exposure

**Risk:**

Application secret keys, database credentials or storage credentials may accidentally be exposed through source control.

**Impact:**

Attackers may gain access to application resources or sensitive information.

**Mitigation:**

- Store secrets in environment variables.
- Exclude `.env` and local secret files using `.gitignore`.
- Never commit passwords, API keys or private credentials.
- Review tracked files before publishing the repository.

**Verification:**

A previous pattern-based secret scan found no matches. This does not guarantee that all secrets are absent. A final Git tracking and repository review is required.

### Threat 10 – Session Abuse

**Risk:**

An attacker may attempt to reuse or steal an authenticated user's session.

**Impact:**

Unauthorized access to the victim's account.

**Mitigation:**

- Use secure authentication and session management.
- Configure HTTPOnly and SameSite cookie settings.
- Use HTTPS in production.
- Invalidate the session when a user logs out.

**Verification:**

Session and cookie configuration should be reviewed, and logout behavior should be tested.

### Threat 11 – Audit Log Tampering

**Risk:**

A malicious user may attempt to modify or remove activity records.

**Impact:**

Loss of accountability and unreliable activity history.

**Mitigation:**

- Restrict audit-related operations.
- Record important document activities.
- Prevent ordinary users from modifying audit records through application routes.
- Keep database access restricted.

**Verification:**

Audit event creation and unauthorized modification attempts require additional testing.

### Threat 12 – Unauthorized Document Sharing

**Risk:**

A user may attempt to share documents with unauthorized accounts or change another user's sharing permissions.

**Impact:**

Private documents may be exposed to unintended recipients.

**Mitigation:**

- Verify authorization before creating or modifying sharing permissions.
- Distinguish View Only and Edit Access.
- Restrict permission updates and removal to authorized users.
- Recheck permissions whenever a shared document is accessed.

**Verification:**

Test sharing, permission changes and access removal using separate user accounts.

## 4. Security Controls Implemented

The following protections are present in the application:

- Flask authentication and login protection.
- Admin and normal-user roles.
- Server-side document permission checks.
- Document ownership checks.
- View Only and Edit Access permissions.
- CSRF protection configuration.
- HTTPOnly and SameSite session cookie configuration.
- Upload size configuration.
- Secure filename handling.
- Audit logging for document activities.

The effectiveness of each control must be verified through testing.

## 5. Security Testing Evidence

### Previously Reported Automated Tests

The previously observed test result was:

**7 tests passed.**

Test results should be reproduced using the current project version before final submission.

### Previously Performed Manual Authorization Tests

| Test | Observed result |
|---|---|
| View-only user accessing replacement route | HTTP 403 |
| View-only user accessing TXT edit route | HTTP 403 |
| View-only user accessing PDF edit route | HTTP 403 |

These results apply only to the tested accounts and routes.

### Additional Tests Required

- [ ] Unauthenticated users cannot access protected document routes.
- [ ] Unauthorized users cannot view documents.
- [ ] Unauthorized users cannot download documents.
- [ ] View-only users cannot edit documents.
- [ ] View-only users cannot replace documents.
- [ ] Unauthorized users cannot delete documents.
- [ ] Users cannot modify sharing permissions without authorization.
- [ ] Normal users cannot access administrator-only routes.
- [ ] Changing document IDs does not bypass permissions.
- [ ] Unsupported file types are rejected.
- [ ] Oversized uploads are rejected.
- [ ] Missing or invalid CSRF tokens are rejected.
- [ ] Logout invalidates the session.
- [ ] Important activities are recorded in audit logs.
- [ ] Ordinary users cannot modify audit records through application routes.
- [ ] No application secrets are committed to GitHub.

## 6. Known Limitations and Future Improvements

The following areas require further verification or improvement:

1. Complete security testing of every protected route.
2. Testing malicious, unsupported and oversized file uploads.
3. Verification of session expiration and logout behavior.
4. Verification of CSRF protection on sensitive operations.
5. Complete audit-log integrity testing.
6. Dependency vulnerability checking.
7. Production environment and storage security review.
8. Testing authorization against the deployed application.

TrustVault should not be considered fully security-audited until these checks are completed.

## 7. Conclusion

TrustVault implements authentication, role-based access control, document-level permissions and audit logging to protect document operations.

The application has undergone initial automated and manual testing, including authorization checks for selected document operations.

The remaining security tests are documented transparently so that unfinished verification is not presented as completed work.

The goal is to ensure that every sensitive document operation is authorized on the server and that important activities can be traced through audit records.