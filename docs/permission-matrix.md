# Permission matrix

Generated from module permission declarations.

| Role | M00 permissions |
| --- | --- |
| `owner_admin` | `core.*` |
| `operations_coordinator` | `core.file.create`, `core.file.view`, `core.invitation.create`, `core.invitation.view`, `core.job.view`, `core.location.create`, `core.location.edit`, `core.location.view`, `core.user.create`, `core.user.edit`, `core.user.view` |
| `finance_officer` | `core.file.create`, `core.file.view`, `core.job.view`, `core.user.view` |
| `instructor` | `core.file.create`, `core.file.view` |
| `marketing_coordinator` | — |
| `guardian` | `core.file.create`, `core.file.view` |
| `student` | — |
| `school_coordinator` | — |
| `sponsor` | — |

## M01 Catalog

| Role | Permissions |
| --- | --- |
| `owner_admin` | `catalog.*` |
| `operations_coordinator` | Programs view/create/edit and non-price confirmation; offerings and rooms view/create/edit |
| `finance_officer` | Programs and offerings view; price confirmation |
| Other roles | Public catalog only |
