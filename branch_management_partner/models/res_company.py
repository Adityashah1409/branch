from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    branch_partner_default = fields.Boolean(
        string="Default Contact Branch",
        help="Contacts created from a contact form are linked to the working "
        "branch of the user who creates them.",
    )
