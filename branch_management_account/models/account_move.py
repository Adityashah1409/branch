from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _name = "account.move"
    _inherit = ["account.move", "res.branch.mixin"]

    branch_id = fields.Many2one(tracking=True)

    # ------------------------------------------------------------------
    # Journal selection
    # ------------------------------------------------------------------

    def _get_branch_journal_domain(self):
        """Journals that could be used by this move, whatever their branch."""
        self.ensure_one()
        Journal = self.env["account.journal"]
        company = self.company_id or self.env.company
        return [
            *Journal._check_company_domain(company),
            ("type", "in", self._get_valid_journal_types()),
        ]

    def _get_branch_journal(self, journal):
        """Return the journal to use instead of ``journal`` for the move's branch.

        * a journal dedicated to the move's branch wins (same currency first):
          this is how a branch gets its own invoice numbering, through the
          journal sequence, without touching move names;
        * a journal dedicated to *another* branch is never proposed: fall back
          on a journal shared by all branches;
        * otherwise keep ``journal``.
        """
        self.ensure_one()
        Journal = self.env["account.journal"]
        domain = self._get_branch_journal_domain()
        if self.branch_id:
            dedicated = Journal.search([*domain, ("branch_id", "=", self.branch_id.id)])
            if dedicated:
                return (
                    dedicated.filtered(lambda j: j.currency_id == journal.currency_id)
                    or dedicated
                )[:1]
        if journal.branch_id and journal.branch_id != self.branch_id:
            return Journal.search([*domain, ("branch_id", "=", False)], limit=1) or journal
        return journal

    def _search_default_journal(self):
        journal = super()._search_default_journal()
        if self.statement_line_ids.statement_id.journal_id:
            # the statement's journal is imposed
            return journal
        return self._get_branch_journal(journal)

    @api.depends("branch_id")
    def _compute_journal_id(self):
        super()._compute_journal_id()
        for move in self:
            if (
                move.state != "draft"
                or move.posted_before
                or move.origin_payment_id
                or move.statement_line_id
            ):
                continue
            journal = move.journal_id
            foreign_branch_journal = journal.branch_id and journal.branch_id != move.branch_id
            # only invoices/bills switch to the branch's dedicated journal:
            # the journal of other entries is chosen by the flow creating them
            may_use_dedicated = move.is_invoice(include_receipts=True) and move.branch_id
            if foreign_branch_journal or may_use_dedicated:
                branch_journal = move._get_branch_journal(journal)
                if branch_journal != journal:
                    move.journal_id = branch_journal

    @api.depends("branch_id")
    def _compute_suitable_journal_ids(self):
        super()._compute_suitable_journal_ids()
        for move in self:
            move.suitable_journal_ids = move.suitable_journal_ids.filtered(
                lambda journal: not journal.branch_id or journal.branch_id == move.branch_id
            )

    def _compute_preferred_payment_method_line_id(self):
        super()._compute_preferred_payment_method_line_id()
        # never propose the payment method of a journal dedicated to another branch
        for move in self:
            journal_branch = move.preferred_payment_method_line_id.journal_id.branch_id
            if journal_branch and journal_branch != move.branch_id:
                move.preferred_payment_method_line_id = False

    @api.onchange("company_id")
    def _onchange_company_id_branch(self):
        self._branch_sync_with_company()

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------

    @api.constrains("journal_id", "branch_id", "company_id")
    def _check_journal_branch(self):
        # the mixin only validates on branch changes: the company of a move
        # can also change through its journal
        self._check_branch_company_match()
        for move in self:
            journal_branch = move.journal_id.branch_id
            if journal_branch and journal_branch != move.branch_id:
                raise ValidationError(self.env._(
                    "Journal %(journal)s is dedicated to branch %(journal_branch)s: "
                    "it cannot be used by %(move)s (branch: %(branch)s).",
                    journal=move.journal_id.display_name,
                    journal_branch=journal_branch.display_name,
                    move=move.display_name,
                    branch=move.branch_id.display_name or self.env._("none"),
                ))
