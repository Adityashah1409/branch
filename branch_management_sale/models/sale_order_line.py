from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    branch_id = fields.Many2one(
        related="order_id.branch_id",
        store=True,
        precompute=True,
        index="btree_not_null",
    )
