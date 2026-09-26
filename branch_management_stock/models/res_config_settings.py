from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    branch_allow_cross_transfer = fields.Boolean(
        related="company_id.branch_allow_cross_transfer",
        readonly=False,
    )
