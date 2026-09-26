from odoo import models

from odoo.addons.branch_management_pos.models.pos_session import POS_BRANCH_CONTEXT_KEY


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _prepare_picking_vals(self, partner, picking_type, location_id, location_dest_id):
        vals = super()._prepare_picking_vals(partner, picking_type, location_id, location_dest_id)
        # the branch of the operation type's warehouse wins (branch_management_stock);
        # for a shared warehouse, the picking belongs to the shop's branch
        branch_id = self.env.context.get(POS_BRANCH_CONTEXT_KEY)
        if branch_id and not picking_type.branch_id:
            vals["branch_id"] = branch_id
        return vals
