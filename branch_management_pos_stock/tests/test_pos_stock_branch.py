from odoo.exceptions import AccessError, ValidationError
from odoo.tests import Form, tagged

from odoo.addons.branch_management_pos.tests.common import PosBranchCommon
from odoo.addons.branch_management_stock.tests.common import StockBranchCommon


@tagged("post_install", "-at_install", "branch_management")
class TestPosStockBranch(PosBranchCommon, StockBranchCommon):
    """PoS pickings keep the shop's branch."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pos_product.is_storable = True
        cls.company_a.point_of_sale_update_stock_quantities = "real"
        for warehouse in (cls.wh_ahm, cls.wh_srt):
            cls.env["stock.quant"]._update_available_quantity(
                cls.pos_product, warehouse.lot_stock_id, 20.0)

    def test_config_picking_type_follows_branch(self):
        self.assertEqual(self.config_ahm.picking_type_id, self.wh_ahm.pos_type_id)
        self.assertEqual(self.config_ahm.warehouse_id, self.wh_ahm)
        self.assertEqual(self.config_srt.picking_type_id, self.wh_srt.pos_type_id)
        # a branch without warehouse uses the warehouse shared by the company
        config_guj = self._create_config("Gujarat Shop", self.branch_guj)
        self.assertFalse(config_guj.picking_type_id.branch_id)
        self.assertEqual(config_guj.warehouse_id, self.wh_company_a)
        # a shop created for an operation type gets its branch
        config = self._create_config("Typed Shop", None, picking_type_id=self.wh_srt.pos_type_id.id)
        self.assertEqual(config.branch_id, self.branch_srt)

        # branch change in the PoS settings (onchange), saved on the shop
        with Form(self.env["res.config.settings"].with_company(self.company_a)) as settings:
            settings.pos_config_id = config_guj
            settings.pos_branch_id = self.branch_ahm
            self.assertEqual(settings.pos_picking_type_id, self.wh_ahm.pos_type_id)
        self.assertEqual(config_guj.branch_id, self.branch_ahm)
        self.assertEqual(config_guj.picking_type_id, self.wh_ahm.pos_type_id)
        self.assertEqual(config_guj.warehouse_id, self.wh_ahm)
        # same onchange on the shop itself
        config_new = self.env["pos.config"].new({
            "branch_id": self.branch_srt.id, "picking_type_id": self.wh_ahm.pos_type_id.id,
        })
        config_new._onchange_branch_id_picking_type()
        self.assertEqual(config_new.picking_type_id, self.wh_srt.pos_type_id)

        with self.assertRaises(ValidationError):
            self.config_ahm.picking_type_id = self.wh_srt.pos_type_id

    def test_realtime_picking_keeps_shop_branch(self):
        session = self._open_session(self.config_ahm, self.user_a)
        order = self._create_order(session, qty=2.0)
        picking = order.picking_ids
        self.assertEqual(len(picking), 1)
        self.assertEqual(picking.state, "done")
        self.assertEqual(picking.branch_id, self.branch_ahm)
        self.assertEqual(picking.move_ids.branch_id, self.branch_ahm)
        self.assertEqual(picking.location_id, self.wh_ahm.lot_stock_id)
        self.assertEqual(picking.picking_type_id, self.wh_ahm.pos_type_id)

        env_b = self.env_for(self.user_b)
        self.assertFalse(env_b["stock.picking"].search([("id", "=", picking.id)]))
        with self.assertRaises(AccessError):
            env_b["stock.picking"].browse(picking.id).read(["name"])

    def test_closing_picking_keeps_shop_branch(self):
        self.company_a.point_of_sale_update_stock_quantities = "closing"
        session = self._open_session(self.config_ahm, self.user_a)
        self.assertTrue(session.update_stock_at_closing)
        self._create_order(session, qty=3.0)
        self.assertFalse(session.picking_ids)
        closer = session.with_user(self.user_multi).with_context(
            current_branch_id=self.branch_srt.id, allowed_company_ids=self.company_a.ids)
        self._close_session(closer)
        picking = session.picking_ids
        self.assertEqual(len(picking), 1)
        self.assertEqual(picking.branch_id, self.branch_ahm)
        self.assertEqual(picking.move_ids.branch_id, self.branch_ahm)

    def test_shared_warehouse_picking_gets_shop_branch(self):
        # Gujarat has no warehouse: its shop delivers from the shared
        # warehouse, the picking still belongs to Gujarat (not to the
        # working branch of the cashier)
        self.env["stock.quant"]._update_available_quantity(
            self.pos_product, self.wh_company_a.lot_stock_id, 20.0)
        config_guj = self._create_config("Gujarat Shop", self.branch_guj)
        cashier = self.branch_admin
        session = self._open_session(config_guj, cashier)
        order = self._create_order(session)
        self.assertEqual(order.branch_id, self.branch_guj)
        self.assertEqual(order.picking_ids.branch_id, self.branch_guj)
        self.assertEqual(order.picking_ids.move_ids.branch_id, self.branch_guj)
        values = order.lines._prepare_procurement_values()
        self.assertEqual(values["branch_id"], self.branch_guj)
