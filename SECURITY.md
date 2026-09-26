# Security model

## Mode C: allowed branches are the boundary, the current branch is the context

* `res.users.allowed_branch_ids` is the **security boundary**. Each
  integration module declares a *restriction*, which is a group-less row in
  Odoo 20's `ir.access`. Restrictions apply to every user and are AND-ed
  with every other rule:

  ```python
  [] if user.branch_unrestricted else
  ['|', ('branch_id', '=', False), ('branch_id', 'in', user.allowed_branch_ids.ids)]
  ```

  They are enforced by the ORM for search, read, write, create and unlink,
  so they hold for the UI, RPC/JSON-2 calls and direct URLs alike, not just
  menus.
* The **current branch** is only a working context, used for defaults and
  filters. The branch id sent by the browser (cookie, then user context) is
  never trusted: `res.users._get_current_branch()` checks it on every use
  against the user's active, allowed branches in the active company.
* Documents without a branch stay visible to everyone the other rules allow.
* **Unrestricted users**: branch administrators, plus portal and public
  users, whose access is governed by their own rules (for example, a
  customer's own orders).

## Other safeguards

| Risk | Safeguard |
| --- | --- |
| Using a branch taken from the browser | `create`/`write` check that `branch_id` is allowed for the user before saving, with a `ValidationError`. The ORM restriction backs this up. |
| Mixing companies | The branch's company must equal the document's company (a constraint). Branches outside the enabled companies are hidden by a multi-company restriction on `res.branch`. |
| Giving oneself branches | `allowed_branch_ids` is not user-writeable. Users have no write access on `res.branch`. Managers can only staff branches they are allowed in. |
| Deleting history | Branch foreign keys are `ondelete='restrict'`, and an explicit check refuses to delete used branches. Archived branches stay inside the boundary. |
| `sudo()` leaks | Every `sudo()` in the code has a comment saying why it can't expose another branch's documents. None of them searches business documents for a user. |
| Stale caches | Changing allowed branches or groups clears Odoo's access-domain and ORM caches. |
| Licence tier | The *Branch User* group is declared a light group, so it does not turn light users into regular users. |

## Deliberately not restricted

Partners, products, stock quants, locations, warehouses and operation types,
and the public employee directory are shared data. Restricting them would
break reservations, messaging and the org chart. Each module's README
explains its own choices.

## How it is verified

The automated tests exercise the boundary through non-sudo environments:

* `search` must hide the other branch's records;
* `browse(id).read()`, `write` and `unlink` must raise `AccessError` (TC-012, TC-021);
* setting a forbidden branch must raise `ValidationError`;
* archived branches keep documents readable (TC-022);
* users with no branch and superuser behaviour (TC-024, TC-025);
* multi-company isolation (TC-009, TC-020).

## Reporting a vulnerability

Please open a private security advisory on the GitHub repository rather than
a public issue.
