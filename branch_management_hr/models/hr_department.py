from odoo import api, fields, models
from odoo.exceptions import ValidationError


class HrDepartment(models.Model):
    _inherit = "hr.department"

    branch_id = fields.Many2one(
        "res.branch",
        string="Branch",
        index="btree_not_null",
        ondelete="restrict",
        tracking=True,
        # departments may have no company ("visible to all"): see the constraint
        domain="company_id and [('company_id', '=', company_id)] or []",
        help="Branch this department belongs to. New employees of the "
        "department are proposed this branch.",
    )

    @api.onchange("company_id")
    def _onchange_company_id_branch(self):
        for department in self:
            if department.branch_id and department.company_id != department.branch_id.company_id:
                department.branch_id = False

    @api.constrains("branch_id", "company_id")
    def _check_branch_company(self):
        for department in self:
            if department.branch_id and department.company_id != department.branch_id.company_id:
                raise ValidationError(self.env._(
                    "Department %(department)s belongs to branch %(branch)s: it must "
                    "belong to the company of that branch (%(company)s).",
                    department=department.display_name,
                    branch=department.branch_id.display_name,
                    company=department.branch_id.company_id.name,
                ))
