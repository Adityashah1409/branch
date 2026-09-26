from odoo import fields, models


class StockQuant(models.Model):
    _inherit = "stock.quant"

    # Reporting only (inventory analysis grouped by branch). No security
    # restriction is declared on quants: reservation must see every quant.
    branch_id = fields.Many2one(
        "res.branch",
        related="location_id.branch_id",
        store=True,
        index="btree_not_null",
        string="Branch",
    )
