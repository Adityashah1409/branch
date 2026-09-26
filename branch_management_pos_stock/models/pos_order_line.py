from odoo import models


class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    def _prepare_procurement_values(self):
        # "ship later" orders go through procurements: stock.rule
        # (branch_management_stock) uses it when the rule's operation type has
        # no branch of its own
        values = super()._prepare_procurement_values()
        values["branch_id"] = self.order_id.branch_id
        return values
