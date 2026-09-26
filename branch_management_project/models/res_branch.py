from odoo import fields, models


class ResBranch(models.Model):
    _inherit = "res.branch"

    # restricted to project users: computing it reads project.project records
    project_count = fields.Integer(
        compute="_compute_project_count",
        string="Projects",
        groups="project.group_project_user",
    )

    def _compute_project_count(self):
        # counted with the user's access rights: only visible projects count
        counts = dict(self.env["project.project"]._read_group(
            [("branch_id", "in", self.ids)], ["branch_id"], ["__count"],
        ))
        for branch in self:
            branch.project_count = counts.get(branch, 0)

    def action_view_projects(self):
        self.ensure_one()
        action = self._get_records_action(self.env._("Projects"), "project.project")
        action["view_mode"] = "kanban,list,form"
        return action
