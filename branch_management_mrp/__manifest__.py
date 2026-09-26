{
    "name": "Multi Branch Management - Manufacturing",
    "version": "20.0.1.0.0",
    "category": "Supply Chain/Manufacturing",
    "summary": "Branch-aware manufacturing and unbuild orders",
    "description": """
Branch integration for Manufacturing
====================================

* manufacturing orders belong to the branch of their operation type's
  warehouse; unbuild orders to the branch of their location / MO;
* component and finished product moves carry the branch;
* orders restricted to the user's allowed branches;
* branch filters, grouping, smart button on the branch and branch block on
  the production order report.
""",
    "author": "Branch Management Contributors",
    "website": "https://github.com/Adityashah1409/branch",
    "license": "LGPL-3",
    "depends": ["branch_management_stock", "mrp"],
    "data": [
        "security/ir.access.csv",
        "views/res_branch_views.xml",
        "views/mrp_production_views.xml",
        "views/mrp_unbuild_views.xml",
        "report/mrp_report_templates.xml",
    ],
    "installable": True,
    "auto_install": False,
}
