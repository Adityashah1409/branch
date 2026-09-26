# Multi Branch Management for Odoo 20

An original, LGPL-3 implementation of a multi-branch (multi-unit) layer for
**Odoo 20.0**. It lets one company run several branches, each with its own
users, documents, security, numbering and printed documents.

```text
Company A                     Company B
 ├── Head Office               ├── Mumbai
 │    └── Gujarat              └── Pune
 │         ├── Ahmedabad
 │         └── Surat
```

A branch is **not** a company. It always belongs to exactly one company, so
it adds a finer dimension and security boundary inside that company. It
works alongside Odoo's multi-company rules.

## Modules

| Module | Depends on | What it adds |
| --- | --- | --- |
| `branch_management` | base, web, base_setup | Branch master and hierarchy, allowed/default/current branch per user, security groups, systray branch selector, `res.branch.mixin`, branch sequences, user assignment wizard, PDF branch block |
| `branch_management_account` | core, account | Branch on journal entries, journal items, payments and journals; branch journals for per-branch invoice numbering; payment register keeps the branch; branch in Invoice Analysis and on invoice and payment PDFs |
| `branch_management_sale` | account integration, sale | Branch on quotations, orders, lines and Sales Analysis; SO → invoice (and down payments) keep the branch; `AHM/SO/00001` numbering; branch on the quotation/order PDF |
| `branch_management_purchase` | account integration, purchase | Branch on RFQs, orders, lines and Purchase Analysis; PO → vendor bill keeps the branch; `AHM/PO/00001` numbering; branch on the RFQ/PO PDF |
| `branch_management_stock` | core, stock | Branch → warehouse → operation types, locations, transfers, moves and quants; explicit cross-branch transfer control; branch on the delivery slip and picking PDFs |
| `branch_management_sale_stock` *(auto)* | sale + stock integrations | The order's warehouse comes from its branch; deliveries keep the order's branch |
| `branch_management_purchase_stock` *(auto)* | purchase + stock integrations | The receipt's operation type comes from the branch; receipts keep the order's branch |
| `branch_management_mrp` | stock integration, mrp | Branch on manufacturing and unbuild orders and their moves |
| `branch_management_pos` | account integration, point_of_sale | Branch on shops, sessions, orders, POS invoices and closing entries |
| `branch_management_pos_stock` *(auto)* | POS + stock integrations | POS pickings use the shop's branch warehouse and keep the branch |
| `branch_management_crm` | core, crm | Branch on leads/opportunities, sales teams dedicated to a branch, activity analysis |
| `branch_management_hr` | core, hr | Branch on employees and departments; the public directory is unaffected |
| `branch_management_project` | core, project | Branch on projects and tasks, task analysis |
| `branch_management_partner` | core | Informative branches on contacts, a "My Branches" filter, optional default |

Every module has its own `README.md` covering its design choices and
limitations. Helpdesk is an Odoo Enterprise app, so there is no
`branch_management_helpdesk` in this community repository.

## Documentation

* [INSTALL.md](INSTALL.md): installation and upgrade
* [CONFIGURATION.md](CONFIGURATION.md): setting up branches, users and numbering
* [SECURITY.md](SECURITY.md): the security model and how it was verified
* [DEVELOPMENT.md](DEVELOPMENT.md): Odoo 20 notes and how to make a model branch-aware
* [CHANGELOG.md](CHANGELOG.md)

## Tests

Every module ships Odoo tests that do not use demo data. They cover the
mandatory cases TC-001 to TC-025, including a real-browser tour of the
branch selector. CI (`.github/workflows/tests.yml`) installs all modules on
Odoo 20.0 and PostgreSQL 16 and runs them. To run them locally:

```bash
tools/run_tests.sh /path/to/odoo-20.0 branch_test python3
```

## License

LGPL-3. This is an independent implementation. It contains no code, assets or
branding from third-party branch modules.
