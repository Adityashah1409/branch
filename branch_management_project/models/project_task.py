from odoo import fields, models


class ProjectTask(models.Model):
    _name = "project.task"
    _inherit = ["project.task", "res.branch.mixin"]

    # A task always belongs to the branch of its project; private tasks and
    # tasks without project have no branch and stay visible to everybody
    # allowed by the other access rules.
    branch_id = fields.Many2one(
        related="project_id.branch_id",
        store=True,
        readonly=True,
        default=None,
        check_company=False,
    )
