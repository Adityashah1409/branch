from datetime import timedelta

from odoo import Command, fields
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import Form, tagged

from odoo.addons.branch_management_account.tests.common import BranchAccountTestCommon
from odoo.addons.branch_management_stock.tests.common import StockBranchCommon


@tagged("post_install", "-at_install", "branch_management")
class TestPurchaseStockBranch(BranchAccountTestCommon, StockBranchCommon):
    """Purchase -> Receipt keeps the branch (TC-015)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._add_groups(
            cls.user_a | cls.user_b | cls.user_multi | cls.manager | cls.branch_admin,
            "purchase.group_purchase_user",
        )
        cls.vendor = cls.env["res.partner"].create({"name": "Branch Stock Vendor"})
        cls.product.write({
            "standard_price": 40.0, "purchase_method": "receive",
            "supplier_taxes_id": [Command.clear()],
        })

    def _create_order(self, env, confirm=False, **values):
        order = env["purchase.order"].create({
            "partner_id": self.vendor.id,
            "order_line": [Command.create({
                "product_id": self.product.id, "product_qty": 4.0,
                "price_unit": 40.0, "tax_ids": [Command.clear()],
            })],
            **values,
        })
        if confirm:
            order.button_confirm()
        return order

    def _receive(self, picking):
        picking.action_assign()
        picking.move_ids.quantity = picking.move_ids.product_uom_qty
        picking.move_ids.picked = True
        picking.button_validate()
        self.assertEqual(picking.state, "done")

    # ------------------------------------------------------------------
    # Operation type of the order
    # ------------------------------------------------------------------

    def test_order_picking_type_follows_branch(self):
        order = self._create_order(self.env_for(self.user_a))
        self.assertEqual(order.branch_id, self.branch_ahm)
        self.assertEqual(order.picking_type_id, self.wh_ahm.in_type_id)

        # explicit branch other than the working branch
        env_multi = self.env_for(self.user_multi, branch=self.branch_ahm)
        order_srt = self._create_order(env_multi, branch_id=self.branch_srt.id)
        self.assertEqual(order_srt.picking_type_id, self.wh_srt.in_type_id)

        # default value in the form, then branch change (onchange)
        with Form(env_multi["purchase.order"]) as form:
            self.assertEqual(form.branch_id, self.branch_ahm)
            self.assertEqual(form.picking_type_id, self.wh_ahm.in_type_id)
            form.partner_id = self.vendor
            form.branch_id = self.branch_srt
            self.assertEqual(form.picking_type_id, self.wh_srt.in_type_id)
        order_form = form.record
        self.assertEqual(order_form.branch_id, self.branch_srt)
        self.assertEqual(order_form.picking_type_id, self.wh_srt.in_type_id)

        # a branch without warehouse receives in the shared company warehouse
        order_guj = self._create_order(self.env, branch_id=self.branch_guj.id)
        self.assertEqual(order_guj.picking_type_id, self.wh_company_a.in_type_id)

    def test_order_branch_from_picking_type(self):
        # an order created for an operation type gets the type's branch
        env_multi = self.env_for(self.user_multi, branch=self.branch_ahm)
        order = self._create_order(env_multi, picking_type_id=self.wh_srt.in_type_id.id)
        self.assertEqual(order.branch_id, self.branch_srt)

    def test_mismatched_picking_type_rejected(self):
        env_a = self.env_for(self.user_a)
        with self.assertRaises(ValidationError):
            self._create_order(
                env_a, branch_id=self.branch_ahm.id, picking_type_id=self.wh_srt.in_type_id.id)
        order = self._create_order(env_a)
        with self.assertRaises(ValidationError):
            order.picking_type_id = self.wh_srt.in_type_id
        # shared warehouse: accepted
        order.picking_type_id = self.wh_company_a.in_type_id
        self.assertEqual(order.picking_type_id, self.wh_company_a.in_type_id)

    # ------------------------------------------------------------------
    # Purchase -> Receipt -> Bill (TC-015)
    # ------------------------------------------------------------------

    def test_tc015_receipt_keeps_order_branch(self):
        """TC-015: confirming a purchase order of AHM creates an AHM receipt."""
        order = self._create_order(self.env_for(self.user_a), confirm=True)
        self.assertEqual(order.state, "purchase")
        receipt = order.picking_ids
        self.assertEqual(len(receipt), 1)
        self.assertEqual(receipt.branch_id, self.branch_ahm)
        self.assertEqual(receipt.picking_type_id, self.wh_ahm.in_type_id)
        self.assertEqual(receipt.move_ids.branch_id, self.branch_ahm)
        self.assertEqual(receipt.location_dest_id, self.wh_ahm.lot_stock_id)

        vals = order.order_line._prepare_stock_move_vals(
            self.env["stock.picking"], 40.0, 1.0, self.product.uom_id)
        self.assertEqual(vals["branch_id"], self.branch_ahm.id)

        # other branch user: no access
        env_b = self.env_for(self.user_b)
        self.assertFalse(env_b["stock.picking"].search([("id", "=", receipt.id)]))
        with self.assertRaises(AccessError):
            env_b["stock.picking"].browse(receipt.id).read(["name"])
        self.assertEqual(self.branch_ahm.with_user(self.user_a).purchase_receipt_count, 1)
        self.assertEqual(self.branch_ahm.with_user(self.user_b).purchase_receipt_count, 0)
        action = self.branch_ahm.action_view_purchase_receipts()
        self.assertEqual(self.env["stock.picking"].search(action["domain"]), receipt)

    def test_tc015_receipt_then_bill_keep_branch(self):
        env_multi = self.env_for(self.user_multi, branch=self.branch_ahm)
        order = self._create_order(env_multi, confirm=True, branch_id=self.branch_srt.id)
        receipt = order.picking_ids
        self.assertEqual(receipt.branch_id, self.branch_srt)
        self._receive(receipt)
        self.assertEqual(order.order_line.qty_received, 4.0)
        quant = self.env["stock.quant"].search([
            ("product_id", "=", self.product.id), ("location_id", "=", self.wh_srt.lot_stock_id.id)])
        self.assertEqual(quant.quantity, 4.0)
        self.assertEqual(quant.branch_id, self.branch_srt)

        order.action_create_invoice()
        bill = order.invoice_ids
        self.assertEqual(len(bill), 1)
        self.assertEqual(bill.branch_id, self.branch_srt)
        self.assertEqual(bill.invoice_line_ids.quantity, 4.0)

        # return to vendor keeps the branch too
        return_picking = receipt._create_return()
        self.assertEqual(return_picking.branch_id, self.branch_srt)
        self.assertEqual(return_picking.move_ids.branch_id, self.branch_srt)

    def test_replenishment_order_in_warehouse_branch(self):
        """A buy rule of the AHM warehouse creates an AHM order, whatever the
        working branch of the user running the scheduler."""
        self.env["product.supplierinfo"].create({
            "partner_id": self.vendor.id,
            "product_tmpl_id": self.product.product_tmpl_id.id,
            "price": 40.0,
        })
        # "Buy" is a warehouse route (buy_to_resupply) of every warehouse
        self.assertTrue(self.wh_ahm.buy_pull_id)
        self.assertEqual(self.wh_ahm.buy_pull_id.picking_type_id, self.wh_ahm.in_type_id)
        env_srt = self.env_for(self.user_multi, branch=self.branch_srt)
        Rule = env_srt["stock.rule"].sudo()  # like the scheduler
        Rule.run([Rule.Procurement(
            self.product, 6.0, self.product.uom_id, self.wh_ahm.lot_stock_id,
            "replenish", "REPL-AHM", self.company_a, {
                "warehouse_id": self.wh_ahm,
                "date_planned": fields.Datetime.now() + timedelta(days=5),
            },
        )])
        order = self.env["purchase.order"].search([("origin", "=", "REPL-AHM")])
        self.assertEqual(len(order), 1)
        self.assertEqual(order.branch_id, self.branch_ahm)
        self.assertEqual(order.picking_type_id, self.wh_ahm.in_type_id)

        # an SRT procurement never lands in the AHM RFQ
        Rule.run([Rule.Procurement(
            self.product, 2.0, self.product.uom_id, self.wh_srt.lot_stock_id,
            "replenish", "REPL-SRT", self.company_a, {
                "warehouse_id": self.wh_srt,
                "date_planned": fields.Datetime.now() + timedelta(days=5),
            },
        )])
        order_srt = self.env["purchase.order"].search([("origin", "=", "REPL-SRT")])
        self.assertEqual(order_srt.branch_id, self.branch_srt)
        self.assertNotEqual(order_srt, order)
