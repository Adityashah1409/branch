from odoo import fields, models
from odoo.models import TableSQL
from odoo.tools import SQL


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    branch_id = fields.Many2one("res.branch", string="Branch", readonly=True)

    def _select_list(self, table: TableSQL):
        return [
            *super()._select_list(table),
            SQL("%s AS branch_id", table.branch_id),
        ]
