# Multi Branch Management - Accounting

Branch integration of the Odoo 20 accounting (`account`) application.

* **Journal entries, invoices and bills** carry a branch (default: the
  user's current branch, tracked). The branch must belong to the document's
  company and be allowed for the user. Journal items store the branch of
  their entry for reporting and grouping.
* **Journals** can be dedicated to a branch. New invoices/bills of a branch
  that has a dedicated sale/purchase journal use it: this gives
  branch-specific invoice numbering through Odoo's own journal sequences
  (move names are never rewritten). A document can't use a journal
  dedicated to another branch.
* **Payments** carry a branch. The *Register Payment* wizard creates the
  payment in the branch of the paid invoices (invoices of different branches
  are never grouped into one payment) and prefers the branch's dedicated
  bank journal. The journal entry of a payment follows its branch.
  Bank statement lines inherit the branch of their journal entry
  (`_inherits`), no extra field is added.
* **Security**: group-less `ir.access` restrictions on `account.move`,
  `account.move.line`, `account.payment` and `account.invoice.report`
  (documents without branch stay visible). Branch administrators are not
  restricted.
* **Reports**: branch column in *Invoice Analysis* (group by Branch), branch
  block on the invoice and payment receipt PDFs.
* **Branch form**: Invoices, Bills and Payments smart buttons.

Run the tests:

```bash
./venv/bin/python odoo/odoo-bin -d test_db --addons-path=odoo/addons,<repo> \
    -i branch_management_account --test-tags /branch_management_account \
    --stop-after-init
```
