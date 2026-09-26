from odoo import models


class ResGroups(models.Model):
    _inherit = "res.groups"

    def _get_light_group_xmlids(self):
        # Every internal user is a branch user (implied by base.group_user):
        # it must not turn light users into regular users.
        return (
            *super()._get_light_group_xmlids(),
            "branch_management.group_branch_user",
        )
