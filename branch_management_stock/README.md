# Multi Branch Management - Inventory (`branch_management_stock`)

Branch integration for Odoo 20 Inventory. Depends on `branch_management` and `stock`.

## Business rule: Branch -> Warehouse -> operations

| Model | `branch_id` | How |
|---|---|---|
| `stock.warehouse` | `res.branch.mixin` | chosen on the warehouse (same company, allowed branch) |
| `stock.picking.type` | stored related | `warehouse_id.branch_id` |
| `stock.location` | stored related | `warehouse_id.branch_id` (`warehouse_id` is a stored compute in Odoo) |
| `stock.picking` | mixin, stored compute, editable | operation type's branch; else the explicit value (procurement / bridge) or the working branch |
| `stock.move` | stored compute, editable | transfer, else operation type, else source / destination location |
| `stock.move.line` | stored compute | move, else transfer, else location |
| `stock.quant` | stored related | `location_id.branch_id` (reporting / grouping only) |

`stock.picking` also has `dest_branch_id` (branch of the destination
location) and `is_cross_branch`. The branch of a transfer only depends on its
operation type (not on the operation type's branch): moving a warehouse to
another branch never rewrites history, and is refused while the warehouse has
ongoing transfers.

A branch may own several warehouses. `res.branch.default_warehouse_id`
(Configuration tab of the branch) chooses the one used by default;
`res.branch._get_default_warehouse(company_fallback=False)` is the helper other
modules must use.

## Validations

* transfer branch must equal the branch of its operation type (TC-017);
* the branch must belong to the document's company and be allowed for the user (mixin);
* cross-branch transfers (source and destination locations in different
  branches) are refused at validation (`button_validate` and `_action_done`)
  unless *Settings > Branches > Cross-Branch Transfers*
  (`res.company.branch_allow_cross_transfer`) is enabled (TC-018).

## Security (`security/ir.access.csv`)

Group-less restriction rows on `stock.picking` and `stock.move`: documents
without branch, of an allowed branch, or whose destination is an allowed branch
(the receiving branch of a cross-branch transfer must see it).

Deliberately **not** restricted: `stock.quant`, `stock.location`,
`stock.warehouse`, `stock.picking.type`, `stock.move.line`. Reservation, putaway,
availability and replenishment read quants, locations and operation types of
the whole company as the current user; restricting them would silently break
reservations and stock levels. They are configuration / stock-level data and
remain protected by Odoo's multi-company rules.

## Propagation hooks (for sale / purchase / mrp bridges)

* `stock.rule._get_stock_move_values`: the rule's operation type branch wins,
  else the `branch_id` procurement value (record or id);
* `stock.rule._push_prepare_move_copy_values`: pushed moves keep the branch;
* `stock.move._get_new_picking_values`, `_key_assign_picking`,
  `_search_picking_for_assignation_domain`: new transfers get the moves' branch
  and moves of different branches are never grouped in the same transfer;
* `stock.move._prepare_merge_moves_distinct_fields`, `_prepare_move_split_vals`.

A bridge only has to (1) pick the warehouse with
`branch._get_default_warehouse()` and (2) put `branch_id` in the procurement
values (sale) or in the stock move values (purchase).

## Reports

Branch address block on the delivery slip and on the picking operations
report (destination branch printed for cross-branch transfers).

## Limitations

* Chained moves spanning two branches (e.g. inter-warehouse resupply through
  a transit location) touch the moves of both branches: they must be processed
  by a user allowed in both branches (or a branch administrator).
* Product forecasts computed as a restricted user only include the moves the
  user can read.
* No branch column in the `report.stock.quantity` SQL view (no clean hook);
  use the stock move analysis / quants grouped by branch.
