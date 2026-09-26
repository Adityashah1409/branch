from odoo import api, fields, models
from odoo.exceptions import ValidationError


class CrmTeam(models.Model):
    _inherit = "crm.team"

    branch_id = fields.Many2one(
        "res.branch",
        string="Branch",
        index="btree_not_null",
        ondelete="restrict",
        tracking=True,
        # not check_company: a team without company ("visible to all") gets
        # the company of its branch through the onchange below, and the
        # constraint gives an explicit message instead of the generic one.
        domain="company_id and [('company_id', '=', company_id)] or []",
        help="Branch this team is dedicated to. Leads assigned to the team "
        "are filed in this branch.",
    )

    @api.onchange("branch_id")
    def _onchange_branch_id(self):
        for team in self:
            if team.branch_id and not team.company_id:
                team.company_id = team.branch_id.company_id

    @api.onchange("company_id")
    def _onchange_company_id_branch(self):
        for team in self:
            if team.branch_id and team.company_id != team.branch_id.company_id:
                team.branch_id = False

    @api.constrains("branch_id", "company_id")
    def _check_branch_company(self):
        for team in self:
            if team.branch_id and team.company_id != team.branch_id.company_id:
                raise ValidationError(self.env._(
                    "Sales team %(team)s is dedicated to branch %(branch)s: it must "
                    "belong to the company of that branch (%(company)s).",
                    team=team.display_name,
                    branch=team.branch_id.display_name,
                    company=team.branch_id.company_id.name,
                ))
