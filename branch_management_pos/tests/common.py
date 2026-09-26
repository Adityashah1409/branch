from random import randint

from odoo import Command, fields

from odoo.addons.branch_management_account.tests.common import BranchAccountTestCommon


class PosBranchCommon(BranchAccountTestCommon):
    """Branch + accounting fixtures and a shop (pos.config) of branch AHM with
    a cash and a bank payment method. No demo data: orders are built like the
    PoS frontend sends them (``pos.order.sync_from_ui``)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(
            cls.env.context, allowed_company_ids=[cls.company_a.id, cls.company_b.id]))
        cls.company_a.account_fiscal_country_id = cls.env.ref("base.us")
        cls._add_groups(
            cls.user_a | cls.user_b | cls.user_multi | cls.user_none,
            "point_of_sale.group_pos_user",
        )
        cls._add_groups(cls.manager | cls.branch_admin, "point_of_sale.group_pos_manager")

        Account = cls.env["account.account"].with_company(cls.company_a)
        cls.cash_profit_account = Account.create({
            "name": "Cash Gain", "code": "BRPOS1", "account_type": "income_other",
        })
        cls.cash_loss_account = Account.create({
            "name": "Cash Loss", "code": "BRPOS2", "account_type": "expense",
        })
        # created on the fly at the first session closing (point_of_sale),
        # which a cashier may not do
        cls.env["account.journal"].with_company(cls.company_a)._ensure_company_account_journal()
        cls.bank_pm = cls.env["pos.payment.method"].create({
            "name": "Branch Bank", "type": "bank", "journal_id": cls.bank_journal_a.id,
            "company_id": cls.company_a.id,
        })
        cls.pos_product = cls.env["product.product"].create({
            "name": "Branch PoS Item", "type": "consu", "available_in_pos": True,
            "list_price": 100.0, "taxes_id": [Command.clear()],
            "company_id": cls.company_a.id,
        })
        cls.config_ahm = cls._create_config("Ahmedabad Shop", cls.branch_ahm)
        cls.config_srt = cls._create_config("Surat Shop", cls.branch_srt)

    @classmethod
    def _create_config(cls, name, branch, **values):
        # a cash payment method (and its cash journal) belongs to one shop;
        # the generic chart of accounts has no cash journal
        cash_journal = cls.env["account.journal"].create({
            "name": f"{name} Cash", "code": f"C{cls.env['account.journal'].search_count([]):04d}",
            "type": "cash", "company_id": cls.company_a.id,
            "profit_account_id": cls.cash_profit_account.id,
            "loss_account_id": cls.cash_loss_account.id,
        })
        cash_pm = cls.env["pos.payment.method"].create({
            "name": f"{name} Cash", "type": "cash", "journal_id": cash_journal.id,
            "company_id": cls.company_a.id,
        })
        return cls.env["pos.config"].with_company(cls.company_a).create({
            "name": name,
            "company_id": cls.company_a.id,
            # branch None: let the shop get its default branch
            **({} if branch is None else {"branch_id": branch.id if branch else False}),
            "journal_id": cls.sale_journal_a.id,
            "payment_method_ids": [Command.set((cash_pm | cls.bank_pm).ids)],
            **values,
        })

    @staticmethod
    def _cash_pm(session):
        return session.config_id.payment_method_ids.filtered(lambda pm: pm.type == "cash")

    def _open_session(self, config, user):
        config = config.with_user(user).with_context(allowed_company_ids=self.company_a.ids)
        config.open_ui()
        session = config.current_session_id
        self.assertTrue(session)
        session.set_opening_control(0, None)
        return session

    def _order_data(self, session, qty=1.0, price=100.0, payment_method=None, partner=None,
                    to_invoice=False):
        uuid = "%05d-%03d-%04d" % (randint(1, 99999), randint(1, 999), randint(1, 9999))
        amount = qty * price
        return {
            "amount_paid": amount,
            "amount_return": 0,
            "amount_tax": 0,
            "amount_total": amount,
            "date_order": fields.Datetime.to_string(fields.Datetime.now()),
            "fiscal_position_id": False,
            "pricelist_id": session.config_id.pricelist_id.id,
            "name": "Order %s" % uuid,
            "lines": [Command.create({
                "id": randint(1, 1000000),
                "product_id": self.pos_product.id,
                "price_unit": price,
                "qty": qty,
                "price_subtotal": abs(amount),
                "price_subtotal_incl": abs(amount),
                "tax_ids": [Command.clear()],
            })],
            "partner_id": partner.id if partner else False,
            "session_id": session.id,
            "payment_ids": [Command.create({
                "amount": amount,
                "name": fields.Datetime.now(),
                "payment_method_id": (payment_method or self._cash_pm(session)).id,
            })],
            "uuid": uuid,
            "user_id": session.env.uid,
            "to_invoice": to_invoice,
        }

    def _create_order(self, session, **kwargs):
        result = session.env["pos.order"].sync_from_ui([self._order_data(session, **kwargs)])
        order = session.env["pos.order"].browse(result["pos.order"][0]["id"])
        self.assertEqual(order.state, "paid")
        return order

    def _close_session(self, session, counted_cash=None):
        cash_pm = self._cash_pm(session)
        if counted_cash is None:
            counted_cash = sum(session.order_ids.payment_ids.filtered(
                lambda payment: payment.payment_method_id == cash_pm).mapped("amount"))
        result = session.close_session_from_ui({cash_pm.id: counted_cash})
        self.assertTrue(result["status"], result)
        self.assertEqual(session.state, "closed")
