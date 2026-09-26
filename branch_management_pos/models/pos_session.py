from odoo import api, fields, models

# Context key set while a session creates its accounting records: entries
# without a PoS link in their values (e.g. bank differences) get the branch.
POS_BRANCH_CONTEXT_KEY = "branch_management_pos_branch_id"


class PosSession(models.Model):
    _name = "pos.session"
    _inherit = ["pos.session", "res.branch.mixin"]

    branch_id = fields.Many2one(
        compute="_compute_branch_id",
        store=True,
        precompute=True,
        readonly=True,
        default=None,
        help="Branch of the shop when the session was opened.",
    )

    @api.depends("config_id")
    def _compute_branch_id(self):
        # only depends on the shop (not on its branch): moving a shop to
        # another branch later does not rewrite the history
        for session in self:
            session.branch_id = session.config_id.branch_id

    def _with_pos_branch_context(self):
        self.ensure_one()
        return self.with_context(**{POS_BRANCH_CONTEXT_KEY: self.branch_id.id or False})

    # ------------------------------------------------------------------
    # Accounting (session closing)
    # ------------------------------------------------------------------

    def _prepare_session_move_vals(self, orders):
        vals = super()._prepare_session_move_vals(orders)
        vals["branch_id"] = self.branch_id.id
        return vals

    def _validate_session_accounting(self):
        return super(PosSession, self._with_pos_branch_context())._validate_session_accounting()

    def _handle_bank_payment_method_difference(self, payment_method_closing={}):  # noqa: B006 (Odoo signature)
        return super(PosSession, self._with_pos_branch_context())._handle_bank_payment_method_difference(
            payment_method_closing
        )

    def _handle_cash_statement_entries(self, payment_method_closing={}):  # noqa: B006 (Odoo signature)
        return super(PosSession, self._with_pos_branch_context())._handle_cash_statement_entries(
            payment_method_closing
        )
