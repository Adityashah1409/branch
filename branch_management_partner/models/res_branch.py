from odoo import fields, models


class ResBranch(models.Model):
    _inherit = "res.branch"

    partner_count = fields.Integer(compute="_compute_partner_count", string="Contacts")

    def _compute_partner_count(self):
        counts = dict(self.env["res.partner"]._read_group(
            [("branch_ids", "in", self.ids)], ["branch_ids"], ["__count"],
        ))
        for branch in self:
            branch.partner_count = counts.get(branch, 0)

    def action_view_partners(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Contacts"),
            "res_model": "res.partner",
            "view_mode": "kanban,list,form",
            "domain": [("branch_ids", "in", self.ids)],
            "context": {"default_branch_ids": self.ids},
        }
