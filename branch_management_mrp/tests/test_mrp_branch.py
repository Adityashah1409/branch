from odoo import Command
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import tagged

from odoo.addons.branch_management_stock.tests.common import StockBranchCommon


@tagged("post_install", "-at_install", "branch_management")
class TestMrpBranch(StockBranchCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        mrp_user = cls.env.ref("mrp.group_mrp_user")
        for user in (cls.user_a, cls.user_b, cls.user_multi, cls.user_none, cls.branch_admin):
            user.group_ids = [Command.link(mrp_user.id)]
        cls.component = cls.env["product.product"].create({
            "name": "Branch Component", "type": "consu", "is_storable": True,
        })
        cls.finished = cls.env["product.product"].create({
            "name": "Branch Finished", "type": "consu", "is_storable": True,
        })
        cls.bom = cls.env["mrp.bom"].create({
            "product_tmpl_id": cls.finished.product_tmpl_id.id,
            "product_qty": 1.0,
            "type": "normal",
            "bom_line_ids": [Command.create({"product_id": cls.component.id, "product_qty": 2.0})],
        })

    def _create_mo(self, env, warehouse, qty=1.0, **values):
        return env["mrp.production"].create(dict({
            "product_id": self.finished.id,
            "bom_id": self.bom.id,
            "product_qty": qty,
            "picking_type_id": warehouse.manu_type_id.id,
        }, **values))

    def test_mo_branch_from_picking_type(self):
        self.assertEqual(self.wh_ahm.manu_type_id.branch_id, self.branch_ahm)
        env = self.env_for(self.user_a, branch=self.branch_ahm)
        mo = self._create_mo(env, self.wh_ahm)
        self.assertEqual(mo.branch_id, self.branch_ahm)
        self.assertEqual(mo.move_raw_ids.branch_id, self.branch_ahm)
        self.assertEqual(mo.move_finished_ids.branch_id, self.branch_ahm)

    def test_mo_done_moves_branch(self):
        self.env["stock.quant"]._update_available_quantity(
            self.component, self.wh_srt.lot_stock_id, 10.0)
        env = self.env_for(self.user_b, branch=self.branch_srt)
        mo = self._create_mo(env, self.wh_srt, qty=2.0)
        mo.action_confirm()
        mo.action_assign()
        mo.qty_producing = 2.0
        mo.move_raw_ids.picked = True
        mo.button_mark_done()
        self.assertEqual(mo.state, "done")
        moves = mo.move_raw_ids | mo.move_finished_ids
        self.assertEqual(moves.branch_id, self.branch_srt)
        self.assertEqual(moves.move_line_ids.branch_id, self.branch_srt)
        quant = self.env["stock.quant"].search([
            ("product_id", "=", self.finished.id), ("location_id", "=", self.wh_srt.lot_stock_id.id)])
        self.assertEqual(quant.branch_id, self.branch_srt)
        self.assertEqual(quant.quantity, 2.0)
        # unbuild from the MO: same branch, moves too
        unbuild = env["mrp.unbuild"].create({
            "mo_id": mo.id, "product_id": self.finished.id, "product_qty": 1.0,
        })
        self.assertEqual(unbuild.branch_id, self.branch_srt)
        unbuild.action_unbuild()
        self.assertEqual(
            (unbuild.produce_line_ids | unbuild.consume_line_ids).branch_id, self.branch_srt)

    def test_mo_branch_mismatch_and_foreign_branch(self):
        env = self.env_for(self.user_multi, branch=self.branch_ahm)
        with self.assertRaises(ValidationError):
            self._create_mo(env, self.wh_ahm, branch_id=self.branch_srt.id)
        env = self.env_for(self.user_a, branch=self.branch_ahm)
        with self.assertRaises((ValidationError, AccessError)):
            self._create_mo(env, self.wh_srt)

    def test_mo_security(self):
        mo_ahm = self._create_mo(self.env, self.wh_ahm)
        mo_srt = self._create_mo(self.env, self.wh_srt)
        both = mo_ahm | mo_srt
        env = self.env_for(self.user_a, branch=self.branch_ahm)
        Production = env["mrp.production"]
        self.assertEqual(Production.search([("id", "in", both.ids)]), mo_ahm)
        with self.assertRaises(AccessError):
            Production.browse(mo_srt.id).read(["name"])
        with self.assertRaises(AccessError):
            env["stock.move"].browse(mo_srt.move_raw_ids.ids).read(["product_id"])
        env = self.env_for(self.user_multi, branch=self.branch_ahm)
        self.assertEqual(env["mrp.production"].search([("id", "in", both.ids)]), both)
        # smart button counts only what the user can see
        branch = self.env_for(self.user_a)["res.branch"].browse(self.branch_ahm.id)
        self.assertEqual(branch.production_count, 1)
        action = self.branch_srt.action_view_productions()
        self.assertEqual(self.env["mrp.production"].search(action["domain"]), mo_srt)

    def test_procurement_mo_branch(self):
        """An MO created by a procurement gets the branch of its warehouse."""
        route = self.wh_ahm.manufacture_pull_id.route_id
        StockRule = self.env["stock.rule"]
        StockRule.run([StockRule.Procurement(
            self.finished, 1.0, self.finished.uom_id, self.wh_ahm.lot_stock_id, "branch",
            "BR-MO-1", self.company_a, {"warehouse_id": self.wh_ahm, "route_ids": route},
        )])
        mo = self.env["mrp.production"].search([("origin", "=", "BR-MO-1")])
        self.assertEqual(mo.branch_id, self.branch_ahm)
        self.assertEqual(mo.move_raw_ids.branch_id, self.branch_ahm)

    def test_report_branch_block(self):
        arch = self.env.ref("mrp.report_mrporder").get_combined_arch()
        self.assertIn("branch_management.branch_address_block", arch)
