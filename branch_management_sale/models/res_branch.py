from odoo import api, fields, models


class ResBranch(models.Model):
    _inherit = "res.branch"

    sale_order_count = fields.Integer(
        compute="_compute_sale_order_count", groups="sales_team.group_sale_salesman",
    )

    @api.depends_context("uid", "allowed_company_ids")
    def _compute_sale_order_count(self):
        # counted with the user's access rights
        counts = dict(self.env["sale.order"]._read_group(
            [("branch_id", "in", self.ids)], ["branch_id"], ["__count"],
        ))
        for branch in self:
            branch.sale_order_count = counts.get(branch, 0)

    def action_view_sale_orders(self):
        return self._get_branch_document_action("sale.action_orders")
