# Configuration

## 1. Create branches

*Settings → Users & Companies → Branches* (or *Settings → General Settings →
Branches → Manage Branches*).

| Field | Notes |
| --- | --- |
| Name, Code | The code is unique **per company** (`AHM` may exist in two companies) and is stored in upper case. |
| Company | A branch belongs to exactly one company. It can't be moved once documents use it. |
| Parent Branch | Unlimited hierarchy, displayed as `Head Office / Gujarat / Ahmedabad`. |
| Manager, address, phone, mobile, email, website, logo | Printed on the branch's documents. |
| Sequence Prefix | Prefix for branch numbering. Defaults to the code. |
| Default Warehouse *(stock)* | Warehouse used by the branch's sales and purchases. |

Archive a branch instead of deleting it. A branch used by any document can't
be deleted, and its history stays readable.

## 2. Give users access

* On the user: *Access Rights → Branches* sets **Allowed Branches** (the
  security boundary) and the **Default Branch**.
* On the branch: the *Users* tab, or the **Assign Users** button (bulk
  grant or revoke, with an option to set the default branch).
* Access level under *Access Rights → Branches*:
  * **User** (every internal user): works in their allowed branches.
  * **Manager**: creates branches, edits and staffs the branches they are
    allowed in.
  * **Administrator**: the full configuration, and sees every branch.
    Settings administrators get it automatically.

## 3. Working branch

The top-bar branch selector lists the active branches the user is allowed in
for the active company. Picking one sets the **current branch** for that
browser session. New documents default to it, and the **Current Branch**
filter uses it. The choice is not saved in the database: after logging in
again, the last branch picked in that browser is used, or the default branch
otherwise. Switching company only offers the new company's branches.

## 4. Optional features

| Setting | Where | Effect |
| --- | --- | --- |
| Branch Sequence Prefix | Settings → Branches | Sales and purchase orders numbered `AHM/SO/00001`, `AHM/PO/00001` per branch |
| Branch journals | Accounting → Journals → *Branch* | Invoices and bills of the branch use this journal, so they get the journal's own numbering (e.g. `AHM/2026/00001` with journal code `AHM`) |
| Allow cross-branch transfers | Settings → Branches *(stock)* | Allows internal transfers between warehouses of different branches. They are flagged as *Cross-branch*. |
| Default contact branch | Settings → Branches *(partner)* | Contacts created from the form get the current branch |

## 5. Reporting

Every branch-aware list, pivot and graph view has a **Branch** group-by and
a **Current Branch** filter, including Sales, Purchase, Invoice, Inventory,
CRM, Task and POS analyses. Printed quotations, orders, RFQs, POs,
invoices, bills, payment receipts, delivery slips, receipts and
manufacturing orders show the branch's name, logo, address and contact
details.
