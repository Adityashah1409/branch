from odoo import models


class StockRule(models.Model):
    _inherit = "stock.rule"

    def _get_procurement_branch(self, picking_type, values):
        """Branch of the order created by a procurement: the branch of the
        operation type's warehouse, else the ``branch_id`` procurement value."""
        branch = picking_type.warehouse_id.branch_id
        if not branch and values.get("branch_id"):
            value = values["branch_id"]
            branch = self.env["res.branch"].browse(
                value.id if isinstance(value, models.BaseModel) else value)
        return branch

    def _prepare_mo_vals(self, product_id, product_qty, product_uom, location_dest_id, name, origin,
                         company_id, values, bom):
        mo_values = super()._prepare_mo_vals(
            product_id, product_qty, product_uom, location_dest_id, name, origin, company_id, values, bom)
        picking_type = self.env["stock.picking.type"].browse(mo_values.get("picking_type_id"))
        branch = self._get_procurement_branch(picking_type, values)
        if branch:
            mo_values["branch_id"] = branch.id
        return mo_values

    def _make_mo_get_domain(self, procurement, bom):
        domain = super()._make_mo_get_domain(procurement, bom)
        picking_type = bom.picking_type_id or self.picking_type_id  # as in _prepare_mo_vals
        branch = self._get_procurement_branch(picking_type, procurement.values)
        # never add the need of a branch to the order of another branch
        return domain + (("branch_id", "=", branch.id or False),)
