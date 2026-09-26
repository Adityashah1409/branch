{
    "name": "Multi Branch Management - Sales",
    "version": "20.0.1.0.0",
    "category": "Sales/Sales",
    "summary": "Branch on quotations and sales orders, propagated to invoices",
    "description": """
Branch-aware sales
==================

* branch on quotations / sales orders (default: current branch, tracked)
  and on order lines
* invoices and down payment invoices created from an order keep its branch
* optional branch-specific order numbering (e.g. AHM/SO/00001)
* branch security on orders, order lines and sales analysis
* branch block on the quotation / order PDF, Sales smart button on branches
""",
    "author": "Branch Management Contributors",
    "website": "https://github.com/Adityashah1409/branch",
    "license": "LGPL-3",
    "depends": ["branch_management_account", "sale"],
    "data": [
        "security/ir.access.csv",
        "views/sale_order_views.xml",
        "views/res_branch_views.xml",
        "report/sale_report_views.xml",
        "report/sale_report_templates.xml",
    ],
    "installable": True,
    "auto_install": False,
}
