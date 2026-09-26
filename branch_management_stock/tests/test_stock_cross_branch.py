from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import StockBranchCommon


@tagged("post_install", "-at_install", "branch_management")
class TestStockCrossBranch(StockBranchCommon):
    """TC-018: internal transfers between branches."""

    def _cross_transfer(self, env):
        self._add_stock(self.wh_ahm.lot_stock_id, 10.0)
        picking = self._create_picking(
            env, self.wh_ahm.int_type_id, self.wh_ahm.lot_stock_id, self.wh_srt.lot_stock_id, qty=4.0)
        picking.action_confirm()
        picking.action_assign()
        return picking

    def test_same_branch_internal_transfer(self):
        env = self.env_for(self.user_a, branch=self.branch_ahm)
        shelf = self.env["stock.location"].create({
            "name": "Shelf", "location_id": self.wh_ahm.lot_stock_id.id})
        self._add_stock(self.wh_ahm.lot_stock_id, 5.0)
        picking = self._create_picking(
            env, self.wh_ahm.int_type_id, self.wh_ahm.lot_stock_id, shelf, qty=2.0)
        self.assertFalse(picking.is_cross_branch)
        self.assertEqual(picking.dest_branch_id, self.branch_ahm)
        picking.button_validate()
        self.assertEqual(picking.state, "done")

    def test_cross_branch_blocked_by_default(self):
        env = self.env_for(self.user_a, branch=self.branch_ahm)
        picking = self._cross_transfer(env)
        self.assertTrue(picking.is_cross_branch)
        self.assertEqual(picking.branch_id, self.branch_ahm)
        self.assertEqual(picking.dest_branch_id, self.branch_srt)
        self.assertFalse(self.company_a.branch_allow_cross_transfer)
        with self.assertRaises(UserError):
            picking.button_validate()
        with self.assertRaises(UserError):
            picking._action_done()
        self.assertNotEqual(picking.state, "done")

    def test_cross_branch_allowed_when_enabled(self):
        self.company_a.branch_allow_cross_transfer = True
        env = self.env_for(self.user_a, branch=self.branch_ahm)
        picking = self._cross_transfer(env)
        picking.button_validate()
        self.assertEqual(picking.state, "done")
        self.assertTrue(picking.is_cross_branch)
        self.assertEqual(picking.branch_id, self.branch_ahm, "source branch")
        self.assertEqual(picking.dest_branch_id, self.branch_srt, "destination branch")
        self.assertEqual(picking.move_ids.branch_id, self.branch_ahm)
        self.assertEqual(picking.move_ids.dest_branch_id, self.branch_srt)
        quant = self.env["stock.quant"].search([
            ("product_id", "=", self.product.id), ("location_id", "=", self.wh_srt.lot_stock_id.id)])
        self.assertEqual(quant.quantity, 4.0)
        self.assertEqual(quant.branch_id, self.branch_srt)
        # the destination branch sees the incoming transfer, others do not
        env_b = self.env_for(self.user_b, branch=self.branch_srt)
        self.assertEqual(env_b["stock.picking"].search([("id", "=", picking.id)]), picking)
        self.assertEqual(
            env_b["stock.picking"].search([("is_cross_branch", "=", True)]), picking)
        env_none = self.env_for(self.user_none)
        self.assertFalse(env_none["stock.picking"].search([("id", "=", picking.id)]))

    def test_cross_branch_setting_in_settings(self):
        settings = self.env["res.config.settings"].with_company(self.company_a).create({})
        settings.branch_allow_cross_transfer = True
        settings.execute()
        self.assertTrue(self.company_a.branch_allow_cross_transfer)
