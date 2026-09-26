{
    "name": "Multi Branch Management - Point of Sale",
    "version": "20.0.1.0.0",
    "category": "Sales/Point of Sale",
    "summary": "Branch on shops (PoS configurations), sessions, orders, payments and their accounting",
    "description": """
Branch-aware Point of Sale
==========================

* each shop (``pos.config``) belongs to a branch; its sessions, orders,
  order lines and payments inherit it (read-only, kept when the shop later
  moves to another branch);
* invoices of PoS orders, session closing entries, bank payments, cash
  statement lines and cash differences are created in the shop's branch;
* branch security on shops, sessions, orders, order lines, payments and the
  PoS order analysis (shops without branch stay visible);
* branch filters / group by, Point of Sale Orders smart button on branches.
""",
    "author": "Branch Management Contributors",
    "website": "https://github.com/Adityashah1409/branch",
    "license": "LGPL-3",
    "depends": ["branch_management_account", "point_of_sale"],
    "data": [
        "security/ir.access.csv",
        "views/pos_config_views.xml",
        "views/pos_session_views.xml",
        "views/pos_order_views.xml",
        "views/pos_payment_views.xml",
        "views/res_config_settings_views.xml",
        "views/res_branch_views.xml",
        "report/pos_order_report_views.xml",
    ],
    "installable": True,
    "auto_install": False,
}
