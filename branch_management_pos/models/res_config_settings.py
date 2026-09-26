from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # "pos_" fields are written to the selected pos.config (point_of_sale)
    pos_branch_id = fields.Many2one(related="pos_config_id.branch_id", readonly=False)
