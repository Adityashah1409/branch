from odoo import fields, models
from odoo.tools import SQL


class ReportProjectTaskUser(models.Model):
    _inherit = "report.project.task.user"

    branch_id = fields.Many2one("res.branch", string="Branch", readonly=True)

    def _select(self):
        return SQL("%s, t.branch_id", super()._select())

    def _group_by(self):
        return SQL("%s, t.branch_id", super()._group_by())
