from odoo import fields, models


class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    branch_id = fields.Many2one(
        "res.branch",
        string="Branch",
        related="order_id.branch_id",
        store=True,
        precompute=True,
        index="btree_not_null",
    )
