# Installation

## Requirements

* Odoo **20.0** (Community or Enterprise), Python 3.12+, PostgreSQL 14+.
* No extra Python package.

## Install

1. Put this repository in your addons path:

   ```ini
   [options]
   addons_path = /opt/odoo/odoo/addons,/opt/odoo/addons,/opt/odoo/custom/branch
   ```

2. Restart Odoo, enable developer mode, then go to *Apps → Update Apps List*.
3. Install **Multi Branch Management** (`branch_management`), then the
   integrations you need (`branch_management_sale`, `_purchase`, `_stock`,
   `_account`, ...). The bridges `branch_management_sale_stock`,
   `_purchase_stock` and `_pos_stock` install automatically when both
   sides are present.

From the command line:

```bash
odoo-bin -d mydb -i branch_management_sale,branch_management_purchase,branch_management_stock --stop-after-init
```

## Upgrade

```bash
odoo-bin -d mydb -u branch_management --stop-after-init   # plus any integration module
```

The modules follow the `20.0.x.y.z` versioning. Upgrades within 20.0 keep
data. Existing documents keep an empty branch after installation, which
means visible to everyone. Stamp them in bulk from list views if needed
(select the records, then *Actions → Edit* the Branch column).

## Uninstall

Uninstall the integration modules first, then `branch_management`. The
branch columns, groups, access rules and the per-branch sequences created on
demand are removed. Business documents themselves are not touched.

## Troubleshooting

| Symptom | Cause / fix |
| --- | --- |
| A user suddenly can't see some orders | Those orders belong to a branch the user is not allowed in. Add the branch on the user (*Access Rights → Branches*) or grant *Branches: Administrator*. |
| "You are not allowed to use branch X" | The branch picked on the document is not in the user's allowed branches. |
| The branch selector is missing from the top bar | The user has no branch in the active company. |
| Invoice numbers are not per branch | Create one sales journal per branch and set its *Branch* (Accounting → Configuration → Journals). |
| Validating an internal transfer fails with "cross-branch" | Enable *Allow cross-branch transfers* in Settings → Branches, or transfer within one branch. |
