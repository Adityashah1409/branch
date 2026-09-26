from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    branch_allow_cross_transfer = fields.Boolean(
        string="Cross-Branch Transfers",
        help="Allow validating transfers whose source and destination locations "
        "belong to different branches. Such transfers are flagged as cross-branch.",
    )
