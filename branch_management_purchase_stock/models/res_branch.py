from odoo import api, fields, models

PURCHASE_RECEIPT_DOMAIN = [("picking_type_code", "=", "incoming"), ("purchase_id", "!=", False)]


class ResBranch(models.Model):
    _inherit = "res.branch"

    purchase_receipt_count = fields.Integer(
        compute="_compute_purchase_receipt_count", string="# Receipts",
        groups="stock.group_stock_user",
    )

    @api.depends_context("uid", "allowed_company_ids")
    def _compute_purchase_receipt_count(self):
        # counted with the user's access rights
        counts = dict(self.env["stock.picking"]._read_group(
            [("branch_id", "in", self.ids), *PURCHASE_RECEIPT_DOMAIN], ["branch_id"], ["__count"],
        ))
        for branch in self:
            branch.purchase_receipt_count = counts.get(branch, 0)

    def action_view_purchase_receipts(self):
        self.ensure_one()
        return self._get_records_action(
            self.env._("Receipts"), "stock.picking", domain=PURCHASE_RECEIPT_DOMAIN,
            context={"create": False},
        )
