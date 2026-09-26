from odoo import models


class PosSession(models.Model):
    _inherit = "pos.session"

    def _create_picking_at_end_of_session(self):
        # pickings of the whole session ("update stock at closing")
        return super(PosSession, self._with_pos_branch_context())._create_picking_at_end_of_session()
