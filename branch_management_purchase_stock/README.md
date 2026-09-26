# Multi Branch Management - Purchase & Inventory (`branch_management_purchase_stock`)

Bridge between `branch_management_purchase` and `branch_management_stock` for
Odoo 20 (depends on `purchase_stock`, installed automatically).

## Purchase -> Receipt keeps the branch (TC-015)

| Step | Hook (Odoo 20) | Behaviour |
|---|---|---|
| Default *Deliver To* | `purchase.order._get_picking_type` (used by the field default and the company onchange) | receipt type (`in_type_id`) of the default warehouse of the working branch (or of `default_branch_id` in the context), else of a warehouse shared by the company, else Odoo's choice |
| Create | `purchase.order.create` | explicit `branch_id` without operation type: the branch's receipt type; operation type without `branch_id`: the type's branch (replenishment, `default_picking_type_id`) |
| Branch change | `@api.onchange("branch_id")` | receipts of another branch (or shared receipts when the branch has its own warehouse) are replaced by the branch's receipt type; a dropship type is kept |
| Stock moves | `purchase.order.line._prepare_stock_move_vals` | adds `branch_id` (order's branch); the operation type's branch still wins (branch_management_stock) |
| Replenishment | `stock.rule._prepare_purchase_order`, `stock.rule._make_po_get_domain` | RFQs are created in the branch of the warehouse to resupply (else the `branch_id` procurement value, e.g. dropship) and never grouped across branches |
| Bill | `purchase.order._prepare_invoice` (branch_management_purchase) | bills after reception keep the order's branch |

## Validation

`purchase.order._check_picking_type_branch`: the operation type's warehouse must
belong to the order's branch (or to no branch).

## Views

*Receipts* smart button on the branch form (incoming transfers of purchase orders).

## Limitations

* Changing the branch of a confirmed order is refused when its operation type
  belongs to another branch; existing receipts are never moved.
