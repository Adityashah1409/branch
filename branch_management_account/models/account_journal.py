from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    branch_id = fields.Many2one(
        "res.branch",
        string="Branch",
        index="btree_not_null",
        ondelete="restrict",
        check_company=True,
        tracking=True,
        help="Dedicate this journal to a branch: only documents of this branch can use it, "
        "and new invoices/bills of the branch use it by default. Leave empty for a "
        "journal shared by all branches. A dedicated sale or purchase journal (with "
        "its own short code) gives the branch its own invoice numbering.",
    )
