from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    branch_sequence_enabled = fields.Boolean(
        related="company_id.branch_sequence_enabled",
        readonly=False,
    )
