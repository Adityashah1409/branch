{
    "name": "Multi Branch Management - Accounting",
    "version": "20.0.1.0.0",
    "category": "Accounting/Accounting",
    "summary": "Branch on invoices, bills, journal entries, payments and journals",
    "description": """
Branch-aware accounting
=======================

* branch on journal entries, invoices and bills (default: current branch),
  stored on journal items for reporting and grouping
* branch on payments, taken from the paid invoices by the Register Payment wizard
* optional branch on journals: branch-dedicated sale/purchase journals give
  branch-specific invoice numbering
* branch security on journal entries, journal items, payments and invoice analysis
* branch block on the invoice and payment receipt PDFs
* Invoices / Bills / Payments smart buttons on the branch form
""",
    "author": "Branch Management Contributors",
    "website": "https://github.com/Adityashah1409/branch",
    "license": "LGPL-3",
    "depends": ["branch_management", "account"],
    "data": [
        "security/ir.access.csv",
        "views/account_journal_views.xml",
        "views/account_move_views.xml",
        "views/account_payment_views.xml",
        "views/res_branch_views.xml",
        "report/account_invoice_report_views.xml",
        "report/report_templates.xml",
    ],
    "installable": True,
    "auto_install": False,
}
