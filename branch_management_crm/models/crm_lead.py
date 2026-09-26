from odoo import api, fields, models


class CrmLead(models.Model):
    _name = "crm.lead"
    _inherit = ["crm.lead", "res.branch.mixin"]

    branch_id = fields.Many2one(
        tracking=True,
        compute="_compute_branch_id",
        store=True,
        readonly=False,
        precompute=True,
        # the default (current branch) is applied by the compute method, so
        # that the branch of a dedicated sales team can win over it
        default=None,
        # Leads may have no company ("visible to all"): the generic company
        # check would then reject every branch. The mixin constraint still
        # enforces branch company == lead company whenever a company is set.
        check_company=False,
        domain="company_id and [('company_id', '=', company_id)] or []",
    )

    @api.depends("team_id")
    def _compute_branch_id(self):
        """Branch of the lead.

        Priority: the branch the sales team is dedicated to, then the branch
        already set (if consistent with the company), then the user's current
        branch for new leads (or when the company changed).
        Explicit values given at creation are never overridden, and existing
        leads without branch are left untouched.

        ``company_id`` is not a declared dependency: it is not precomputed on
        crm.lead, which would prevent the precomputation of the branch at
        creation. Company changes are handled by the onchange below.
        """
        for lead in self:
            company = lead.company_id
            team_branch = lead.team_id.branch_id
            if team_branch and (not company or team_branch.company_id == company):
                lead.branch_id = team_branch
            elif lead.branch_id and (not company or lead.branch_id.company_id == company):
                lead.branch_id = lead.branch_id
            elif lead.branch_id or not lead._origin:
                lead.branch_id = lead.env.user._get_current_branch(
                    company or lead._branch_default_company()
                )
            else:
                lead.branch_id = False

    @api.onchange("company_id")
    def _onchange_company_id_branch(self):
        self._branch_sync_with_company()

    def _merge_get_fields(self):
        # the merged opportunity keeps the branch of the first lead having one
        return super()._merge_get_fields() + ["branch_id"]
