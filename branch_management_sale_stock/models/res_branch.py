from odoo import api, fields, models

SALE_DELIVERY_DOMAIN = [("picking_type_code", "=", "outgoing"), ("sale_id", "!=", False)]


class ResBranch(models.Model):
    _inherit = "res.branch"

    sale_delivery_count = fields.Integer(
        compute="_compute_sale_delivery_count", string="# Deliveries",
        groups="stock.group_stock_user",
    )

    @api.depends_context("uid", "allowed_company_ids")
    def _compute_sale_delivery_count(self):
        # counted with the user's access rights
        counts = dict(self.env["stock.picking"]._read_group(
            [("branch_id", "in", self.ids), *SALE_DELIVERY_DOMAIN], ["branch_id"], ["__count"],
        ))
        for branch in self:
            branch.sale_delivery_count = counts.get(branch, 0)

    def action_view_sale_deliveries(self):
        self.ensure_one()
        return self._get_records_action(
            self.env._("Deliveries"), "stock.picking", domain=SALE_DELIVERY_DOMAIN,
            context={"create": False},
        )
