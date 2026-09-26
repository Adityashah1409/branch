from odoo import fields, models
from odoo.tools import SQL


class ReportPosOrder(models.Model):
    _inherit = "report.pos.order"

    branch_id = fields.Many2one("res.branch", string="Branch", readonly=True)

    def _select(self):
        # report.pos.order has no GROUP BY (one row per order line)
        return SQL("%s, s.branch_id AS branch_id", super()._select())
