from odoo import api, models


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    @api.model
    def _get_line_batch_key(self, line):
        # Lines of different branches never end up in the same payment: the
        # branch is part of the grouping key of the batches.
        key = super()._get_line_batch_key(line)
        key["branch_id"] = line.move_id.branch_id.id
        return key

    @api.model
    def _get_batch_branch(self, batch_result):
        branch_id = batch_result["payment_values"].get("branch_id")
        if branch_id:
            return self.env["res.branch"].browse(branch_id)
        branches = batch_result["lines"].move_id.branch_id
        return branches if len(branches) == 1 else self.env["res.branch"]

    @api.model
    def _get_batch_available_journals(self, batch_result):
        journals = super()._get_batch_available_journals(batch_result)
        branches = batch_result["lines"].move_id.branch_id
        return journals.filtered(lambda journal: not journal.branch_id or journal.branch_id in branches)

    @api.model
    def _get_batch_journal(self, batch_result):
        journal = super()._get_batch_journal(batch_result)
        branch = self._get_batch_branch(batch_result)
        if branch and journal.branch_id != branch:
            dedicated = self.available_journal_ids._origin.filtered(
                lambda j: j.branch_id == branch and j.company_id == journal.company_id
            )
            if dedicated:
                currency_id = batch_result["payment_values"]["currency_id"]
                return (dedicated.filtered(lambda j: j.currency_id.id == currency_id) or dedicated)[:1]
        return journal

    @api.depends("available_journal_ids")
    def _compute_journal_id(self):
        super()._compute_journal_id()
        for wizard in self:
            # e.g. the preferred payment method of the partner points to a
            # journal dedicated to another branch
            if wizard.journal_id.branch_id and wizard.journal_id not in wizard.available_journal_ids:
                batches = wizard._get_batches()
                wizard.journal_id = wizard._get_batch_journal(batches[0]) if batches else False

    def _create_payment_vals_from_wizard(self, batch_result):
        vals = super()._create_payment_vals_from_wizard(batch_result)
        vals["branch_id"] = self._get_batch_branch(batch_result).id
        return vals

    def _create_payment_vals_from_batch(self, batch_result):
        vals = super()._create_payment_vals_from_batch(batch_result)
        vals["branch_id"] = self._get_batch_branch(batch_result).id
        return vals
