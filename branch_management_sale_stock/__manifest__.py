{
    "name": "Multi Branch Management - Sales & Inventory",
    "version": "20.0.1.0.0",
    "category": "Sales/Sales",
    "summary": "Sales orders ship from their branch's warehouse; deliveries keep the order's branch",
    "description": """
Bridge between branch-aware Sales and Inventory
===============================================

* the warehouse of a quotation is the default warehouse of its branch
  (recomputed when the branch changes on a quotation);
* an order cannot ship from a warehouse of another branch;
* procurements carry the order's branch: deliveries, stock moves and
  returns belong to the branch of the sales order (TC-013);
* Deliveries smart button on the branch form.
""",
    "author": "Branch Management Contributors",
    "website": "https://github.com/Adityashah1409/branch",
    "license": "LGPL-3",
    "depends": ["branch_management_sale", "branch_management_stock", "sale_stock"],
    "data": [
        "views/res_branch_views.xml",
    ],
    "installable": True,
    "auto_install": True,
}
