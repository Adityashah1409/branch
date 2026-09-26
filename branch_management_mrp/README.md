# Multi Branch Management - Manufacturing (`branch_management_mrp`)

Depends on `branch_management_stock` and `mrp`.

* `mrp.production.branch_id` (mixin, stored compute, editable): branch of the
  operation type's warehouse (`picking_type_id.warehouse_id.branch_id`), else
  the explicit value / working branch. Must match the operation type's branch.
* `mrp.unbuild.branch_id`: branch of the unbuilt MO, else of the source location.
* Component, finished and by-product moves carry the order's branch
  (`_get_move_raw_values`, `_get_move_finished_values`, and the
  `stock.move._get_branch_from_origin` extension), and so do their move lines.
* Procurement-generated MOs: `stock.rule._prepare_mo_vals` sets the branch
  (operation type's branch, else `branch_id` procurement value) and
  `_make_mo_get_domain` never merges the needs of different branches.
* Security: group-less restriction rows on `mrp.production` and `mrp.unbuild`.
* Views: branch on MO / unbuild form, list and search (Current Branch filter,
  group by Branch); "Manufacturing Orders" smart button on the branch form.
* Report: branch address block on the production order PDF.
