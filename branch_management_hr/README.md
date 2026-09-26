# Multi Branch Management - Employees

Integration of `branch_management` with the Employees application (Odoo 20.0).

## Features

* **Branch on employees** (`hr.employee.branch_id`, tracked), defaulting to
  the current branch; also exposed on the public employee directory
  (`hr.employee.public`) for search and grouping.
* **Branch on departments** (optional `hr.department.branch_id`): picking a
  department in the employee form proposes its branch (onchange only, nothing
  automatic otherwise).
* Employee list/search: branch column, *Current Branch* filter and *Branch*
  group-by (also in the employee directory); department form, list and
  search.
* **Smart button** *Employees* on the branch form (HR officers only).

## Security choice

Odoo 20 serves employees through two models:

* `hr.employee`: the full HR record, readable only by HR officers
  (`hr.group_hr_user`);
* `hr.employee.public`: the company-wide directory used by every internal
  user (directory, org chart, avatar cards, many2one fields to employees).
  `hr.employee` transparently falls back to it for users without HR rights.

This module adds group-less `ir.access` **restrictions** on `hr.employee`
and on `hr.version` (the contract/record data of an employee), for all
operations. In practice they only affect HR officers and managers, who
now manage the employees of their allowed branches (plus employees without
branch); branch administrators are unrestricted.

`hr.employee.public` is deliberately **not** restricted: everybody keeps the
full company directory and org chart (a manager or colleague in another
branch stays visible), and users linked to an employee of another branch keep
reading their own profile (the related user fields are read as superuser by
Odoo). The branch is informative in the directory.

Limitation: in the *Employees* app (which uses `hr.employee` for HR
officers), a restricted HR officer's hierarchy/org chart only shows the
employees they can access; the *Employee Directory* (public model) still
shows the whole structure.

Using a branch the user is not allowed in raises a `ValidationError`; a
department dedicated to a branch must belong to the branch's company.
