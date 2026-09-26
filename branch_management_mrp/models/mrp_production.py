import logging

from odoo import api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    _name = "mrp.production"
    _inherit = ["mrp.production", "res.branch.mixin"]

    # Branch -> Warehouse -> Manufacturing operation type
    branch_id = fields.Many2one(
        compute="_compute_branch_id",
        store=True,
        readonly=False,
        precompute=True,
        compute_sudo=False,  # the fallback on the working branch needs the real user
        default=None,
        copy=False,
        tracking=True,
    )

    @api.depends("picking_type_id")
    def _compute_branch_id(self):
        for production in self:
            type_branch = production.picking_type_id.warehouse_id.branch_id
            if type_branch:
                production.branch_id = type_branch
            elif not production.branch_id and not self.env.su and production.company_id:
                production.branch_id = self.env.user._get_current_branch(production.company_id)

    @api.constrains("branch_id", "picking_type_id")
    def _check_picking_type_branch(self):
        for production in self:
            type_branch = production.picking_type_id.warehouse_id.branch_id
            if production.branch_id and type_branch and production.branch_id != type_branch:
                _logger.info(
                    "Branch mismatch on manufacturing order %s: branch %s vs operation type branch %s",
                    production.id, production.branch_id.id, type_branch.id,
                )
                raise ValidationError(self.env._(
                    "The branch %(branch)s of manufacturing order %(production)s does not match "
                    "the branch %(type_branch)s of its operation type %(type)s.",
                    branch=production.branch_id.display_name,
                    production=production.display_name,
                    type_branch=type_branch.display_name,
                    type=production.picking_type_id.display_name,
                ))

    def copy_data(self, default=None):
        vals_list = super().copy_data(default=default)
        default = default or {}
        for production, vals in zip(self, vals_list):
            if "branch_id" in default:
                continue
            picking_type = self.env["stock.picking.type"].browse(
                vals.get("picking_type_id") or production.picking_type_id.id
            )
            if not picking_type.warehouse_id.branch_id and production.branch_id:
                vals["branch_id"] = production.branch_id.id
        return vals_list

    def _get_move_raw_values(self, product, product_uom_qty, product_uom, operation_id=False, bom_line=False):
        values = super()._get_move_raw_values(
            product, product_uom_qty, product_uom, operation_id=operation_id, bom_line=bom_line)
        if self.branch_id:
            values["branch_id"] = self.branch_id.id
        return values

    def _get_move_finished_values(self, product_id, product_uom_qty, product_uom, operation_id=False,
                                  byproduct_id=False, cost_share=0):
        values = super()._get_move_finished_values(
            product_id, product_uom_qty, product_uom, operation_id=operation_id,
            byproduct_id=byproduct_id, cost_share=cost_share)
        if self.branch_id:
            values["branch_id"] = self.branch_id.id
        return values

    def _get_backorder_mo_vals(self):
        values = super()._get_backorder_mo_vals()
        if self.branch_id:
            values["branch_id"] = self.branch_id.id
        return values
