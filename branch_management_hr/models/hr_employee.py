from odoo import api, fields, models


class HrEmployee(models.Model):
    _name = "hr.employee"
    _inherit = ["hr.employee", "res.branch.mixin"]

    # Both fields also exist on hr.employee.public (see hr_employee_public.py):
    # users without HR rights read employees through that model, and hr
    # requires fields without `groups` to be available there.
    branch_id = fields.Many2one(tracking=True)

    @api.onchange("company_id")
    def _onchange_company_id_branch(self):
        self._branch_sync_with_company()

    @api.onchange("department_id")
    def _onchange_department_id_branch(self):
        for employee in self:
            branch = employee.department_id.branch_id
            if branch and branch.company_id == employee.company_id:
                employee.branch_id = branch
