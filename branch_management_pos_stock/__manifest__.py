{
    "name": "Multi Branch Management - Point of Sale & Inventory",
    "version": "20.0.1.0.0",
    "category": "Sales/Point of Sale",
    "summary": "Shops deliver from their branch's warehouse; PoS pickings keep the shop's branch",
    "description": """
Bridge between branch-aware Point of Sale and Inventory
=======================================================

* the operation type of a shop is the PoS operation type of its branch's
  default warehouse (and follows the branch when it changes);
* a shop cannot use the operation type of another branch's warehouse;
* PoS pickings (real time, at session closing, ship later) and their stock
  moves belong to the shop's branch.
""",
    "author": "Branch Management Contributors",
    "website": "https://github.com/Adityashah1409/branch",
    "license": "LGPL-3",
    "depends": ["branch_management_pos", "branch_management_stock", "pos_stock"],
    "data": [],
    "installable": True,
    "auto_install": True,
}
