from odoo import fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged

from .common import StockBranchCommon


@tagged("post_install", "-at_install", "branch_management")
class TestStockBranch(StockBranchCommon):

    def test_warehouse_branch_propagation(self):
        wh = self.wh_ahm
        self.assertEqual(wh.branch_id, self.branch_ahm)
        for picking_type in (wh.in_type_id, wh.out_type_id, wh.int_type_id):
            self.assertEqual(picking_type.branch_id, self.branch_ahm)
        for location in (wh.view_location_id, wh.lot_stock_id):
            self.assertEqual(location.branch_id, self.branch_ahm)
        self.assertIn(wh, self.branch_ahm.warehouse_ids)
        self.assertEqual(self.branch_ahm.warehouse_count, 1)
        self.assertFalse(self.supplier_location.branch_id)
        self.assertFalse(self.wh_company_a.branch_id,
                         "the warehouse created with the company has no branch")
        action = self.branch_ahm.action_view_warehouses()
        self.assertEqual(self.env["stock.warehouse"].search(action["domain"]), wh)

    def test_sublocation_gets_branch(self):
        shelf = self.env["stock.location"].create({
            "name": "Shelf 1", "location_id": self.wh_ahm.lot_stock_id.id,
        })
        self.assertEqual(shelf.branch_id, self.branch_ahm)

    def test_default_warehouse(self):
        self.assertEqual(self.branch_ahm._get_default_warehouse(), self.wh_ahm)
        wh_ahm2 = self.env["stock.warehouse"].with_company(self.company_a).create({
            "name": "Ahmedabad Warehouse 2", "code": "WAH2",
            "company_id": self.company_a.id, "branch_id": self.branch_ahm.id,
        })
        self.assertEqual(self.branch_ahm.warehouse_count, 2, "a branch may own several warehouses")
        self.branch_ahm.default_warehouse_id = wh_ahm2
        self.assertEqual(self.branch_ahm._get_default_warehouse(), wh_ahm2)
        self.assertFalse(self.branch_guj._get_default_warehouse())
        self.assertEqual(
            self.branch_guj._get_default_warehouse(company_fallback=True), self.wh_company_a)
        with self.assertRaises(ValidationError):
            self.branch_ahm.default_warehouse_id = self.wh_srt

    def test_warehouse_branch_company(self):
        with self.assertRaises(ValidationError):
            self.env["stock.warehouse"].with_company(self.company_a).create({
                "name": "Wrong", "code": "WRNG",
                "company_id": self.company_a.id, "branch_id": self.branch_mum.id,
            })
        with self.assertRaises(ValidationError):
            self.wh_ahm.branch_id = self.branch_pun

    def test_new_company_warehouse(self):
        company = self.env["res.company"].create({"name": "Branch Stock New Co"})
        warehouse = self.env["stock.warehouse"].search([("company_id", "=", company.id)])
        self.assertTrue(warehouse)
        self.assertFalse(warehouse.branch_id)

    def test_warehouse_default_branch_for_user(self):
        env = self.env_for(self.manager, branch=self.branch_srt)
        self.manager.group_ids = [(4, self.env.ref("stock.group_stock_manager").id)]
        warehouse = env["stock.warehouse"].create({
            "name": "Surat 2", "code": "WSR2", "company_id": self.company_a.id,
        })
        self.assertEqual(warehouse.branch_id, self.branch_srt)

    def test_receipt_and_delivery_branch(self):
        env = self.env_for(self.user_a, branch=self.branch_ahm)
        receipt = self._create_picking(
            env, self.wh_ahm.in_type_id, self.supplier_location, self.wh_ahm.lot_stock_id)
        self.assertEqual(receipt.branch_id, self.branch_ahm)
        self.assertEqual(receipt.move_ids.branch_id, self.branch_ahm)
        self.assertFalse(receipt.is_cross_branch)
        receipt.button_validate()
        self.assertEqual(receipt.state, "done")
        self.assertEqual(receipt.move_ids.move_line_ids.branch_id, self.branch_ahm)
        quant = self.env["stock.quant"].search([
            ("product_id", "=", self.product.id), ("location_id", "=", self.wh_ahm.lot_stock_id.id),
        ])
        self.assertEqual(quant.branch_id, self.branch_ahm)
        self.assertEqual(quant.quantity, 5.0)

        delivery = self._create_picking(
            env, self.wh_ahm.out_type_id, self.wh_ahm.lot_stock_id, self.customer_location, qty=3.0)
        self.assertEqual(delivery.branch_id, self.branch_ahm)
        delivery.action_confirm()
        delivery.action_assign()
        self.assertEqual(delivery.move_ids.move_line_ids.branch_id, self.branch_ahm)
        delivery.button_validate()
        self.assertEqual(delivery.state, "done")
        self.assertEqual(delivery.move_ids.branch_id, self.branch_ahm)
        # branch-level reporting: group moves by branch
        groups = self.env["stock.move"]._read_group(
            [("product_id", "=", self.product.id)], ["branch_id"], ["product_uom_qty:sum"])
        self.assertEqual(groups, [(self.branch_ahm, 8.0)])

    def test_backorder_keeps_branch(self):
        self._add_stock(self.wh_srt.lot_stock_id, 2.0)
        env = self.env_for(self.user_b, branch=self.branch_srt)
        delivery = self._create_picking(
            env, self.wh_srt.out_type_id, self.wh_srt.lot_stock_id, self.customer_location, qty=5.0)
        delivery.action_confirm()
        delivery.action_assign()
        delivery.move_ids.picked = True
        delivery.with_context(skip_backorder=True).button_validate()
        self.assertEqual(delivery.state, "done")
        backorder = delivery.backorder_ids
        self.assertTrue(backorder)
        self.assertEqual(backorder.branch_id, self.branch_srt)
        self.assertEqual(backorder.move_ids.branch_id, self.branch_srt)

    def test_moves_assigned_to_branch_picking(self):
        """Moves confirmed without transfer get a transfer of their branch."""
        move = self.env["stock.move"].create({
            "product_id": self.product.id,
            "product_uom_qty": 1.0,
            "picking_type_id": self.wh_srt.out_type_id.id,
            "location_id": self.wh_srt.lot_stock_id.id,
            "location_dest_id": self.customer_location.id,
        })
        self.assertEqual(move.branch_id, self.branch_srt)
        move._action_confirm()
        self.assertTrue(move.picking_id)
        self.assertEqual(move.picking_id.branch_id, self.branch_srt)

    def test_procurement_branch(self):
        """The branch of the rule's warehouse wins; the procurement's branch is
        used for warehouses without branch (bridge modules pass it)."""
        StockRule = self.env["stock.rule"]
        uom = self.product.uom_id
        StockRule.run([StockRule.Procurement(
            self.product, 2.0, uom, self.customer_location, "branch", "BR-PROC-1",
            self.company_a, {"warehouse_id": self.wh_company_a, "branch_id": self.branch_ahm},
        )])
        move = self.env["stock.move"].search([("origin", "=", "BR-PROC-1")])
        self.assertEqual(move.branch_id, self.branch_ahm)
        self.assertEqual(move.picking_id.branch_id, self.branch_ahm)

        StockRule.run([StockRule.Procurement(
            self.product, 2.0, uom, self.customer_location, "branch", "BR-PROC-2",
            self.company_a, {"warehouse_id": self.wh_srt, "branch_id": self.branch_ahm,
                             "date_planned": fields.Datetime.now()},
        )])
        move = self.env["stock.move"].search([("origin", "=", "BR-PROC-2")])
        self.assertEqual(move.branch_id, self.branch_srt)
        self.assertEqual(move.picking_id.branch_id, self.branch_srt)
        # transfers of different branches are never merged
        self.assertNotEqual(
            self.env["stock.move"].search([("origin", "=", "BR-PROC-1")]).picking_id, move.picking_id)

    def test_tc017_picking_type_branch_mismatch(self):
        """TC-017: the branch of a transfer must match its operation type."""
        env = self.env_for(self.user_multi, branch=self.branch_ahm)
        with self.assertRaises(ValidationError):
            self._create_picking(
                env, self.wh_ahm.int_type_id, self.wh_ahm.lot_stock_id, self.wh_ahm.lot_stock_id,
                branch_id=self.branch_srt.id)
        picking = self._create_picking(
            env, self.wh_ahm.int_type_id, self.wh_ahm.lot_stock_id, self.wh_ahm.lot_stock_id)
        with self.assertRaises(ValidationError):
            picking.branch_id = self.branch_srt
        # branch of a warehouse without branch: free choice, kept on copy
        free = self._create_picking(
            env, self.wh_company_a.int_type_id, self.wh_company_a.lot_stock_id,
            self.wh_company_a.lot_stock_id, branch_id=self.branch_srt.id)
        self.assertEqual(free.branch_id, self.branch_srt)
        self.assertEqual(free.copy().branch_id, self.branch_srt)

    def test_tc017_user_cannot_use_foreign_branch(self):
        """TC-017: a user cannot create a transfer in a branch they are not allowed in."""
        env = self.env_for(self.user_a, branch=self.branch_ahm)
        # refused by the branch validation or by the branch security boundary
        with self.assertRaises((ValidationError, AccessError)):
            self._create_picking(
                env, self.wh_srt.int_type_id, self.wh_srt.lot_stock_id, self.wh_srt.lot_stock_id)
        with self.assertRaises((ValidationError, AccessError)):
            self._create_picking(
                env, self.wh_company_a.int_type_id, self.wh_company_a.lot_stock_id,
                self.wh_company_a.lot_stock_id, branch_id=self.branch_srt.id)
        # interactive creation on a warehouse without branch: working branch
        picking = self._create_picking(
            env, self.wh_company_a.int_type_id, self.wh_company_a.lot_stock_id,
            self.wh_company_a.lot_stock_id)
        self.assertEqual(picking.branch_id, self.branch_ahm)

    def test_warehouse_branch_change_with_ongoing_transfers(self):
        picking = self._create_picking(
            self.env, self.wh_ahm.out_type_id, self.wh_ahm.lot_stock_id, self.customer_location)
        picking.action_confirm()
        with self.assertRaises(UserError):
            self.wh_ahm.branch_id = self.branch_srt
        picking.action_cancel()
        self.wh_ahm.branch_id = self.branch_srt
        self.assertEqual(self.wh_ahm.out_type_id.branch_id, self.branch_srt)
        self.assertEqual(self.wh_ahm.lot_stock_id.branch_id, self.branch_srt)
        self.assertEqual(picking.branch_id, self.branch_ahm,
                         "existing transfers keep their branch (history)")

    def test_reports_render(self):
        picking = self._create_picking(
            self.env, self.wh_ahm.out_type_id, self.wh_ahm.lot_stock_id, self.customer_location)
        self.branch_ahm.street = "Branch Street 1"
        html = self.env["ir.actions.report"]._render_qweb_html(
            "stock.action_report_delivery", picking.ids)[0]
        self.assertIn(b"o_branch_address_block", html)
        self.assertIn(b"Branch Street 1", html)
        # the picking operations report also prints a barcode (needs a
        # reportlab backend): only check the template inheritance
        arch = self.env.ref("stock.report_picking").get_combined_arch()
        self.assertIn("branch_management.branch_address_block", arch)
