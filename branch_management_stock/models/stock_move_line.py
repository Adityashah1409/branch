from odoo import api, fields, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    # Reporting only: move lines follow their move / transfer.
    branch_id = fields.Many2one(
        "res.branch",
        string="Branch",
        compute="_compute_branch_id",
        store=True,
        index="btree_not_null",
    )

    @api.depends("move_id.branch_id", "picking_id.branch_id", "location_id", "location_dest_id")
    def _compute_branch_id(self):
        for line in self:
            line.branch_id = (
                line.move_id.branch_id
                or line.picking_id.branch_id
                or line.location_id.branch_id
                or line.location_dest_id.branch_id
            )
