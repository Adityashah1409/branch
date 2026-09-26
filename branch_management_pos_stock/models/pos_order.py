from odoo import models

from odoo.addons.branch_management_pos.models.pos_session import POS_BRANCH_CONTEXT_KEY


class PosOrder(models.Model):
    _inherit = "pos.order"

    def _create_order_picking(self):
        # real-time pickings (stock.picking._prepare_picking_vals reads it)
        return super(PosOrder, self.with_context(**{POS_BRANCH_CONTEXT_KEY: self.branch_id.id or False}))._create_order_picking()
