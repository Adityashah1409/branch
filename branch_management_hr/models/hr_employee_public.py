from odoo import api, fields, models
from odoo.fields import Domain


class HrEmployeePublic(models.Model):
    _inherit = "hr.employee.public"

    # stored column of the SQL view (hr.employee.public._get_fields() selects
    # every stored field from hr_employee)
    branch_id = fields.Many2one("res.branch", string="Branch", readonly=True)
    is_current_branch = fields.Boolean(
        string="In Current Branch",
        compute="_compute_is_current_branch",
        search="_search_is_current_branch",
    )

    @api.depends("branch_id")
    @api.depends_context("current_branch_id", "allowed_company_ids", "uid")
    def _compute_is_current_branch(self):
        current = self.env.user._get_current_branch()
        for employee in self:
            employee.is_current_branch = employee.branch_id == current

    def _search_is_current_branch(self, operator, value):
        if operator not in ("in", "not in"):
            return NotImplemented
        domain = Domain("branch_id", "=", self.env.user._get_current_branch().id or False)
        positive = (operator == "in") == (True in value)
        return domain if positive else ~domain
