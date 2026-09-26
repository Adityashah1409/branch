# Multi Branch Management (core)

Technical name: `branch_management` · Odoo 20.0 · LGPL-3

Foundation of the branch framework. Depends only on `base`, `web` and
`base_setup`; application integrations are separate `branch_management_*`
modules.

## What it provides

| Area | Details |
| --- | --- |
| Branch master `res.branch` | name, unique code per company, company, unlimited hierarchy (`parent_id`, `complete_name` "Head Office / Gujarat / Ahmedabad"), manager, address, phone, mobile, email, website, logo, optional contact, sequence prefix, archive |
| Users | `allowed_branch_ids` (security boundary), `default_branch_id` (user preference, must be allowed), `current_branch_id` (working branch of the session, computed) |
| Groups | Branch **User** (every internal user), **Manager** (create branches, edit and staff the branches they are allowed in), **Administrator** (full configuration, not restricted; implied by Settings administrators) |
| Branch selector | systray dropdown listing the valid branches of the active company; the choice is kept in a browser cookie and sent in the user context; nothing is written in the database |
| `res.branch.mixin` | reusable abstract model making a document branch-aware (default, validations, "Current Branch" filter) |
| Numbering | optional branch sequences `AHM/SO/00001` (Settings > General Settings > Branches) |
| Reports | `branch_management.branch_address_block` QWeb snippet for printed documents |
| Wizard | Assign Users to Branches (grant / revoke in bulk) |

## Configuration

1. *Settings > Users & Companies > Branches*: create the branches.
2. On each user (*Access Rights* tab > *Branches*) or on the branch
   (*Users* tab, or *Assign Users* button): grant branches, pick a default.
3. Optionally enable *Branch Sequence Prefix* in *Settings > General
   Settings > Branches*.

## Security model (mode C)

* **Allowed branches = security boundary.** Integration modules declare a
  group-less `ir.access` restriction on their documents:
  `[] if user.branch_unrestricted else ['|', ('branch_id', '=', False), ('branch_id', 'in', user.allowed_branch_ids.ids)]`.
  It applies to every ORM/RPC/URL access, not only to menus.
* **Current branch = working context.** Used for default values and the
  *Current Branch* search filter. The branch sent by the browser is never
  trusted: `res.users._get_current_branch()` re-validates it against the
  allowed, active branches of the active company on every request.
* Branch users cannot change their allowed branches (`allowed_branch_ids`
  is not user-writeable) and cannot staff branches (no write access on
  `res.branch`). Managers only edit/staff the branches they are allowed in.
* Archived branches stay in the security boundary so that historical
  documents remain readable; they disappear from the selector and cannot be
  picked as default.
* Branches referenced by any document cannot be deleted (archive them).

## Tests

`tests/` covers TC-001..TC-010, TC-020, TC-023 (including a real browser
tour of the selector), TC-024 and TC-025.

```bash
odoo-bin -d test_db -i branch_management --test-tags /branch_management --stop-after-init
```

## Known limitations

* The selector sets one working branch; users working in several branches
  switch explicitly (records of all allowed branches remain accessible).
* Odoo's own "company branches" (child companies, `res.company.parent_id`)
  are a different concept: they are separate legal/fiscal entities. This
  module's branches live *inside* one company.
