from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged

from .common import BranchAccountTestCommon


@tagged("post_install", "-at_install", "branch_management")
class TestAccountBranch(BranchAccountTestCommon):

    # ------------------------------------------------------------------
    # Defaults and validation
    # ------------------------------------------------------------------

    def test_invoice_default_branch(self):
        """Invoices and bills default to the user's current branch."""
        invoice = self._create_invoice(self.env_for(self.user_a))
        self.assertEqual(invoice.branch_id, self.branch_ahm)
        self.assertEqual(invoice.line_ids.branch_id, self.branch_ahm,
                         "journal items store the branch of their entry")

        env_multi = self.env_for(self.user_multi, branch=self.branch_srt)
        bill = self._create_invoice(env_multi, move_type="in_invoice")
        self.assertEqual(bill.branch_id, self.branch_srt)

        invoice.action_post()
        self.assertEqual(invoice.state, "posted")
        credit_note = invoice._reverse_moves()
        self.assertEqual(credit_note.branch_id, self.branch_ahm, "a credit note keeps the branch")

    def test_tc019_invoice_branch_company_mismatch(self):
        """TC-019: Invoice branch/company mismatch is rejected."""
        with self.assertRaises(ValidationError):
            self.env["account.move"].with_company(self.company_a).create(
                self._invoice_vals(branch_id=self.branch_mum.id, company_id=self.company_a.id)
            )
        env = self.env_for(self.user_multi, companies=self.company_a | self.company_b)
        invoice = self._create_invoice(env, branch_id=self.branch_ahm.id)
        with self.assertRaises(ValidationError):
            invoice.write({"branch_id": self.branch_mum.id})

    def test_invoice_unauthorized_branch(self):
        env = self.env_for(self.user_a)
        with self.assertRaises(ValidationError):
            self._create_invoice(env, branch_id=self.branch_srt.id)
        invoice = self._create_invoice(env)
        with self.assertRaises(ValidationError):
            invoice.write({"branch_id": self.branch_ho.id})

    # ------------------------------------------------------------------
    # Journals
    # ------------------------------------------------------------------

    def test_journal_default_by_branch(self):
        """A branch-dedicated sale journal numbers the branch's invoices."""
        ahm_journal = self.env["account.journal"].create({
            "name": "Ahmedabad Sales", "code": "AHMS", "type": "sale",
            "company_id": self.company_a.id, "branch_id": self.branch_ahm.id,
        })
        invoice_a = self._create_invoice(self.env_for(self.user_a), post=True)
        self.assertEqual(invoice_a.journal_id, ahm_journal)
        self.assertTrue(invoice_a.name.startswith("AHMS/"), invoice_a.name)

        invoice_b = self._create_invoice(self.env_for(self.user_b), post=True)
        self.assertNotEqual(invoice_b.journal_id, ahm_journal)
        self.assertFalse(invoice_b.journal_id.branch_id)
        self.assertFalse(invoice_b.name.startswith("AHMS/"))

        # bills are not affected by a dedicated sale journal
        bill = self._create_invoice(self.env_for(self.user_a), move_type="in_invoice")
        self.assertEqual(bill.journal_id.type, "purchase")

        # changing the branch of a draft invoice changes its journal
        env_multi = self.env_for(self.user_multi, branch=self.branch_srt)
        draft = self._create_invoice(env_multi)
        self.assertEqual(draft.journal_id, self.sale_journal_a)
        draft.branch_id = self.branch_ahm
        self.assertEqual(draft.journal_id, ahm_journal)
        self.assertNotIn(ahm_journal, self._create_invoice(env_multi).suitable_journal_ids)
        draft.branch_id = self.branch_srt
        self.assertEqual(draft.journal_id, self.sale_journal_a)

    def test_journal_branch_mismatch_rejected(self):
        ahm_journal = self.env["account.journal"].create({
            "name": "Ahmedabad Sales", "code": "AHMS", "type": "sale",
            "company_id": self.company_a.id, "branch_id": self.branch_ahm.id,
        })
        env_multi = self.env_for(self.user_multi, branch=self.branch_srt)
        with self.assertRaises(ValidationError):
            self._create_invoice(env_multi, journal_id=ahm_journal.id)
        with self.assertRaises(ValidationError):
            self._create_invoice(self.env, journal_id=ahm_journal.id, branch_id=False)
        # a journal can only be dedicated to a branch of its company
        with self.assertRaises(UserError):
            ahm_journal.branch_id = self.branch_mum

    # ------------------------------------------------------------------
    # Payments
    # ------------------------------------------------------------------

    def _register_payment(self, env, invoices, **values):
        wizard = env["account.payment.register"].with_context(
            active_model="account.move", active_ids=invoices.ids,
        ).create(values)
        return wizard._create_payments()

    def test_payment_keeps_invoice_branch(self):
        """The Register Payment wizard creates the payment in the invoice's branch."""
        env_multi = self.env_for(self.user_multi, branch=self.branch_ahm)
        invoice = self._create_invoice(env_multi, post=True, branch_id=self.branch_srt.id)
        # the user works in AHM but pays an SRT invoice: the payment is SRT
        payment = self._register_payment(env_multi, invoice)
        self.assertEqual(payment.branch_id, self.branch_srt)
        self.assertEqual(payment.move_id.branch_id, self.branch_srt)
        self.assertEqual(payment.move_id.line_ids.branch_id, self.branch_srt)
        self.assertIn(invoice.payment_state, ("paid", "in_payment"))

        # a user restricted to AHM registers the payment of an AHM invoice
        env_a = self.env_for(self.user_a)
        invoice_a = self._create_invoice(env_a, post=True)
        payment_a = self._register_payment(env_a, invoice_a)
        self.assertEqual(payment_a.branch_id, self.branch_ahm)
        self.assertIn(invoice_a.payment_state, ("paid", "in_payment"))

    def test_payment_grouping_never_mixes_branches(self):
        env = self.env_for(self.branch_admin, company=self.company_a)
        invoice_ahm = self._create_invoice(env, post=True, branch_id=self.branch_ahm.id)
        invoice_srt = self._create_invoice(env, post=True, branch_id=self.branch_srt.id)
        payments = self._register_payment(env, invoice_ahm | invoice_srt, group_payment=True)
        self.assertEqual(len(payments), 2)
        self.assertEqual(
            {(payment.branch_id, payment.amount) for payment in payments},
            {(self.branch_ahm, 100.0), (self.branch_srt, 100.0)},
        )

    def test_payment_uses_branch_bank_journal(self):
        ahm_bank = self.env["account.journal"].create({
            "name": "Ahmedabad Bank", "code": "AHMB", "type": "bank",
            "company_id": self.company_a.id, "branch_id": self.branch_ahm.id,
        })
        env_a = self.env_for(self.user_a)
        invoice = self._create_invoice(env_a, post=True)
        payment = self._register_payment(env_a, invoice)
        self.assertEqual(payment.journal_id, ahm_bank)

        # the SRT invoice can't be paid in the AHM bank journal
        invoice_b = self._create_invoice(self.env_for(self.user_b), post=True)
        payment_b = self._register_payment(self.env_for(self.user_b), invoice_b)
        self.assertNotEqual(payment_b.journal_id, ahm_bank)
        with self.assertRaises(ValidationError):
            self.env["account.payment"].create({
                "payment_type": "inbound", "partner_type": "customer", "amount": 10.0,
                "partner_id": self.partner.id, "journal_id": ahm_bank.id,
                "branch_id": self.branch_srt.id,
            })

    def test_payment_branch_change_follows_on_entry(self):
        env_multi = self.env_for(self.user_multi, branch=self.branch_ahm)
        payment = env_multi["account.payment"].create({
            "payment_type": "inbound", "partner_type": "customer", "amount": 50.0,
            "partner_id": self.partner.id, "journal_id": self.bank_journal_a.id,
        })
        self.assertEqual(payment.branch_id, self.branch_ahm)
        payment.action_post()
        if payment.move_id:
            self.assertEqual(payment.move_id.branch_id, self.branch_ahm)
        payment.branch_id = self.branch_srt
        if payment.move_id:
            self.assertEqual(payment.move_id.branch_id, self.branch_srt)

    # ------------------------------------------------------------------
    # Security
    # ------------------------------------------------------------------

    def test_tc021_unauthorized_user_cannot_read_other_branch_invoice(self):
        """TC-021: a user of SRT can't see or read an AHM invoice."""
        env_a = self.env_for(self.user_a)
        invoice = self._create_invoice(env_a, post=True)
        payment = self._register_payment(env_a, invoice)

        env_b = self.env_for(self.user_b)
        Move = env_b["account.move"]
        self.assertFalse(Move.search([("id", "=", invoice.id)]))
        self.assertFalse(env_b["account.move.line"].search([("move_id", "=", invoice.id)]))
        self.assertFalse(env_b["account.payment"].search([("id", "=", payment.id)]))
        with self.assertRaises(AccessError):
            Move.browse(invoice.id).read(["name"])
        with self.assertRaises(AccessError):
            Move.browse(invoice.id).write({"ref": "hacked"})
        with self.assertRaises(AccessError):
            env_b["account.payment"].browse(payment.id).read(["amount"])
        with self.assertRaises(AccessError):
            env_b["account.move.line"].browse(invoice.line_ids[0].id).read(["name"])

        # user A still reads it, the branch admin sees everything
        self.assertTrue(env_a["account.move"].search([("id", "=", invoice.id)]))
        env_admin = self.env_for(self.branch_admin)
        self.assertTrue(env_admin["account.move"].search([("id", "=", invoice.id)]))

        # invoice analysis applies the same boundary
        Report = env_b["account.invoice.report"]
        self.assertFalse(Report.search([("move_id", "=", invoice.id)]))
        self.assertTrue(env_a["account.invoice.report"].search([("move_id", "=", invoice.id)]))

    def test_entries_without_branch_stay_visible(self):
        invoice = self._create_invoice(self.env(context=dict(self.env.context, allowed_company_ids=self.company_a.ids)), branch_id=False)
        self.assertTrue(self.env_for(self.user_b)["account.move"].search([("id", "=", invoice.id)]))

    def test_archived_branch_keeps_invoices_readable(self):
        invoice = self._create_invoice(self.env_for(self.user_a), post=True)
        self.branch_ahm.active = False
        env_a = self.env_for(self.user_a)
        self.assertEqual(env_a["account.move"].browse(invoice.id).read(["name"])[0]["name"], invoice.name)

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    def test_invoice_analysis_group_by_branch(self):
        self._create_invoice(self.env_for(self.user_a), post=True, price=100.0)
        self._create_invoice(self.env_for(self.user_b), post=True, price=250.0)
        groups = self.env["account.invoice.report"].with_company(self.company_a)._read_group(
            [("company_id", "=", self.company_a.id)], ["branch_id"], ["price_subtotal:sum"],
        )
        totals = {branch: total for branch, total in groups}
        self.assertEqual(totals[self.branch_ahm], 100.0)
        self.assertEqual(totals[self.branch_srt], 250.0)

    def test_invoice_pdf_shows_branch(self):
        self.branch_ahm.write({"street": "Ashram Road 12", "city": "Ahmedabad"})
        invoice = self._create_invoice(self.env_for(self.user_a), post=True)
        html, _dummy = self.env["ir.actions.report"]._render_qweb_html("account.account_invoices", invoice.ids)
        self.assertIn("o_branch_address_block", str(html))
        self.assertIn("Ashram Road 12", str(html))

        payment = self._register_payment(self.env_for(self.user_a), invoice)
        html, _dummy = self.env["ir.actions.report"]._render_qweb_html(
            "account.action_report_payment_receipt", payment.ids,
        )
        self.assertIn("Ashram Road 12", str(html))

    def test_branch_smart_buttons(self):
        env_a = self.env_for(self.user_a)
        self._create_invoice(env_a, post=True)
        bill = self._create_invoice(env_a, move_type="in_invoice", post=True)
        self._register_payment(env_a, bill)
        branch = env_a["res.branch"].browse(self.branch_ahm.id)
        self.assertEqual((branch.invoice_count, branch.bill_count, branch.payment_count), (1, 1, 1))
        action = branch.action_view_invoices()
        self.assertEqual(action["res_model"], "account.move")
        self.assertEqual(action["context"]["default_branch_id"], self.branch_ahm.id)
        self.assertEqual(env_a["account.move"].search_count(action["domain"]), 1)
        self.assertEqual(env_a["account.move"].search_count(branch.action_view_bills()["domain"]), 1)
        self.assertEqual(env_a["account.payment"].search_count(branch.action_view_payments()["domain"]), 1)
        # other branch's user counts nothing of AHM
        other = self.env_for(self.user_b)["res.branch"].browse(self.branch_ahm.id)
        self.assertEqual(other.invoice_count, 0)

    def test_current_branch_filter(self):
        env_multi = self.env_for(self.user_multi, branch=self.branch_ahm)
        inv_ahm = self._create_invoice(env_multi)
        inv_srt = self._create_invoice(env_multi, branch_id=self.branch_srt.id)
        found = env_multi["account.move"].search([
            ("is_current_branch", "=", True), ("id", "in", (inv_ahm | inv_srt).ids),
        ])
        self.assertEqual(found, inv_ahm)
        self.assertTrue(inv_ahm.with_env(env_multi).line_ids.branch_id == self.branch_ahm)
        # grouping journal items by branch
        groups = env_multi["account.move.line"]._read_group(
            [("move_id", "in", (inv_ahm | inv_srt).ids)], ["branch_id"], ["__count"],
        )
        self.assertEqual({branch for branch, _count in groups}, {self.branch_ahm, self.branch_srt})
        self.assertTrue(all(count for _branch, count in groups))
