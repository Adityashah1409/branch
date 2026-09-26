from odoo import Command
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import Form, tagged

from odoo.addons.branch_management_account.tests.common import BranchAccountTestCommon
from odoo.addons.branch_management_stock.tests.common import StockBranchCommon


@tagged("post_install", "-at_install", "branch_management")
class TestSaleStockBranch(BranchAccountTestCommon, StockBranchCommon):
    """Sale -> Delivery keeps the branch (TC-013)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._add_groups(
            cls.user_a | cls.user_b | cls.user_multi | cls.manager | cls.branch_admin,
            "sales_team.group_sale_salesman_all_leads",
        )
        cls.product.write({
            "list_price": 100.0, "invoice_policy": "delivery", "taxes_id": [Command.clear()],
        })

    def _create_order(self, env, confirm=False, **values):
        order = env["sale.order"].create({
            "partner_id": self.partner.id,
            "order_line": [Command.create({
                "product_id": self.product.id, "product_uom_qty": 3.0,
                "price_unit": 100.0, "tax_ids": [Command.clear()],
            })],
            **values,
        })
        if confirm:
            order.action_confirm()
        return order

    def _deliver(self, picking):
        self._add_stock(picking.location_id, 10.0)
        picking.action_assign()
        picking.move_ids.picked = True
        picking.button_validate()
        self.assertEqual(picking.state, "done")

    # ------------------------------------------------------------------
    # Warehouse of the order
    # ------------------------------------------------------------------

    def test_order_warehouse_follows_branch(self):
        env_multi = self.env_for(self.user_multi, branch=self.branch_ahm)
        order = self._create_order(env_multi)
        self.assertEqual(order.branch_id, self.branch_ahm)
        self.assertEqual(order.warehouse_id, self.wh_ahm)

        # switching the branch of a quotation switches its warehouse
        order.branch_id = self.branch_srt
        self.assertEqual(order.warehouse_id, self.wh_srt)
        self.assertEqual(order.order_line.warehouse_id, self.wh_srt)

        # same in the form view (onchange)
        with Form(order) as form:
            form.branch_id = self.branch_ahm
            self.assertEqual(form.warehouse_id, self.wh_ahm)
        self.assertEqual(order.warehouse_id, self.wh_ahm)

        # the branch's default warehouse is used
        wh_ahm2 = self.env["stock.warehouse"].create({
            "name": "Ahmedabad Warehouse 2", "code": "WAH2",
            "company_id": self.company_a.id, "branch_id": self.branch_ahm.id,
        })
        self.branch_ahm.default_warehouse_id = wh_ahm2
        order_2 = self._create_order(env_multi)
        self.assertEqual(order_2.warehouse_id, wh_ahm2)

    def test_order_of_branch_without_warehouse(self):
        # Gujarat has no warehouse: the company warehouse shared by all
        # branches is used, never the warehouse of another branch
        order = self._create_order(self.env, branch_id=self.branch_guj.id)
        self.assertFalse(order.warehouse_id.branch_id)
        self.assertEqual(order.warehouse_id.company_id, self.company_a)

    def test_mismatched_warehouse_rejected(self):
        env_a = self.env_for(self.user_a)
        with self.assertRaises(ValidationError):
            self._create_order(env_a, warehouse_id=self.wh_srt.id)
        order = self._create_order(env_a)
        with self.assertRaises(ValidationError):
            order.warehouse_id = self.wh_srt
        # a warehouse shared by all branches is accepted
        order.warehouse_id = self.wh_company_a
        self.assertEqual(order.warehouse_id, self.wh_company_a)

        # a confirmed order cannot move to another branch than its warehouse's
        env_multi = self.env_for(self.user_multi, branch=self.branch_ahm)
        confirmed = self._create_order(env_multi, confirm=True)
        with self.assertRaises(ValidationError):
            confirmed.branch_id = self.branch_srt

    # ------------------------------------------------------------------
    # Sale -> Delivery (TC-013)
    # ------------------------------------------------------------------

    def test_tc013_delivery_keeps_order_branch(self):
        """TC-013: confirming an order of branch AHM creates an AHM delivery."""
        order = self._create_order(self.env_for(self.user_a), confirm=True)
        self.assertEqual(order.state, "sale")
        self.assertEqual(order.warehouse_id, self.wh_ahm)
        delivery = order.picking_ids
        self.assertEqual(len(delivery), 1)
        self.assertEqual(delivery.branch_id, self.branch_ahm)
        self.assertEqual(delivery.picking_type_id, self.wh_ahm.out_type_id)
        self.assertEqual(delivery.move_ids.branch_id, self.branch_ahm)
        self.assertEqual(delivery.location_id, self.wh_ahm.lot_stock_id)

        # the SRT user (other branch) cannot see the AHM delivery
        env_b = self.env_for(self.user_b)
        self.assertFalse(env_b["stock.picking"].search([("id", "=", delivery.id)]))
        self.assertFalse(env_b["stock.move"].search([("id", "in", delivery.move_ids.ids)]))
        with self.assertRaises(AccessError):
            env_b["stock.picking"].browse(delivery.id).read(["name"])

        # the branch smart button counts it
        self.assertEqual(self.branch_ahm.with_user(self.user_a).sale_delivery_count, 1)
        self.assertEqual(self.branch_ahm.with_user(self.user_b).sale_delivery_count, 0)
        action = self.branch_ahm.action_view_sale_deliveries()
        self.assertEqual(self.env["stock.picking"].search(action["domain"]), delivery)

    def test_tc013_order_branch_wins_over_working_branch(self):
        env_multi = self.env_for(self.user_multi, branch=self.branch_ahm)
        order = self._create_order(env_multi, confirm=True, branch_id=self.branch_srt.id)
        self.assertEqual(order.warehouse_id, self.wh_srt)
        self.assertEqual(order.picking_ids.branch_id, self.branch_srt)
        self.assertEqual(order.picking_ids.move_ids.branch_id, self.branch_srt)

    def test_procurement_values_carry_branch(self):
        order = self._create_order(self.env_for(self.user_a))
        values = order.order_line._prepare_procurement_values()
        self.assertEqual(values["branch_id"], self.branch_ahm)

    def test_delivery_from_shared_warehouse_keeps_order_branch(self):
        # the shared warehouse has no branch: the procurement value decides
        order = self._create_order(
            self.env, confirm=True, branch_id=self.branch_guj.id, warehouse_id=self.wh_company_a.id)
        self.assertEqual(order.picking_ids.branch_id, self.branch_guj)
        self.assertEqual(order.picking_ids.move_ids.branch_id, self.branch_guj)

    def test_return_and_invoice_keep_branch(self):
        env_a = self.env_for(self.user_a)
        order = self._create_order(env_a, confirm=True)
        delivery = order.picking_ids
        self._deliver(delivery)
        self.assertEqual(order.order_line.qty_delivered, 3.0)

        # invoice after delivery
        invoice = order._create_invoices()
        self.assertEqual(invoice.branch_id, self.branch_ahm)
        self.assertEqual(invoice.invoice_line_ids.quantity, 3.0)

        # return
        return_picking = delivery._create_return()
        self.assertEqual(return_picking.branch_id, self.branch_ahm)
        self.assertEqual(return_picking.move_ids.branch_id, self.branch_ahm)
        self.assertEqual(return_picking.picking_type_id.warehouse_id, self.wh_ahm)
        self._deliver_return(return_picking)
        self.assertEqual(order.order_line.qty_delivered, 0.0)
        self.assertEqual(order.picking_ids, delivery | return_picking)

    def _deliver_return(self, picking):
        picking.action_confirm()
        picking.action_assign()
        picking.move_ids.quantity = 3.0
        picking.move_ids.picked = True
        picking.button_validate()
        self.assertEqual(picking.state, "done")
