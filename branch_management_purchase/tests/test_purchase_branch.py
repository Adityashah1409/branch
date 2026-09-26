from odoo import Command
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import tagged

from odoo.addons.branch_management_account.tests.common import BranchAccountTestCommon


@tagged("post_install", "-at_install", "branch_management")
class TestPurchaseBranch(BranchAccountTestCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._add_groups(
            cls.user_a | cls.user_b | cls.user_multi | cls.user_none | cls.manager | cls.branch_admin,
            "purchase.group_purchase_user",
        )
        cls.vendor = cls.env["res.partner"].create({"name": "Branch Test Vendor"})
        cls.product = cls.env["product.product"].create({
            "name": "Branch Purchased Service", "type": "service",
            "standard_price": 50.0, "supplier_taxes_id": [Command.clear()],
        })

    def _create_order(self, env, confirm=False, price=50.0, **values):
        order = env["purchase.order"].create({
            "partner_id": self.vendor.id,
            "order_line": [Command.create({
                "product_id": self.product.id, "product_qty": 2.0,
                "price_unit": price, "tax_ids": [Command.clear()],
            })],
            **values,
        })
        if confirm:
            order.button_confirm()
        return order

    def test_order_defaults_and_validation(self):
        order = self._create_order(self.env_for(self.user_a))
        self.assertEqual(order.branch_id, self.branch_ahm)
        self.assertEqual(order.order_line.branch_id, self.branch_ahm)
        order_srt = self._create_order(self.env_for(self.user_multi, branch=self.branch_srt))
        self.assertEqual(order_srt.branch_id, self.branch_srt)

        with self.assertRaises(ValidationError):
            self._create_order(self.env_for(self.user_a), branch_id=self.branch_srt.id)
        with self.assertRaises(ValidationError):
            order.write({"branch_id": self.branch_ho.id})
        with self.assertRaises(ValidationError):
            self._create_order(self.env, company_id=self.company_a.id, branch_id=self.branch_mum.id)

    def test_tc016_vendor_bill_keeps_order_branch(self):
        """TC-016: the vendor bill created from a purchase order keeps its branch."""
        env_multi = self.env_for(self.user_multi, branch=self.branch_ahm)
        order = self._create_order(env_multi, confirm=True, branch_id=self.branch_srt.id)
        self.assertEqual(order.state, "purchase")
        order.action_create_invoice()
        bill = order.invoice_ids
        self.assertEqual(len(bill), 1)
        self.assertEqual(bill.move_type, "in_invoice")
        self.assertEqual(bill.branch_id, self.branch_srt, "not the user's current branch")
        self.assertEqual(bill.invoice_line_ids.branch_id, self.branch_srt)

        # restricted user, branch-dedicated purchase journal
        ahm_journal = self.env["account.journal"].create({
            "name": "Ahmedabad Purchases", "code": "AHMP", "type": "purchase",
            "company_id": self.company_a.id, "branch_id": self.branch_ahm.id,
        })
        order_a = self._create_order(self.env_for(self.user_a), confirm=True)
        order_a.action_create_invoice()
        self.assertEqual(order_a.invoice_ids.branch_id, self.branch_ahm)
        self.assertEqual(order_a.invoice_ids.journal_id, ahm_journal)

    def test_tc016_bill_auto_complete_from_order(self):
        order = self._create_order(self.env_for(self.user_b), confirm=True)
        env_multi = self.env_for(self.user_multi, branch=self.branch_ahm)
        bill = env_multi["account.move"].with_context(default_move_type="in_invoice").new({
            "partner_id": self.vendor.id,
        })
        self.assertEqual(bill.branch_id, self.branch_ahm)
        bill.purchase_id = order
        bill._onchange_purchase_auto_complete()
        self.assertEqual(bill.branch_id, self.branch_srt)

    def test_orders_of_different_branches_billed_separately(self):
        env_admin = self.env_for(self.branch_admin)
        order_ahm = self._create_order(env_admin, confirm=True, branch_id=self.branch_ahm.id)
        order_srt = self._create_order(env_admin, confirm=True, branch_id=self.branch_srt.id)
        action = (order_ahm | order_srt).action_create_invoice()
        bills = order_ahm.invoice_ids | order_srt.invoice_ids
        self.assertEqual(len(bills), 2)
        self.assertEqual(order_ahm.invoice_ids.branch_id, self.branch_ahm)
        self.assertEqual(order_srt.invoice_ids.branch_id, self.branch_srt)
        self.assertEqual(action["res_model"], "account.move")

    def test_security(self):
        order_b = self._create_order(self.env_for(self.user_b), confirm=True)
        env_a = self.env_for(self.user_a)
        PurchaseOrder = env_a["purchase.order"]
        self.assertFalse(PurchaseOrder.search([("id", "=", order_b.id)]))
        self.assertFalse(env_a["purchase.order.line"].search([("order_id", "=", order_b.id)]))
        self.assertFalse(env_a["purchase.report"].search([("order_id", "=", order_b.id)]))
        with self.assertRaises(AccessError):
            PurchaseOrder.browse(order_b.id).read(["name"])
        with self.assertRaises(AccessError):
            PurchaseOrder.browse(order_b.id).write({"notes": "hacked"})
        with self.assertRaises(AccessError):
            PurchaseOrder.browse(order_b.id).unlink()
        with self.assertRaises(AccessError):
            env_a["purchase.order.line"].browse(order_b.order_line.id).read(["name"])
        # the branch admin sees everything, TC-022: archived branch stays readable
        self.assertTrue(self.env_for(self.branch_admin)["purchase.order"].search([("id", "=", order_b.id)]))
        self.branch_srt.active = False
        env_b = self.env_for(self.user_b)
        self.assertEqual(env_b["purchase.order"].browse(order_b.id).read(["name"])[0]["name"], order_b.name)

    def test_branch_sequence_numbering(self):
        standard = self._create_order(self.env_for(self.user_a))
        self.assertFalse(standard.name.startswith("AHM/"))
        self.company_a.branch_sequence_enabled = True
        first = self._create_order(self.env_for(self.user_a))
        second = self._create_order(self.env_for(self.user_a))
        other = self._create_order(self.env_for(self.user_b))
        self.assertEqual((first.name, second.name, other.name), ("AHM/PO/00001", "AHM/PO/00002", "SRT/PO/00001"))

    def test_purchase_report_and_pdf(self):
        self.branch_ahm.write({"street": "Ashram Road 12", "city": "Ahmedabad"})
        order = self._create_order(self.env_for(self.user_a), price=50.0)
        self._create_order(self.env_for(self.user_b), price=70.0)
        for report in ("purchase.report_purchase_quotation", "purchase.action_report_purchase_order"):
            html, _dummy = self.env["ir.actions.report"]._render_qweb_html(report, order.ids)
            self.assertIn(b"o_branch_address_block", html, report)
            self.assertIn(b"Ashram Road 12", html, report)

        groups = self.env["purchase.report"].with_company(self.company_a)._read_group(
            [("company_id", "=", self.company_a.id)], ["branch_id"], ["untaxed_total:sum"],
        )
        totals = dict(groups)
        self.assertEqual(totals[self.branch_ahm], 100.0)
        self.assertEqual(totals[self.branch_srt], 140.0)
        groups_a = self.env_for(self.user_a)["purchase.report"]._read_group([], ["branch_id"], ["__count"])
        self.assertEqual([branch for branch, _count in groups_a], [self.branch_ahm])

    def test_current_branch_filter_and_smart_button(self):
        env_multi = self.env_for(self.user_multi, branch=self.branch_ahm)
        order_ahm = self._create_order(env_multi)
        order_srt = self._create_order(env_multi, branch_id=self.branch_srt.id)
        found = env_multi["purchase.order"].search([
            ("is_current_branch", "=", True), ("id", "in", (order_ahm | order_srt).ids),
        ])
        self.assertEqual(found, order_ahm)
        branch = env_multi["res.branch"].browse(self.branch_ahm.id)
        self.assertEqual(branch.purchase_order_count, 1)
        action = branch.action_view_purchase_orders()
        self.assertEqual(env_multi["purchase.order"].search(action["domain"]), order_ahm)
        self.assertEqual(action["context"]["default_branch_id"], self.branch_ahm.id)
