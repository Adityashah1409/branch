from odoo import api, fields, models


class ResBranch(models.Model):
    _inherit = "res.branch"

    purchase_order_count = fields.Integer(
        compute="_compute_purchase_order_count", groups="purchase.group_purchase_user",
    )

    @api.depends_context("uid", "allowed_company_ids")
    def _compute_purchase_order_count(self):
        # counted with the user's access rights
        counts = dict(self.env["purchase.order"]._read_group(
            [("branch_id", "in", self.ids)], ["branch_id"], ["__count"],
        ))
        for branch in self:
            branch.purchase_order_count = counts.get(branch, 0)

    def action_view_purchase_orders(self):
        return self._get_branch_document_action("purchase.purchase_rfq")
