from odoo import api, models

from .pos_session import POS_BRANCH_CONTEXT_KEY


class AccountPayment(models.Model):
    _inherit = "account.payment"

    @api.model_create_multi
    def create(self, vals_list):
        # bank payments of PoS orders / sessions (pos.payment.method._create_bank_payment_line)
        for vals in vals_list:
            if "branch_id" in vals:
                continue
            if vals.get("pos_session_id"):
                # sudo: only reads the branch of the session the payment is
                # created for (by a sudo PoS flow)
                vals["branch_id"] = self.env["pos.session"].sudo().browse(vals["pos_session_id"]).branch_id.id
            elif POS_BRANCH_CONTEXT_KEY in self.env.context:
                vals["branch_id"] = self.env.context[POS_BRANCH_CONTEXT_KEY]
        return super().create(vals_list)
