# Multi Branch Management - Point of Sale & Inventory (`branch_management_pos_stock`)

Bridge between `branch_management_pos` and `branch_management_stock` for Odoo 20.
In Odoo 20 the pickings of the Point of Sale are created by `pos_stock`
(`stock.picking._create_picking_from_pos_order_lines`), installed automatically
with this bridge.

## PoS pickings keep the shop's branch

| Step | Hook (Odoo 20) | Behaviour |
|---|---|---|
| Operation type of the shop | `pos.config.create`, `@api.onchange("branch_id")` (and on `pos_branch_id` in the PoS settings) | the PoS operation type (`pos_type_id`) of the branch's default warehouse, else of a warehouse shared by the company |
| Real-time pickings | `pos.order._create_order_picking` | a picking of a branch-owned warehouse belongs to its operation type's branch (branch_management_stock); with a shared warehouse, `stock.picking._prepare_picking_vals` gives it the shop's branch |
| Pickings at session closing | `pos.session._create_picking_at_end_of_session` | same |
| Ship later (procurements) | `pos.order.line._prepare_procurement_values` | adds `branch_id` (used by `stock.rule._get_stock_move_values`) |

## Validation

`pos.config._check_picking_type_branch`: the shop's operation type must belong
to its branch's warehouse (or to a warehouse without branch).

## Limitations

* Stock valuation entries of PoS pickings are not handled here (no
  `stock_account` branch bridge).
