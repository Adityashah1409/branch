from odoo import fields, models
from odoo.models import TableSQL
from odoo.tools import SQL


class PurchaseReport(models.Model):
    _inherit = "purchase.report"

    branch_id = fields.Many2one("res.branch", string="Branch", readonly=True)

    def _select_list(self, table: TableSQL):
        # functionally dependent on the order, which is part of the GROUP BY
        return [
            *super()._select_list(table),
            SQL("%s AS branch_id", table.order_id.branch_id),
        ]
