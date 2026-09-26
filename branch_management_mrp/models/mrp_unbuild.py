from odoo import api, fields, models
from odoo.exceptions import ValidationError


class MrpUnbuild(models.Model):
    _name = "mrp.unbuild"
    _inherit = ["mrp.unbuild", "res.branch.mixin"]

    # mrp.unbuild has no operation type: the branch comes from the unbuilt
    # manufacturing order, else from the warehouse of the source location.
    branch_id = fields.Many2one(
        compute="_compute_branch_id",
        store=True,
        readonly=False,
        precompute=True,
        compute_sudo=False,  # the fallback on the working branch needs the real user
        default=None,
        copy=False,
        tracking=True,
    )

    @api.depends("mo_id", "location_id")
    def _compute_branch_id(self):
        for unbuild in self:
            branch = unbuild.mo_id.branch_id or unbuild.location_id.branch_id
            if branch:
                unbuild.branch_id = branch
            elif not unbuild.branch_id and not self.env.su and unbuild.company_id:
                unbuild.branch_id = self.env.user._get_current_branch(unbuild.company_id)

    @api.constrains("branch_id", "location_id")
    def _check_location_branch(self):
        for unbuild in self:
            location_branch = unbuild.location_id.branch_id
            if unbuild.branch_id and location_branch and unbuild.branch_id != location_branch:
                raise ValidationError(self.env._(
                    "The branch %(branch)s of unbuild order %(unbuild)s does not match the "
                    "branch %(location_branch)s of its source location %(location)s.",
                    branch=unbuild.branch_id.display_name,
                    unbuild=unbuild.display_name,
                    location_branch=location_branch.display_name,
                    location=unbuild.location_id.display_name,
                ))
