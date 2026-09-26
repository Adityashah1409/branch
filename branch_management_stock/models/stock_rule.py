from odoo import models


class StockRule(models.Model):
    _inherit = "stock.rule"

    def _get_stock_move_values(self, product_id, product_qty, uom_id, location_dest_id, name, origin, company_id, values):
        """Carry the branch of the procurement to the stock move.

        The branch of the rule's operation type (i.e. of its warehouse) wins
        (Branch -> Warehouse -> operations); the ``branch_id`` procurement
        value (record or id, set by bridge modules in their procurement
        values) is used when the operation type has no branch.
        """
        move_values = super()._get_stock_move_values(
            product_id, product_qty, uom_id, location_dest_id, name, origin, company_id, values
        )
        branch = self.picking_type_id.branch_id
        if not branch and values.get("branch_id"):
            branch = self.env["res.branch"].browse(
                values["branch_id"].id if isinstance(values["branch_id"], models.BaseModel)
                else values["branch_id"]
            )
        if branch:
            move_values["branch_id"] = branch.id
        return move_values

    def _push_prepare_move_copy_values(self, move_to_copy):
        new_move_vals = super()._push_prepare_move_copy_values(move_to_copy)
        branch = self.picking_type_id.branch_id or move_to_copy.branch_id
        if branch:
            new_move_vals["branch_id"] = branch.id
        return new_move_vals
