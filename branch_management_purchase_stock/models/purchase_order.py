import logging

from odoo import api, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    # ------------------------------------------------------------------
    # Operation type (Deliver To) of the branch
    # ------------------------------------------------------------------

    @api.model
    def _get_branch_picking_type(self, branch):
        """Receipt operation type of ``branch``: the one of its default
        warehouse, else of a warehouse shared by the company (no branch)."""
        if not branch:
            return self.env["stock.picking.type"]
        warehouse = branch._get_default_warehouse(company_fallback=True)
        return warehouse.in_type_id.filtered("active")

    @api.model
    def _get_default_branch_for_company(self, company):
        """Branch a new order of ``company`` gets when none is given."""
        branch_id = self.env.context.get("default_branch_id")
        branch = self.env["res.branch"].browse(branch_id) if branch_id else self.env["res.branch"]
        if branch.company_id != company:
            branch = self.with_company(company)._default_branch_id()
        return branch

    @api.model
    def _get_picking_type(self, company_id):
        # default value of picking_type_id and company onchange (purchase_stock)
        company = self.env["res.company"].browse(company_id)
        branch = self._get_default_branch_for_company(company)
        return self._get_branch_picking_type(branch) or super()._get_picking_type(company_id)

    @api.model_create_multi
    def create(self, vals_list):
        PickingType = self.env["stock.picking.type"]
        for vals in vals_list:
            picking_type_id = vals.get("picking_type_id") or self.env.context.get("default_picking_type_id")
            if picking_type_id:
                # e.g. replenishment: the warehouse to resupply decides the branch
                picking_type = PickingType.browse(picking_type_id)
                if "branch_id" not in vals and picking_type.branch_id:
                    vals["branch_id"] = picking_type.branch_id.id
                continue
            if "branch_id" in vals:
                branch = self.env["res.branch"].browse(vals["branch_id"])
            else:
                company = self.env["res.company"].browse(
                    vals.get("company_id") or self.default_get(["company_id"]).get("company_id")
                )
                branch = self._get_default_branch_for_company(company)
            picking_type = self._get_branch_picking_type(branch)
            if picking_type:
                vals["picking_type_id"] = picking_type.id
        return super().create(vals_list)

    @api.onchange("branch_id")
    def _onchange_branch_id_picking_type(self):
        picking_type = self.picking_type_id
        if not self.branch_id or picking_type.branch_id == self.branch_id:
            return
        # keep a dropship (or other operation type without warehouse branch)
        # chosen by the user; replace receipts of another branch or shared
        # receipts when the branch has its own warehouse
        if picking_type.branch_id or picking_type.code == "incoming" or not picking_type:
            branch_type = self._get_branch_picking_type(self.branch_id)
            if branch_type:
                self.picking_type_id = branch_type

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    @api.constrains("branch_id", "picking_type_id")
    def _check_picking_type_branch(self):
        for order in self:
            type_branch = order.picking_type_id.branch_id
            if order.branch_id and type_branch and type_branch != order.branch_id:
                _logger.info(
                    "Branch mismatch on purchase order %s: branch %s vs operation type branch %s",
                    order.id, order.branch_id.id, type_branch.id,
                )
                raise ValidationError(self.env._(
                    "Purchase order %(order)s belongs to branch %(branch)s but is received with "
                    "operation type %(type)s of branch %(type_branch)s. Choose an operation type "
                    "of the order's branch (or of a warehouse shared by all branches).",
                    order=order.display_name,
                    branch=order.branch_id.display_name,
                    type=order.picking_type_id.display_name,
                    type_branch=type_branch.display_name,
                ))
