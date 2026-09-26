from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    branch_ids = fields.One2many("res.branch", "company_id", string="Business Branches")
    branch_sequence_enabled = fields.Boolean(
        string="Branch Sequence Prefix",
        help="Number sales and purchase documents with a branch-specific sequence "
        "(e.g. AHM/SO/00001). Accounting documents keep Odoo's journal-based "
        "numbering: use one journal per branch to get branch-specific invoice numbers.",
    )
