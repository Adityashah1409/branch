from odoo import fields, models


class ResBranch(models.Model):
    _inherit = "res.branch"

    # restricted to HR officers: computing it reads hr.employee records
    employee_count = fields.Integer(
        compute="_compute_employee_count",
        string="Employees",
        groups="hr.group_hr_user",
    )

    def _compute_employee_count(self):
        # counted with the user's access rights: only visible employees count
        counts = dict(self.env["hr.employee"]._read_group(
            [("branch_id", "in", self.ids)], ["branch_id"], ["__count"],
        ))
        for branch in self:
            branch.employee_count = counts.get(branch, 0)

    def action_view_employees(self):
        self.ensure_one()
        action = self._get_records_action(self.env._("Employees"), "hr.employee")
        action["view_mode"] = "kanban,list,form"
        return action
