# Multi Branch Management - Purchase

Branch integration of the Odoo 20 Purchase application.

* **RFQs / purchase orders** carry a branch (default: the user's current
  branch in the order's company, tracked); order lines store it for
  reporting. The branch must belong to the order's company and be allowed
  for the user.
* **Vendor bills** created from orders (*Create Bill*, or the purchase
  auto-complete on a bill) are in the order's branch (`_prepare_invoice`);
  orders of different branches are billed separately. When the branch has a
  dedicated purchase journal, the bill uses it.
* **Numbering**: when *Branch Sequence Prefix* is enabled on the company,
  orders of a branch are numbered `<branch prefix>/PO/00001`.
* **Security**: group-less `ir.access` restrictions on `purchase.order`,
  `purchase.order.line` and `purchase.report`.
* **Reports**: branch in *Purchase Analysis* (group by Branch), branch block
  on the RFQ and purchase order PDFs.
* **Views**: branch on the order form and lists, *Current Branch* filter and
  *Branch* group-by; *Purchases* smart button on the branch form.

Receipts are handled by the stock integration, not by this module.
