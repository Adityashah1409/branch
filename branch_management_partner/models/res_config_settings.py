from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    branch_partner_default = fields.Boolean(
        related="company_id.branch_partner_default",
        readonly=False,
    )
