from odoo import models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    def _prepare_stock_move_vals(self, picking, price_unit, product_uom_qty, product_uom):
        # the branch of the operation type's warehouse still wins in
        # stock.move._compute_branch_id; the order's branch covers operation
        # types without branch (e.g. dropship)
        vals = super()._prepare_stock_move_vals(picking, price_unit, product_uom_qty, product_uom)
        vals["branch_id"] = self.order_id.branch_id.id
        return vals
