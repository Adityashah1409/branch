# Test report

All modules are tested together on a fresh Odoo 20.0 database (PostgreSQL 16,
no demo data) with `tools/run_tests.sh`, locally and in GitHub Actions.

Latest local run with all 14 modules installed together:
`0 failed, 0 error(s) of 183 tests`. This includes the real-browser tour
of the branch selector.

## Mandatory test cases

| Case | Test | Module |
| --- | --- | --- |
| TC-001 Create branch | `test_tc001_create_branch` | branch_management |
| TC-002 Duplicate code, same company, fails | `test_tc002_duplicate_code_same_company` | branch_management |
| TC-003 Same code, other company, allowed | `test_tc003_same_code_other_company` | branch_management |
| TC-004 Assign branch to user | `test_tc004_assign_branch_to_user` | branch_management |
| TC-005 User cannot use an unauthorized branch | `test_tc005_order_unauthorized_branch_rejected` | branch_management_sale |
| TC-006 Manager manages permitted branches | `test_tc006_manager_manages_permitted_branches` | branch_management |
| TC-007 Current/default branch within allowed | `test_tc007_default_branch_must_be_allowed` | branch_management |
| TC-008 Switching updates the working context | `test_tc008_switch_updates_working_context` + browser tour | branch_management |
| TC-009 Company switch invalidates branch | `test_tc009_switching_company_invalidates_branch` | branch_management |
| TC-010 Archived current branch handled | `test_tc010_archived_current_branch` | branch_management |
| TC-011 SO defaults to current branch | `test_tc011_order_defaults_to_current_branch` | branch_management_sale |
| TC-012 Cannot read another branch's SO | `test_tc012_user_cannot_access_other_branch_orders` | branch_management_sale |
| TC-013 Sale → Delivery keeps branch | `test_tc013_*` | branch_management_sale_stock |
| TC-014 Sale → Invoice keeps branch | `test_tc014_*` | branch_management_sale |
| TC-015 Purchase → Receipt keeps branch | `test_tc015_*` | branch_management_purchase_stock |
| TC-016 Purchase → Bill keeps branch | `test_tc016_*` | branch_management_purchase |
| TC-017 Transfer validates branch | `test_tc017_*` | branch_management_stock |
| TC-018 Cross-branch transfer | `TestStockCrossBranch` (`test_cross_branch_*`) | branch_management_stock |
| TC-019 Invoice branch/company mismatch rejected | `test_tc019_*` | branch_management_account |
| TC-020 Multi-company isolation | `test_tc020_branch_isolation_between_companies` | branch_management |
| TC-021 Direct RPC access blocked | `test_tc021_*` | branch_management_account (plus read/write/unlink checks in every restricted module) |
| TC-022 Archive keeps history readable | `test_tc022_archived_branch_keeps_orders_readable` | branch_management_sale (also purchase) |
| TC-023 Selector shows only valid branches | `test_tc023_selector_displays_valid_branches` + browser tour | branch_management |
| TC-024 User with zero branches | `test_tc024_user_without_branch` | branch_management |
| TC-025 Superuser behaviour | `test_tc025_superuser_behavior` | branch_management |

## Final quality gate

| Check | Result |
| --- | --- |
| Installs on a clean Odoo 20 database | Yes, all 14 modules together |
| Upgrades (`-u` all modules) | Yes, no errors or warnings |
| Uninstalls safely | Yes. All modules removed; branch columns, tables and groups dropped; sales orders still readable |
| No Python traceback, XML or asset errors | None in the install and test logs |
| No OWL/JavaScript errors | The browser tour fails on any console error, and it passed |
| No branch security bypass | Search, read, write and unlink tested through non-sudo environments in every restricted module |
| Multi-company, switching, sales, purchase, inventory, accounting, POS | Covered by the tests above |
| Reports and PDFs | Every module with a PDF asserts the branch block is in its QWeb template. The delivery slip, invoice, sales order and purchase order HTML output are rendered and checked. PDF binary rendering needs wkhtmltopdf, which was not installed in the test environment. |
| Translations | `.pot` for every module; complete fr, es, hi, gu and ar translations of the core |
| Performance | The security uses indexed `branch_id IN (...)` SQL domains. Access domains are cached by Odoo and flushed only when users' branches or groups change. There is no `search()` override. Not load-tested at production volume. |

## Also verified

Odoo's own stock, mrp, crm, hr, project and sales_team suites were run with
these modules installed. They gave the same results as a database without
them: the few failures there also fail on a plain Odoo 20.0 database and are
unrelated to branches.
