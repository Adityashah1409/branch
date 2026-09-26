# Development guide

Target: **Odoo 20.0** (verified against the `20.0` branch of odoo/odoo).
License: LGPL-3. Version stem: `20.0.1.0.0`. Modules live at the repository root.

## Local environment

```bash
git clone --depth 1 --branch 20.0 https://github.com/odoo/odoo.git
python3.12 -m venv venv && ./venv/bin/pip install -r odoo/requirements.txt
# PostgreSQL 14+ running, a superuser role for the current OS user

./venv/bin/python odoo/odoo-bin -d branch_test \
    --addons-path=odoo/addons,<this repo> \
    -i branch_management_sale --test-tags /branch_management_sale \
    --stop-after-init --log-level=test
```

## Odoo 20 facts this code relies on (checked in the 20.0 source)

* **Security is `ir.access`** (`security/ir.access.csv`, columns
  `id,name,model_id,group_id/id,operation,domain`). `model_id` is the model
  *name* (`sale.order`), `operation` a subset of `crud`. There is no
  `ir.model.access` / `ir.rule` any more.
  * rows **with** a group are *permissions*: OR-ed together;
  * rows **without** a group are *restrictions*: AND-ed for everybody
    (this is how multi-company rules are written:
    `[('company_id', 'in', company_ids)]`).
  * Domains are evaluated with `user`, `company_ids`, `company_id`, `time`.
* Groups use `privilege_id` (`res.groups.privilege`), `implied_ids`, `user_ids`;
  users have `group_ids`.
* Constraints/indexes: `models.Constraint(...)`, `models.UniqueIndex(...)`
  (no `_sql_constraints`).
* `env.user` is a **sudo** record: tests exercising access rights must use
  `env["res.users"].browse(uid)` or other models, never `env.user.write`.
* Web client: Owl 3 (`props = useProps({...})`, `this.` in templates),
  `@web/core/user` holds the user context sent with every RPC.
* View icons are Material Symbols names (`icon="local_shipping"`), lists are
  `<list>`, visibility uses `invisible="expr"`.

## The branch framework (core module `branch_management`)

### Security mode C

* `res.users.allowed_branch_ids` = **security boundary**.
* `res.users.current_branch_id` = **working context** (defaults, filters).
  It comes from the `current_branch_id` context key set by the systray
  selector (cookie `branch_id`), and is **re-validated server side** by
  `res.users._get_current_branch(company)`: a branch the user may not use is
  ignored (falls back to the default branch, then the first allowed branch).
* Branch administrators (`branch_management.group_branch_admin`, implied by
  Settings administrators) and external users (portal/public, governed by
  their own rules) are *unrestricted*: `user.branch_unrestricted`.

### Making a model branch-aware

1. Inherit the mixin:

   ```python
   class SaleOrder(models.Model):
       _name = "sale.order"
       _inherit = ["sale.order", "res.branch.mixin"]
   ```

   The mixin gives `branch_id` (default = current branch of the record's
   company, `check_company=True`, `ondelete='restrict'`, indexed),
   `is_current_branch` (searchable, for "Current Branch" filters) and a
   validation of `branch_id`:
   * in `create`/`write`, before saving: the branch is allowed for the user
     (skipped for `sudo()` and unrestricted users). It is not an
     `@api.constrains` because Odoo 20 runs constraints as superuser;
   * constraint: branch company == record company (`_branch_company()` can be
     overridden).

   Redefine `branch_id` in the model to add `tracking=True`, `readonly`
   rules, `compute=...` (e.g. derived from a warehouse), etc.

   For a model with `company_id`, add:

   ```python
   @api.onchange("company_id")
   def _onchange_company_id_branch(self):
       self._branch_sync_with_company()
   ```

2. Declare the security **restriction** (group-less `ir.access` row) so the
   boundary applies to ORM, RPC, URL and UI alike:

   ```csv
   sale_order_branch_rule,Sales Order: allowed branches,sale.order,,crud,"[] if user.branch_unrestricted else ['|', ('branch_id', '=', False), ('branch_id', 'in', user.allowed_branch_ids.ids)]"
   ```

   Documents without a branch stay visible to everybody allowed by the
   other rules. Child models (order lines, move lines) use a stored related
   `branch_id` and the same restriction, or `('order_id', 'access', 'read')`
   style conditions where Odoo already does so.

3. Views: add `branch_id` to form (`groups` not needed), list
   (`optional="show"`), search (field + `Current Branch` filter
   `[('is_current_branch', '=', True)]` + group by branch) and pivot/graph
   reports where there is a `*.report` SQL view (add the column in
   `_select`/`_group_by`).

4. Propagation: override the Odoo 20 hook that builds the next document's
   values (`_prepare_invoice`, `_prepare_picking`, procurement values, ...)
   and pass `branch_id`. Never let the branch silently change along a flow.

5. Reports: inherit the QWeb report and call

   ```xml
   <t t-call="branch_management.branch_address_block" branch="doc.branch_id"/>
   ```

   (In Odoo 20 a `t-set` inside the `t-call` body is *not* passed to the
   called template: pass values as attributes of the `t-call` element.)

6. Smart button on the branch form: inherit
   `branch_management.view_res_branch_form`, add a button in
   `//div[@name='button_box']`, backed by a method using
   `self._get_records_action(name, res_model, domain)`.

7. Numbering: `branch._get_next_sequence_number(doc_code, "SO")` returns
   `AHM/SO/00001`; only use it when `company.branch_sequence_enabled`.

### sudo() policy

Every `sudo()` must carry a comment explaining why it cannot leak data across
branches. Never use it to search/read business documents on behalf of a user.

### Tests

* Tag with `@tagged("post_install", "-at_install", "branch_management")`.
* Never rely on demo data. Reuse `odoo.addons.branch_management.tests.common.BranchTestCommon`
  (two companies, branches HO/GUJ/AHM/SRT in company A, MUM/PUN in company B,
  users `user_a` (AHM), `user_b` (SRT), `user_multi`, `user_none`, `manager`,
  `branch_admin`, and `env_for(user, company=..., branch=..., companies=...)`),
  adding the application groups your tests need to the users.
* Test security through a non-sudo env: search, read, write, unlink, and
  direct `browse(id).read()` of another branch's record (must raise
  `AccessError`).
