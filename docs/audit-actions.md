# Audit actions

## M00 Foundation

`auth.login.succeeded`, `auth.login.failed`, `auth.logout`, `user.registered`, `user.invited`,
`invitation.accepted`, `invitation.expired`, `invitation.revoked`, `role.granted`, `role.revoked`,
`mfa.enabled`, `mfa.disabled`, `password.reset`, `file.uploaded`, `file.downloaded`,
`file.deleted`, `setting.changed`, `job.run`.

Denied and failed actions are persisted through a separate database transaction so request rollbacks cannot remove them.

## M01 Catalog

`program.created`, `program.edited`, `program.confirmed`, `program.archived`,
`offering.created`, `offering.edited`, `offering.published`, `offering.unpublished`,
`inquiry.received`, `inquiry.assigned`, `inquiry.transitioned`, `trial.scheduled`,
`trial.transitioned`, `faq.created`, `faq.edited`.
