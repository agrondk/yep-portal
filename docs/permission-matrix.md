# Permission matrix

Generated from module permission declarations.

| Role | M00 Foundation | M01 Catalog |
| --- | --- | --- |
| `owner_admin` | `core.*` | `catalog.*` |
| `operations_coordinator` | `core.file.create`, `core.file.view`, `core.invitation.create`, `core.invitation.view`, `core.job.view`, `core.location.create`, `core.location.edit`, `core.location.view`, `core.user.create`, `core.user.edit`, `core.user.view` | `catalog.inquiry.assign`, `catalog.inquiry.transition`, `catalog.inquiry.view`, `catalog.offering.create`, `catalog.offering.edit`, `catalog.offering.view`, `catalog.program.confirm`, `catalog.program.create`, `catalog.program.edit`, `catalog.program.view`, `catalog.room.create`, `catalog.room.edit`, `catalog.room.view`, `catalog.trial.schedule`, `catalog.trial.transition`, `catalog.trial.view` |
| `finance_officer` | `core.file.create`, `core.file.view`, `core.job.view`, `core.user.view` | `catalog.offering.view`, `catalog.program.confirm_price`, `catalog.program.view` |
| `instructor` | `core.file.create`, `core.file.view` | — |
| `marketing_coordinator` | — | — |
| `guardian` | `core.file.create`, `core.file.view` | — |
| `student` | — | — |
| `school_coordinator` | — | — |
| `sponsor` | — | — |
