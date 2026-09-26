from odoo import fields, models
from odoo.models import TableSQL


class SaleReport(models.Model):
    _inherit = "sale.report"

    branch_id = fields.Many2one("res.branch", string="Branch", readonly=True)

    def _select_dict(self, table: TableSQL):
        res = super()._select_dict(table)
        # functionally dependent on the order, which is part of the GROUP BY
        res["branch_id"] = table.order_id.branch_id
        return res
