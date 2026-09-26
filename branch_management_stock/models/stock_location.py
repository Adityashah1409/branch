from odoo import fields, models


class StockLocation(models.Model):
    _inherit = "stock.location"

    # stock.location.warehouse_id is a stored compute (stock_location.py),
    # derived from the warehouse view location in parent_path.
    branch_id = fields.Many2one(
        "res.branch",
        related="warehouse_id.branch_id",
        store=True,
        index="btree_not_null",
        string="Branch",
    )
