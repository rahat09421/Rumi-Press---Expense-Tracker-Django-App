# Permission System (RBAC)

- Roles:
  - Superuser: full administrative rights.
  - Admin: read-only across all data; can insert new records; can edit only records they created; cannot delete any data.

- Enforcement:
  - View mixins guard update/delete and stamp `created_by` on create.
  - Bulk delete endpoints block Admin users.

- Audit Logging:
  - Logs all admin GET (read) and write actions with timestamp, actor, model, object_id.

- Email Verification:
  - Superuser creates admin accounts; verification link sent to console email backend.

- Tests:
  - Cover admin viewing, creating, blocking delete, blocking editing others, superuser admin creation.