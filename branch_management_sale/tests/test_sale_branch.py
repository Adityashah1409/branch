from odoo import Command
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import tagged

from odoo.addons.branch_management_account.tests.common import BranchAccountTestCommon


@tagged("post_install", "-at_install", "branch_management")
class TestSaleBranch(BranchAccountTestCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._add_groups(
            cls.user_a | cls.user_b | cls.user_multi | cls.user_none | cls.manager | cls.branch_admin,
            "sales_team.group_sale_salesman_all_leads",
        )
        cls.product = cls.env["product.product"].create({
            "name": "Branch Service", "type": "service", "invoice_policy": "order",
            "list_price": 100.0, "taxes_id": [Command.clear()],
        })

    def _create_order(self, env, confirm=False, price=100.0, **values):
        order = env["sale.order"].create({
            "partner_id": self.partner.id,
            "order_line": [Command.create({
                "product_id": self.product.id, "product_uom_qty": 1.0,
                "price_unit": price, "tax_ids": [Command.clear()],
            })],
            **values,
        })
        if confirm:
            order.action_confirm()
        return order

    # ------------------------------------------------------------------
    # Defaults and validation
    # ------------------------------------------------------------------

    def test_tc011_order_defaults_to_current_branch(self):
        """TC-011: a quotation defaults to the user's current branch."""
        order = self._create_order(self.env_for(self.user_a))
        self.assertEqual(order.branch_id, self.branch_ahm)
        self.assertEqual(order.order_line.branch_id, self.branch_ahm)

        order_srt = self._create_order(self.env_for(self.user_multi, branch=self.branch_srt))
        self.assertEqual(order_srt.branch_id, self.branch_srt)
        # a branch that is not selectable is ignored: back to the default branch
        order_ho = self._create_order(self.env_for(self.user_multi, branch=self.branch_ho))
        self.assertEqual(order_ho.branch_id, self.branch_ahm)
        # the default branch belongs to the order's company
        env_b = self.env_for(self.user_multi, company=self.company_a, companies=self.company_a | self.company_b)
        order_b = self._create_order(env_b, company_id=self.company_b.id)
        self.assertEqual(order_b.branch_id, self.branch_mum)

    def test_tc005_order_unauthorized_branch_rejected(self):
        """TC-005: a user cannot use a branch they are not allowed in."""
        env = self.env_for(self.user_a)
        with self.assertRaises(ValidationError):
            self._create_order(env, branch_id=self.branch_srt.id)
        order = self._create_order(env)
        with self.assertRaises(ValidationError):
            order.write({"branch_id": self.branch_ho.id})
        self.assertEqual(order.branch_id, self.branch_ahm)

    def test_order_other_company_branch_rejected(self):
        with self.assertRaises(ValidationError):
            self._create_order(self.env, company_id=self.company_a.id, branch_id=self.branch_mum.id)
        env = self.env_for(self.user_multi, companies=self.company_a | self.company_b)
        order = self._create_order(env)
        with self.assertRaises(ValidationError):
            order.write({"branch_id": self.branch_mum.id})

    # ------------------------------------------------------------------
    # Security
    # ------------------------------------------------------------------

    def test_tc012_user_cannot_access_other_branch_orders(self):
        """TC-012: user A cannot read branch B's orders (search, read, write, unlink)."""
        order_b = self._create_order(self.env_for(self.user_b))
        env_a = self.env_for(self.user_a)
        SaleOrder = env_a["sale.order"]
        self.assertFalse(SaleOrder.search([("id", "=", order_b.id)]))
        self.assertFalse(env_a["sale.order.line"].search([("order_id", "=", order_b.id)]))
        self.assertFalse(env_a["sale.report"].search([("order_reference", "=", f"sale.order,{order_b.id}")]))
        with self.assertRaises(AccessError):
            SaleOrder.browse(order_b.id).read(["name"])
        with self.assertRaises(AccessError):
            SaleOrder.browse(order_b.id).write({"note": "hacked"})
        with self.assertRaises(AccessError):
            SaleOrder.browse(order_b.id).unlink()
        with self.assertRaises(AccessError):
            env_a["sale.order.line"].browse(order_b.order_line.id).read(["name"])
        self.assertTrue(order_b.exists())

    def test_branch_admin_sees_all_orders(self):
        order_a = self._create_order(self.env_for(self.user_a))
        order_b = self._create_order(self.env_for(self.user_b))
        env_admin = self.env_for(self.branch_admin)
        found = env_admin["sale.order"].search([("id", "in", (order_a | order_b).ids)])
        self.assertEqual(found, order_a | order_b)
        env_multi = self.env_for(self.user_multi)
        self.assertEqual(env_multi["sale.order"].search([("id", "in", (order_a | order_b).ids)]), order_a | order_b)

    def test_tc022_archived_branch_keeps_orders_readable(self):
        """TC-022: archiving a branch keeps its history readable."""
        order = self._create_order(self.env_for(self.user_a), confirm=True)
        self.branch_ahm.active = False
        env_a = self.env_for(self.user_a)
        self.assertEqual(env_a["sale.order"].search([("id", "=", order.id)]), order)
        self.assertEqual(env_a["sale.order"].browse(order.id).read(["branch_id"])[0]["branch_id"][0], self.branch_ahm.id)

    # ------------------------------------------------------------------
    # Invoicing
    # ------------------------------------------------------------------

    def test_tc014_invoice_keeps_order_branch(self):
        """TC-014: the invoice created from an order is in the order's branch."""
        env_multi = self.env_for(self.user_multi, branch=self.branch_ahm)
        order = self._create_order(env_multi, confirm=True, branch_id=self.branch_srt.id)
        invoice = order._create_invoices()
        self.assertEqual(invoice.branch_id, self.branch_srt, "not the user's current branch")
        self.assertEqual(invoice.line_ids.branch_id, self.branch_srt)

        # a salesperson restricted to AHM invoices their order
        order_a = self._create_order(self.env_for(self.user_a), confirm=True)
        invoice_a = order_a._create_invoices()
        self.assertEqual(invoice_a.branch_id, self.branch_ahm)
        invoice_a.action_post()
        self.assertEqual(order_a.invoice_status, "invoiced")

    def test_tc014_invoice_uses_branch_journal(self):
        ahm_journal = self.env["account.journal"].create({
            "name": "Ahmedabad Sales", "code": "AHMS", "type": "sale",
            "company_id": self.company_a.id, "branch_id": self.branch_ahm.id,
        })
        order = self._create_order(self.env_for(self.user_a), confirm=True)
        invoice = order._create_invoices()
        self.assertEqual(invoice.journal_id, ahm_journal)

    def test_tc014_down_payment_and_final_invoice(self):
        env_a = self.env_for(self.user_a)
        order = self._create_order(env_a, confirm=True, price=1000.0)
        wizard = env_a["sale.advance.payment.inv"].with_context(
            active_model="sale.order", active_ids=order.ids,
        ).create({"advance_payment_method": "percentage", "amount": 10.0})
        action = wizard.create_invoices()
        down_payment = self.env["account.move"].browse(action["res_id"])
        self.assertEqual(down_payment.branch_id, self.branch_ahm)
        self.assertEqual(down_payment.amount_untaxed, 100.0)
        down_payment.action_post()

        wizard = env_a["sale.advance.payment.inv"].with_context(
            active_model="sale.order", active_ids=order.ids,
        ).create({"advance_payment_method": "delivered"})
        wizard.create_invoices()
        final = order.invoice_ids - down_payment
        self.assertEqual(final.branch_id, self.branch_ahm)
        self.assertEqual(final.amount_untaxed, 900.0)

    def test_orders_of_different_branches_not_grouped(self):
        env_admin = self.env_for(self.branch_admin)
        order_ahm = self._create_order(env_admin, confirm=True, branch_id=self.branch_ahm.id)
        order_srt = self._create_order(env_admin, confirm=True, branch_id=self.branch_srt.id)
        invoices = (order_ahm | order_srt)._create_invoices()
        self.assertEqual(len(invoices), 2)
        self.assertEqual(set(invoices.mapped("branch_id")), {self.branch_ahm, self.branch_srt})
        self.assertEqual(order_ahm.invoice_ids.branch_id, self.branch_ahm)

    # ------------------------------------------------------------------
    # Numbering, reporting, UI helpers
    # ------------------------------------------------------------------

    def test_branch_sequence_numbering(self):
        standard = self._create_order(self.env_for(self.user_a))
        self.assertFalse(standard.name.startswith("AHM/"))

        self.company_a.branch_sequence_enabled = True
        first = self._create_order(self.env_for(self.user_a))
        second = self._create_order(self.env_for(self.user_a))
        other = self._create_order(self.env_for(self.user_b))
        self.assertEqual(first.name, "AHM/SO/00001")
        self.assertEqual(second.name, "AHM/SO/00002")
        self.assertEqual(other.name, "SRT/SO/00001")
        # an explicit name is kept
        named = self._create_order(self.env_for(self.user_a), name="MANUAL-1")
        self.assertEqual(named.name, "MANUAL-1")
        # no branch: standard numbering
        no_branch = self._create_order(self.env_for(self.user_none))
        self.assertFalse(no_branch.branch_id)
        self.assertNotIn("/SO/", no_branch.name)

    def test_sale_report_group_by_branch(self):
        self._create_order(self.env_for(self.user_a), confirm=True, price=100.0)
        self._create_order(self.env_for(self.user_b), confirm=True, price=300.0)
        groups = self.env["sale.report"].with_company(self.company_a)._read_group(
            [("company_id", "=", self.company_a.id)], ["branch_id"], ["price_subtotal:sum"],
        )
        totals = dict(groups)
        self.assertEqual(totals[self.branch_ahm], 100.0)
        self.assertEqual(totals[self.branch_srt], 300.0)
        # a restricted user only sees their branch in the analysis
        groups_a = self.env_for(self.user_a)["sale.report"]._read_group([], ["branch_id"], ["__count"])
        self.assertEqual([branch for branch, _count in groups_a], [self.branch_ahm])

    def test_order_pdf_shows_branch(self):
        self.branch_ahm.write({"street": "Ashram Road 12", "city": "Ahmedabad"})
        order = self._create_order(self.env_for(self.user_a))
        html, _dummy = self.env["ir.actions.report"]._render_qweb_html("sale.action_report_saleorder", order.ids)
        self.assertIn(b"o_branch_address_block", html)
        self.assertIn(b"Ashram Road 12", html)

    def test_current_branch_filter_and_smart_button(self):
        env_multi = self.env_for(self.user_multi, branch=self.branch_ahm)
        order_ahm = self._create_order(env_multi)
        order_srt = self._create_order(env_multi, branch_id=self.branch_srt.id)
        orders = order_ahm | order_srt
        found = env_multi["sale.order"].search([("is_current_branch", "=", True), ("id", "in", orders.ids)])
        self.assertEqual(found, order_ahm)
        env_srt = self.env_for(self.user_multi, branch=self.branch_srt)
        found = env_srt["sale.order"].search([("is_current_branch", "=", True), ("id", "in", orders.ids)])
        self.assertEqual(found, order_srt)

        branch = env_multi["res.branch"].browse(self.branch_ahm.id)
        self.assertEqual(branch.sale_order_count, 1)
        action = branch.action_view_sale_orders()
        self.assertEqual(env_multi["sale.order"].search(action["domain"]), order_ahm)
        self.assertEqual(action["context"]["default_branch_id"], self.branch_ahm.id)
        self.assertEqual(self.env_for(self.user_b)["res.branch"].browse(self.branch_ahm.id).sale_order_count, 0)
