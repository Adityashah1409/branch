from odoo import api, models

from .pos_session import POS_BRANCH_CONTEXT_KEY


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    @api.model_create_multi
    def create(self, vals_list):
        # cash moves of PoS sessions (pos.payment.method._create_cash_payment_line):
        # ``branch_id`` is a field of the statement line's journal entry
        # (_inherits), so it is written on the entry
        for vals in vals_list:
            if "branch_id" in vals:
                continue
            if vals.get("pos_session_id"):
                # sudo: only reads the branch of the session the cash move is
                # created for (by a sudo PoS flow)
                vals["branch_id"] = self.env["pos.session"].sudo().browse(vals["pos_session_id"]).branch_id.id
            elif POS_BRANCH_CONTEXT_KEY in self.env.context:
                vals["branch_id"] = self.env.context[POS_BRANCH_CONTEXT_KEY]
        return super().create(vals_list)
