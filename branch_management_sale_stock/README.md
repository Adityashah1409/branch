# Multi Branch Management - Sales & Inventory (`branch_management_sale_stock`)

Bridge between `branch_management_sale` and `branch_management_stock` for Odoo 20
(depends on `sale_stock`, installed automatically).

## Sale -> Delivery keeps the branch (TC-013)

| Step | Hook (Odoo 20) | Behaviour |
|---|---|---|
| Warehouse of the order | `sale.order._compute_warehouse_id` (sale_stock) + `@api.depends("branch_id")` | quotations ship from `branch._get_default_warehouse()`; when the branch has no warehouse and Odoo proposed a warehouse of another branch, a warehouse shared by the company (no branch) is used; otherwise Odoo's proposal is kept. Recomputed when the branch of a quotation changes. |
| Procurement | `sale.order.line._prepare_procurement_values` | adds `branch_id` (the order's branch); used by `stock.rule._get_stock_move_values` (branch_management_stock) when the rule's operation type has no branch |
| Delivery / moves | branch_management_stock | the delivery and its moves belong to the branch of the warehouse's operation type, else to the order's branch |
| Returns | `stock.picking.copy_data` (branch_management_stock) | returns keep the delivery's branch |
| Invoice | `sale.order._prepare_invoice` (branch_management_sale) | invoices after delivery keep the order's branch |

## Validation

`sale.order._check_warehouse_branch`: an order whose warehouse belongs to another
branch is refused (`ValidationError`); warehouses without branch are accepted.
A confirmed order cannot be moved to a branch other than its warehouse's.

## Views

*Deliveries* smart button on the branch form (outgoing transfers of sales
orders, counted with the user's access rights).

## Limitations

* Confirmed orders keep their warehouse (as in Odoo): change the branch of a
  quotation, not of a confirmed order.
* Order lines whose route forces another warehouse (`sale.order.line.warehouse_id`)
  follow Odoo's route logic; the resulting transfers belong to that
  warehouse's branch.
