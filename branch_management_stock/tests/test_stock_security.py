from odoo.exceptions import AccessError
from odoo.tests import tagged

from .common import StockBranchCommon


@tagged("post_install", "-at_install", "branch_management")
class TestStockBranchSecurity(StockBranchCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.picking_ahm = cls._create_picking_cls(cls.wh_ahm)
        cls.picking_srt = cls._create_picking_cls(cls.wh_srt)

    @classmethod
    def _create_picking_cls(cls, warehouse):
        return cls.env["stock.picking"].create({
            "picking_type_id": warehouse.out_type_id.id,
            "location_id": warehouse.lot_stock_id.id,
            "location_dest_id": cls.customer_location.id,
            "move_ids": [(0, 0, {
                "product_id": cls.product.id,
                "product_uom_qty": 1.0,
                "location_id": warehouse.lot_stock_id.id,
                "location_dest_id": cls.customer_location.id,
            })],
        })

    def test_user_sees_only_own_branch_pickings(self):
        env = self.env_for(self.user_a, branch=self.branch_ahm)
        Picking = env["stock.picking"]
        found = Picking.search([("id", "in", (self.picking_ahm | self.picking_srt).ids)])
        self.assertEqual(found, self.picking_ahm)
        self.assertEqual(Picking.search_count([("branch_id", "=", self.branch_srt.id)]), 0)
        with self.assertRaises(AccessError):
            Picking.browse(self.picking_srt.id).read(["name"])
        with self.assertRaises(AccessError):
            Picking.browse(self.picking_srt.id).write({"origin": "hack"})
        with self.assertRaises(AccessError):
            Picking.browse(self.picking_srt.id).unlink()
        # stock moves follow the same boundary
        Move = env["stock.move"]
        self.assertEqual(
            Move.search([("id", "in", (self.picking_ahm | self.picking_srt).move_ids.ids)]),
            self.picking_ahm.move_ids)
        with self.assertRaises(AccessError):
            Move.browse(self.picking_srt.move_ids.id).read(["product_uom_qty"])
        # but the user can work in their own branch
        Picking.browse(self.picking_ahm.id).write({"origin": "ok"})
        self.assertEqual(self.picking_ahm.origin, "ok")

    def test_multi_branch_and_admin(self):
        both = self.picking_ahm | self.picking_srt
        env = self.env_for(self.user_multi, branch=self.branch_ahm)
        self.assertEqual(env["stock.picking"].search([("id", "in", both.ids)]), both)
        env = self.env_for(self.branch_admin)
        self.assertEqual(env["stock.picking"].search([("id", "in", both.ids)]), both)
        env = self.env_for(self.user_none)
        self.assertFalse(env["stock.picking"].search([("id", "in", both.ids)]))

    def test_quants_and_warehouses_not_restricted(self):
        """Configuration and stock levels stay readable (reservation needs them)."""
        self._add_stock(self.wh_srt.lot_stock_id, 4.0)
        env = self.env_for(self.user_a, branch=self.branch_ahm)
        quant = env["stock.quant"].search([
            ("product_id", "=", self.product.id), ("location_id", "=", self.wh_srt.lot_stock_id.id)])
        self.assertEqual(quant.quantity, 4.0)
        self.assertTrue(env["stock.warehouse"].browse(self.wh_srt.id).read(["name"]))
        self.assertTrue(env["stock.picking.type"].browse(self.wh_srt.out_type_id.id).read(["name"]))

    def test_archived_branch_keeps_pickings_readable(self):
        self.branch_ahm.active = False
        env = self.env_for(self.user_a)
        picking = env["stock.picking"].browse(self.picking_ahm.id)
        self.assertEqual(picking.read(["name"])[0]["id"], self.picking_ahm.id)
        self.assertEqual(env["stock.picking"].search([("id", "=", self.picking_ahm.id)]), picking)
        self.assertEqual(picking.branch_id.with_context(active_test=False), self.branch_ahm)
