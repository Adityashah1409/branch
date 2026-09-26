{
    "name": "Multi Branch Management - Inventory",
    "version": "20.0.1.0.0",
    "category": "Inventory/Inventory",
    "summary": "Branch-aware warehouses, transfers, stock moves and cross-branch transfer control",
    "description": """
Branch integration for Inventory
================================

* Branch -> Warehouse -> operations: warehouses belong to a branch, operation
  types, locations, transfers, stock moves, move lines and quants inherit it;
* default warehouse of a branch (``res.branch._get_default_warehouse()``);
* transfers restricted to the user's allowed branches;
* cross-branch internal transfers blocked unless enabled in the settings;
* branch block on delivery slips and picking operations.
""",
    "author": "Branch Management Contributors",
    "website": "https://github.com/Adityashah1409/branch",
    "license": "LGPL-3",
    "depends": ["branch_management", "stock"],
    "data": [
        "security/ir.access.csv",
        "views/res_branch_views.xml",
        "views/res_config_settings_views.xml",
        "views/stock_warehouse_views.xml",
        "views/stock_picking_type_views.xml",
        "views/stock_location_views.xml",
        "views/stock_picking_views.xml",
        "views/stock_move_views.xml",
        "views/stock_quant_views.xml",
        "report/stock_report_templates.xml",
    ],
    "installable": True,
    "auto_install": False,
}
