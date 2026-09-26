{
    "name": "Multi Branch Management - Purchase & Inventory",
    "version": "20.0.1.0.0",
    "category": "Supply Chain/Purchase",
    "summary": "Purchase orders receive in their branch's warehouse; receipts keep the order's branch",
    "description": """
Bridge between branch-aware Purchase and Inventory
==================================================

* the operation type (Deliver To) of an RFQ is the receipt type of its
  branch's default warehouse, and follows the branch when it changes;
* an order cannot receive in a warehouse of another branch;
* receipts and their stock moves belong to the branch of the purchase order
  (TC-015); vendor bills created after reception keep it;
* replenishment (buy rule) creates purchase orders in the branch of the
  warehouse to resupply;
* Receipts smart button on the branch form.
""",
    "author": "Branch Management Contributors",
    "website": "https://github.com/Adityashah1409/branch",
    "license": "LGPL-3",
    "depends": ["branch_management_purchase", "branch_management_stock", "purchase_stock"],
    "data": [
        "views/res_branch_views.xml",
    ],
    "installable": True,
    "auto_install": True,
}
