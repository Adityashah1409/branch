from odoo import fields, models


class PosPayment(models.Model):
    _inherit = "pos.payment"

    branch_id = fields.Many2one(
        "res.branch",
        string="Branch",
        related="pos_order_id.branch_id",
        store=True,
        precompute=True,
        index="btree_not_null",
    )
