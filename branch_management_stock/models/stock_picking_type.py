from odoo import fields, models


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    branch_id = fields.Many2one(
        "res.branch",
        related="warehouse_id.branch_id",
        store=True,
        index="btree_not_null",
        string="Branch",
    )
