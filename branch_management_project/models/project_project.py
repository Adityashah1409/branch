from odoo import api, fields, models


class ProjectProject(models.Model):
    _name = "project.project"
    _inherit = ["project.project", "res.branch.mixin"]

    branch_id = fields.Many2one(
        tracking=True,
        # Projects may have no company ("visible to all"): the generic
        # company domain would then offer no branch at all. The mixin
        # constraint still enforces branch company == project company
        # whenever a company is set.
        check_company=False,
        domain="company_id and [('company_id', '=', company_id)] or []",
    )

    @api.onchange("company_id")
    def _onchange_company_id_branch(self):
        self._branch_sync_with_company()
