from odoo import api, fields, models


class BranchUserAssign(models.TransientModel):
    """Grant or revoke access to several branches for several users at once."""

    _name = "branch.user.assign"
    _description = "Assign Users to Branches"

    branch_ids = fields.Many2many(
        "res.branch",
        string="Branches",
        required=True,
        default=lambda self: self._default_branch_ids(),
    )
    user_ids = fields.Many2many(
        "res.users",
        string="Users",
        required=True,
        domain="[('share', '=', False)]",
    )
    mode = fields.Selection(
        [("add", "Grant access"), ("remove", "Revoke access")],
        default="add",
        required=True,
    )
    set_default = fields.Boolean(
        string="Set as Default Branch",
        help="Also make the (first) branch the default branch of the users.",
    )

    @api.model
    def _default_branch_ids(self):
        if self.env.context.get("active_model") == "res.branch":
            return self.env.context.get("active_ids", [])
        return []

    def action_apply(self):
        """Apply through res.branch.user_ids, so that the operation is
        authorized by the access rights on branches (a branch manager can
        only manage the branches they are allowed to write)."""
        self.ensure_one()
        command = fields.Command.link if self.mode == "add" else fields.Command.unlink
        for branch in self.branch_ids:
            branch.write({"user_ids": [command(user.id) for user in self.user_ids]})
        if self.mode == "add" and self.set_default:
            # default branch is a preference of the user: written as sudo once
            # the access was granted above through the checked branch write
            self.user_ids.sudo().write({"default_branch_id": self.branch_ids[:1].id})
        return {"type": "ir.actions.act_window_close"}
