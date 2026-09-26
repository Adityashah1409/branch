from odoo import fields, models


class ResBranch(models.Model):
    _inherit = "res.branch"

    # restricted to salesmen: computing it reads crm.lead records
    crm_lead_count = fields.Integer(
        compute="_compute_crm_lead_count",
        string="Leads/Opportunities",
        groups="sales_team.group_sale_salesman",
    )

    def _compute_crm_lead_count(self):
        # counted with the user's access rights: only visible leads are counted
        counts = dict(self.env["crm.lead"]._read_group(
            [("branch_id", "in", self.ids)], ["branch_id"], ["__count"],
        ))
        for branch in self:
            branch.crm_lead_count = counts.get(branch, 0)

    def action_view_crm_leads(self):
        self.ensure_one()
        action = self._get_records_action(
            self.env._("Leads/Opportunities"), "crm.lead",
        )
        action["view_mode"] = "list,kanban,form"
        return action
