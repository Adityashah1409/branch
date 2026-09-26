from odoo import api, fields, models


class ResBranch(models.Model):
    _inherit = "res.branch"

    pos_order_count = fields.Integer(
        compute="_compute_pos_order_count", string="# PoS Orders",
        groups="point_of_sale.group_pos_user",
    )

    @api.depends_context("uid", "allowed_company_ids")
    def _compute_pos_order_count(self):
        # counted with the user's access rights
        counts = dict(self.env["pos.order"]._read_group(
            [("branch_id", "in", self.ids)], ["branch_id"], ["__count"],
        ))
        for branch in self:
            branch.pos_order_count = counts.get(branch, 0)

    def action_view_pos_orders(self):
        return self._get_branch_document_action("point_of_sale.action_pos_pos_form")
