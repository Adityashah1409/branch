from odoo import Command

from odoo.addons.branch_management.tests.common import BranchTestCommon


class StockBranchCommon(BranchTestCommon):
    """Branch fixtures + one warehouse per branch (AHM, SRT in company A,
    MUM in company B) and a storable product. No demo data."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # work in company A by default (as the web client would)
        cls.env = cls.env(context=dict(
            cls.env.context, allowed_company_ids=[cls.company_a.id, cls.company_b.id]))
        stock_user = cls.env.ref("stock.group_stock_user")
        for user in (cls.user_a, cls.user_b, cls.user_multi, cls.user_none,
                     cls.manager, cls.branch_admin):
            user.group_ids = [Command.link(stock_user.id)]

        Warehouse = cls.env["stock.warehouse"]
        cls.wh_company_a = Warehouse.search([("company_id", "=", cls.company_a.id)], limit=1)
        cls.wh_ahm = Warehouse.with_company(cls.company_a).create({
            "name": "Ahmedabad Warehouse", "code": "WAHM",
            "company_id": cls.company_a.id, "branch_id": cls.branch_ahm.id,
        })
        cls.wh_srt = Warehouse.with_company(cls.company_a).create({
            "name": "Surat Warehouse", "code": "WSRT",
            "company_id": cls.company_a.id, "branch_id": cls.branch_srt.id,
        })
        cls.wh_mum = Warehouse.with_company(cls.company_b).create({
            "name": "Mumbai Warehouse", "code": "WMUM",
            "company_id": cls.company_b.id, "branch_id": cls.branch_mum.id,
        })
        cls.product = cls.env["product.product"].create({
            "name": "Branch Widget", "type": "consu", "is_storable": True,
        })
        cls.supplier_location = cls.env.ref("stock.stock_location_suppliers")
        cls.customer_location = cls.env.ref("stock.stock_location_customers")

    def _create_picking(self, env, picking_type, src, dest, qty=5.0, **values):
        return env["stock.picking"].create(dict({
            "picking_type_id": picking_type.id,
            "location_id": src.id,
            "location_dest_id": dest.id,
            "move_ids": [Command.create({
                "product_id": self.product.id,
                "product_uom_qty": qty,
                "location_id": src.id,
                "location_dest_id": dest.id,
            })],
        }, **values))

    def _add_stock(self, location, qty=10.0):
        self.env["stock.quant"]._update_available_quantity(self.product, location, qty)
