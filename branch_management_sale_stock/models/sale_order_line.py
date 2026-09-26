from odoo import models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _prepare_procurement_values(self):
        # stock.rule._get_stock_move_values (branch_management_stock) uses it
        # when the operation type of the rule has no branch of its own
        values = super()._prepare_procurement_values()
        values["branch_id"] = self.order_id.branch_id
        return values
