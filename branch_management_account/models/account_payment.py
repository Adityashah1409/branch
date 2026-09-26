from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AccountPayment(models.Model):
    _name = "account.payment"
    _inherit = ["account.payment", "res.branch.mixin"]

    branch_id = fields.Many2one(tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        without_branch = [i for i, vals in enumerate(vals_list) if "branch_id" not in vals]
        payments = super().create(vals_list)
        # A payment created for invoices (e.g. by a payment flow that does not
        # know about branches) belongs to the branch of these invoices rather
        # than to the user's working branch.
        for index in without_branch:
            payment = payments[index]
            invoice_branch = payment.invoice_ids.branch_id
            if len(invoice_branch) == 1 and invoice_branch != payment.branch_id:
                payment.branch_id = invoice_branch
        return payments

    def write(self, vals):
        res = super().write(vals)
        if "branch_id" in vals:
            # keep the journal entry of the payment in the payment's branch
            for payment in self.filtered("move_id"):
                if payment.move_id.branch_id != payment.branch_id:
                    payment.move_id.branch_id = payment.branch_id
        return res

    def _generate_move_vals(self, write_off_line_vals=None, force_balance=None, line_ids=None):
        vals = super()._generate_move_vals(
            write_off_line_vals=write_off_line_vals, force_balance=force_balance, line_ids=line_ids,
        )
        vals["branch_id"] = self.branch_id.id
        return vals

    @api.onchange("company_id")
    def _onchange_company_id_branch(self):
        self._branch_sync_with_company()

    # ------------------------------------------------------------------
    # Journal selection
    # ------------------------------------------------------------------

    @api.depends("branch_id")
    def _compute_journal_id(self):
        super()._compute_journal_id()
        Journal = self.env["account.journal"]
        for payment in self:
            journal_branch = payment.journal_id.branch_id
            if payment.state != "draft" or not journal_branch or journal_branch == payment.branch_id:
                continue
            company = payment.company_id or self.env.company
            payment.journal_id = Journal.search([
                *Journal._check_company_domain(company),
                ("type", "in", ("bank", "cash", "credit")),
                ("branch_id", "in", [False, payment.branch_id.id]),
            ], limit=1) or payment.journal_id

    @api.depends("branch_id")
    def _compute_available_journal_ids(self):
        super()._compute_available_journal_ids()
        for payment in self:
            payment.available_journal_ids = payment.available_journal_ids.filtered(
                lambda journal: not journal.branch_id or journal.branch_id == payment.branch_id
            )

    @api.constrains("journal_id", "branch_id", "company_id")
    def _check_journal_branch(self):
        self._check_branch_company_match()
        for payment in self:
            journal_branch = payment.journal_id.branch_id
            if journal_branch and journal_branch != payment.branch_id:
                raise ValidationError(self.env._(
                    "Journal %(journal)s is dedicated to branch %(journal_branch)s: "
                    "it cannot be used by payment %(payment)s (branch: %(branch)s).",
                    journal=payment.journal_id.display_name,
                    journal_branch=journal_branch.display_name,
                    payment=payment.display_name,
                    branch=payment.branch_id.display_name or self.env._("none"),
                ))
