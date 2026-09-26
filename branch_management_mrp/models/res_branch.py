from odoo import fields, models


class ResBranch(models.Model):
    _inherit = "res.branch"

    production_count = fields.Integer(
        compute="_compute_production_count", string="# Manufacturing Orders")

    def _compute_production_count(self):
        # counted with the user's access rights: only visible orders
        counts = dict(self.env["mrp.production"]._read_group(
            [("branch_id", "in", self.ids)], ["branch_id"], ["__count"]))
        for branch in self:
            branch.production_count = counts.get(branch, 0)

    def action_view_productions(self):
        self.ensure_one()
        return self._get_records_action(self.env._("Manufacturing Orders"), "mrp.production")
