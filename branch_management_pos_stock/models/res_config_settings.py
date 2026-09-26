from odoo import api, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    @api.onchange("pos_branch_id")
    def _onchange_pos_branch_id_picking_type(self):
        if not self.pos_branch_id or self.pos_picking_type_id.branch_id == self.pos_branch_id:
            return
        picking_type = self.env["pos.config"]._get_branch_pos_picking_type(self.pos_branch_id)
        if picking_type:
            self.pos_picking_type_id = picking_type
