from odoo import fields, models
from odoo.tools import SQL


class CrmActivityReport(models.Model):
    _inherit = "crm.activity.report"

    branch_id = fields.Many2one("res.branch", string="Branch", readonly=True)

    def _select(self):
        return SQL("%s, l.branch_id AS branch_id", super()._select())
