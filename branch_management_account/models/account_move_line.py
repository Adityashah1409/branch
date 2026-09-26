from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    # Stored so that journal items can be filtered, grouped and secured by
    # branch (ledgers, pivot views, invoice analysis) without a join.
    #
    # Security choice: journal items get the same branch restriction as their
    # journal entry (security/ir.access.csv). All the lines of a move share
    # its branch, so reading a move you may access never hits a forbidden
    # line. Reconciliation keeps working because Odoo reads the counterpart
    # of reconciled items in sudo (payment widgets, partials, exchange
    # difference entries); the outstanding credits proposed on an invoice are
    # limited to the branches of the user, which is the expected boundary.
    # Items without branch (entries created before installation or by flows
    # without a branch) stay visible to everybody allowed by the other rules.
    branch_id = fields.Many2one(
        related="move_id.branch_id",
        store=True,
        precompute=True,
        index="btree_not_null",
    )
