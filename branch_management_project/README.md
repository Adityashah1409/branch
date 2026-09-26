# Multi Branch Management - Project

Integration of `branch_management` with the Project application (Odoo 20.0).

## Features

* **Branch on projects** (`project.project.branch_id`, tracked), defaulting
  to the current branch.
* **Branch on tasks**: stored, read-only `project.task.branch_id` related to
  the task's project. Changing the project (or the project's branch) moves
  the tasks with it.
* Project and task lists/search: branch column, *Current Branch* filter and
  *Branch* group-by; `branch_id` added to the *Tasks Analysis* SQL report
  (`report.project.task.user`) with its group-by.
* **Smart button** *Projects* on the branch form (project users only).

## Security

Group-less `ir.access` **restrictions** on `project.project`,
`project.task` and `report.project.task.user`:

```
[] if user.branch_unrestricted else
['|', ('branch_id', '=', False), ('branch_id', 'in', user.allowed_branch_ids.ids)]
```

* private tasks and tasks without project have no branch: they stay visible
  to everybody allowed by the Project rules;
* being assignee or follower of a task of another branch does not bypass the
  boundary;
* portal users (project sharing) are governed by the Project portal rules
  only (external users are unrestricted by branches); the branch column is
  hidden from them.

Projects may have no company ("visible to all"), so the branch field does not
use `check_company`; the mixin constraint enforces branch company = project
company whenever a company is set. Using a branch the user is not allowed in
raises a `ValidationError`.
