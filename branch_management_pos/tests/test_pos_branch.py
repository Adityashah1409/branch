from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged

from .common import PosBranchCommon


@tagged("post_install", "-at_install", "branch_management")
class TestPosBranch(PosBranchCommon):

    # ------------------------------------------------------------------
    # Shop configuration
    # ------------------------------------------------------------------

    def test_config_branch_defaults_and_validation(self):
        self.assertEqual(self.config_ahm.branch_id, self.branch_ahm)
        # default: the working branch of the user creating the shop
        env_multi = self.env_for(self.user_multi, branch=self.branch_srt)
        self._add_groups(self.user_multi, "point_of_sale.group_pos_manager")
        config = env_multi["pos.config"].create({
            "name": "Default Branch Shop", "journal_id": self.sale_journal_a.id,
        })
        self.assertEqual(config.branch_id, self.branch_srt)
        # branch of another company / not allowed branch
        with self.assertRaises(ValidationError):
            self._create_config("Wrong Company Shop", self.branch_mum)
        with self.assertRaises(ValidationError):
            config.branch_id = self.branch_ho

    def test_config_journals_of_other_branch_rejected(self):
        srt_journal = self.env["account.journal"].create({
            "name": "Surat PoS Sales", "code": "SRTP", "type": "sale",
            "company_id": self.company_a.id, "branch_id": self.branch_srt.id,
        })
        with self.assertRaises(ValidationError):
            self.config_ahm.journal_id = srt_journal
        self.config_srt.journal_id = srt_journal
        self.assertEqual(self.config_srt.journal_id, srt_journal)

    def test_trusted_config_of_other_branch_rejected(self):
        with self.assertRaises(ValidationError):
            self.config_ahm.trusted_config_ids = self.config_srt
        config_ahm_2 = self._create_config("Ahmedabad Shop 2", self.branch_ahm)
        self.config_ahm.trusted_config_ids = config_ahm_2
        self.assertEqual(self.config_ahm.trusted_config_ids, config_ahm_2)

    def test_config_branch_change_refused_with_open_session(self):
        self._open_session(self.config_ahm, self.user_a)
        with self.assertRaises(UserError):
            self.config_ahm.branch_id = self.branch_srt

    # ------------------------------------------------------------------
    # Propagation: session, orders, payments, invoice, closing entries
    # ------------------------------------------------------------------

    def test_config_branch_propagates_to_session_and_orders(self):
        session = self._open_session(self.config_ahm, self.user_a)
        self.assertEqual(session.branch_id, self.branch_ahm)
        order = self._create_order(session)
        self.assertEqual(order.branch_id, self.branch_ahm)
        self.assertEqual(order.lines.branch_id, self.branch_ahm)
        self.assertEqual(order.payment_ids.branch_id, self.branch_ahm)

        # later branch changes of the shop do not rewrite the history
        self._close_session(session)
        self.config_ahm.branch_id = self.branch_srt
        self.assertEqual(session.branch_id, self.branch_ahm)
        self.assertEqual(order.branch_id, self.branch_ahm)
        self.assertEqual(self._open_session(self.config_ahm, self.user_multi).branch_id, self.branch_srt)

    def test_invoice_of_order_keeps_branch(self):
        session = self._open_session(self.config_ahm, self.user_a)
        order = self._create_order(
            session, partner=self.partner, to_invoice=True, payment_method=self.bank_pm)
        invoice = order.account_move
        self.assertTrue(invoice)
        self.assertEqual(invoice.move_type, "out_invoice")
        self.assertEqual(invoice.branch_id, self.branch_ahm)
        self.assertEqual(invoice.line_ids.branch_id, self.branch_ahm)
        # the bank payment reconciled with the invoice
        payment = self.env["account.payment"].search([("pos_session_id", "=", session.id)])
        self.assertTrue(payment)
        self.assertEqual(payment.branch_id, self.branch_ahm)
        self.assertEqual(payment.move_id.branch_id, self.branch_ahm)
        self.assertEqual(invoice.payment_state, "paid")

        vals = order._prepare_invoice_vals()
        self.assertEqual(vals["branch_id"], self.branch_ahm.id)

    def test_session_closing_entries_keep_branch(self):
        """Closing entries are created in the shop's branch, even when the
        session is closed by a user working in another branch."""
        session = self._open_session(self.config_ahm, self.user_a)
        self._create_order(session)                               # cash
        self._create_order(session, payment_method=self.bank_pm)  # bank
        closer_session = session.with_user(self.user_multi).with_context(
            current_branch_id=self.branch_srt.id, allowed_company_ids=self.company_a.ids)
        # 5.0 more cash counted than expected: cash difference statement line
        self._close_session(closer_session, counted_cash=105.0)

        closing = session.sale_move_ids
        self.assertEqual(len(closing), 1)
        self.assertEqual(closing.state, "posted")
        self.assertEqual(closing.branch_id, self.branch_ahm)
        self.assertEqual(closing.line_ids.branch_id, self.branch_ahm)

        statement_lines = session.bank_statement_id.line_ids
        self.assertEqual(len(statement_lines), 2, "cash sales + cash difference")
        self.assertEqual(statement_lines.move_id.branch_id, self.branch_ahm)

        payments = self.env["account.payment"].search([("pos_session_id", "=", session.id)])
        self.assertTrue(payments)
        self.assertEqual(payments.branch_id, self.branch_ahm)
        self.assertEqual(payments.move_id.branch_id, self.branch_ahm)

    def test_bank_difference_entry_keeps_branch(self):
        self.bank_journal_a.write({
            "loss_account_id": self.cash_loss_account.id,
            "profit_account_id": self.cash_profit_account.id,
        })
        session = self._open_session(self.config_ahm, self.user_a)
        self._create_order(session, payment_method=self.bank_pm)
        env_multi = self.env_for(self.user_multi, branch=self.branch_srt, company=self.company_a)
        session.with_env(env_multi)._handle_bank_payment_method_difference({self.bank_pm.id: 90.0})
        self.assertTrue(session.correction_move_ids)
        self.assertEqual(session.correction_move_ids.branch_id, self.branch_ahm)

    def test_invoice_after_session_closing_keeps_branch(self):
        session = self._open_session(self.config_ahm, self.user_a)
        order = self._create_order(session, partner=self.partner)
        self._close_session(session)
        self.assertEqual(order.account_move, session.sale_move_ids)

        env_multi = self.env_for(self.user_multi, branch=self.branch_srt, company=self.company_a)
        order.with_env(env_multi).action_pos_order_invoice()
        invoice = order.account_move
        self.assertEqual(invoice.move_type, "out_invoice")
        self.assertEqual(invoice.branch_id, self.branch_ahm)
        reversal = self.env["account.move"].search([("reversed_pos_order_id", "=", order.id)])
        self.assertTrue(reversal)
        self.assertEqual(reversal.branch_id, self.branch_ahm)

    def test_shop_without_branch(self):
        config = self._create_config("Shared Shop", False)
        session = self._open_session(config, self.user_multi)
        self.assertFalse(session.branch_id)
        order = self._create_order(session)
        self.assertFalse(order.branch_id)
        closer = session.with_context(current_branch_id=self.branch_srt.id)
        self._close_session(closer)
        # not the working branch of the user closing the session
        self.assertFalse(session.sale_move_ids.branch_id)
        self.assertFalse(session.bank_statement_id.line_ids.move_id.branch_id)
        # visible to the users of every branch
        env_b = self.env_for(self.user_b)
        self.assertEqual(env_b["pos.config"].search([("id", "=", config.id)]), config)
        self.assertEqual(env_b["pos.order"].search([("id", "=", order.id)]), order)

    # ------------------------------------------------------------------
    # Security
    # ------------------------------------------------------------------

    def test_branch_security(self):
        session = self._open_session(self.config_ahm, self.user_a)
        order = self._create_order(session)
        env_b = self.env_for(self.user_b)
        for model, record in (
            ("pos.config", self.config_ahm),
            ("pos.session", session),
            ("pos.order", order),
            ("pos.order.line", order.lines),
            ("pos.payment", order.payment_ids),
        ):
            self.assertFalse(env_b[model].search([("id", "=", record.id)]), model)
            with self.assertRaises(AccessError, msg=model):
                env_b[model].browse(record.id).read(["display_name"])
        with self.assertRaises(AccessError):
            env_b["pos.order"].browse(order.id).write({"note": "hack"})
        # the SRT cashier sees and opens the SRT shop only
        self.assertEqual(env_b["pos.config"].search([("id", "in", (self.config_ahm | self.config_srt).ids)]), self.config_srt)
        session_srt = self._open_session(self.config_srt, self.user_b)
        self.assertEqual(session_srt.branch_id, self.branch_srt)
        # the AHM cashier sees their own documents
        env_a = self.env_for(self.user_a)
        self.assertEqual(env_a["pos.order"].search([("session_id", "=", session.id)]), order)
        self.assertEqual(self.branch_ahm.with_user(self.user_a).pos_order_count, 1)
        self.assertEqual(self.branch_ahm.with_user(self.user_b).pos_order_count, 0)
        action = self.branch_ahm.action_view_pos_orders()
        self.assertEqual(self.env["pos.order"].search(action["domain"]), order)

    def test_pos_order_report_by_branch(self):
        session_ahm = self._open_session(self.config_ahm, self.user_a)
        self._create_order(session_ahm, qty=2.0)
        session_srt = self._open_session(self.config_srt, self.user_b)
        self._create_order(session_srt, qty=3.0)
        self.env.flush_all()
        Report = self.env["report.pos.order"]
        groups = dict(Report._read_group(
            [("config_id", "in", (self.config_ahm | self.config_srt).ids)],
            ["branch_id"], ["price_total:sum"],
        ))
        self.assertEqual(groups[self.branch_ahm], 200.0)
        self.assertEqual(groups[self.branch_srt], 300.0)
        rows_a = self.env_for(self.user_a)["report.pos.order"].search([
            ("config_id", "in", (self.config_ahm | self.config_srt).ids)])
        self.assertEqual(rows_a.branch_id, self.branch_ahm)
