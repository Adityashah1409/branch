{
    "name": "Multi Branch Management - Purchase",
    "version": "20.0.1.0.0",
    "category": "Supply Chain/Purchase",
    "summary": "Branch on requests for quotation and purchase orders, propagated to vendor bills",
    "description": """
Branch-aware purchases
======================

* branch on RFQs / purchase orders (default: current branch, tracked) and
  on order lines
* vendor bills created from an order keep its branch
* optional branch-specific order numbering (e.g. AHM/PO/00001)
* branch security on orders, order lines and purchase analysis
* branch block on the RFQ / purchase order PDFs, Purchases smart button on branches
""",
    "author": "Branch Management Contributors",
    "website": "https://github.com/Adityashah1409/branch",
    "license": "LGPL-3",
    "depends": ["branch_management_account", "purchase"],
    "data": [
        "security/ir.access.csv",
        "views/purchase_order_views.xml",
        "views/res_branch_views.xml",
        "report/purchase_report_views.xml",
        "report/purchase_report_templates.xml",
    ],
    "installable": True,
    "auto_install": False,
}
