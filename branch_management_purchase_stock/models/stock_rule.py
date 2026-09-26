from odoo import models


class StockRule(models.Model):
    _inherit = "stock.rule"

    def _get_purchase_branch(self, values):
        """Branch of the purchase order created / reused for a procurement:
        the branch of the rule's operation type (warehouse to resupply), else
        the ``branch_id`` procurement value (e.g. a dropshipped sale)."""
        branch = self.picking_type_id.branch_id
        if not branch and values.get("branch_id"):
            value = values["branch_id"]
            branch = value if isinstance(value, models.BaseModel) else self.env["res.branch"].browse(value)
        return branch

    def _prepare_purchase_order(self, company_id, origins, values):
        vals = super()._prepare_purchase_order(company_id, origins, values)
        branch = self._get_purchase_branch(values[0])
        if branch:
            vals["branch_id"] = branch.id
        return vals

    def _make_po_get_domain(self, company_id, values, partner):
        domain = super()._make_po_get_domain(company_id, values, partner)
        branch = self._get_purchase_branch(values)
        if branch:
            # never add a procurement to an RFQ of another branch
            domain += (("branch_id", "=", branch.id),)
        return domain
