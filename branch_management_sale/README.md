# Multi Branch Management - Sales

Branch integration of the Odoo 20 Sales application.

* **Quotations / sales orders** carry a branch (default: the user's current
  branch in the order's company, tracked); order lines store it for
  reporting. The branch must belong to the order's company and be allowed
  for the user.
* **Invoicing**: invoices created from orders (`_create_invoices`, the
  *Create Invoice* wizard, down payments) are created in the order's branch
  (`_prepare_invoice`), never in the user's current branch; orders of
  different branches are never merged into one invoice. When the branch has
  a dedicated sale journal, the invoice uses it.
* **Numbering**: when *Branch Sequence Prefix* is enabled on the company,
  orders of a branch are numbered `<branch prefix>/SO/00001`.
* **Security**: group-less `ir.access` restrictions on `sale.order`,
  `sale.order.line` and `sale.report`.
* **Reports**: branch in *Sales Analysis* (group by Branch), branch block on
  the quotation / order PDF.
* **Views**: branch on the order form and list, *Current Branch* filter and
  *Branch* group-by; *Sales* smart button on the branch form.
