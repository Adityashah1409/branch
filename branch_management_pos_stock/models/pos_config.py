import logging

from odoo import api, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PosConfig(models.Model):
    _inherit = "pos.config"

    @api.model
    def _get_branch_pos_picking_type(self, branch):
        """PoS operation type of ``branch``: the one of its default warehouse,
        else of a warehouse shared by the company (no branch)."""
        if not branch:
            return self.env["stock.picking.type"]
        warehouse = branch._get_default_warehouse(company_fallback=True)
        if warehouse and not warehouse.pos_type_id:
            # pos_stock creates it lazily, like pos.config._default_picking_type_id
            warehouse._create_missing_pos_picking_types()
        return warehouse.pos_type_id

    @api.model_create_multi
    def create(self, vals_list):
        PickingType = self.env["stock.picking.type"]
        for vals in vals_list:
            picking_type_id = vals.get("picking_type_id") or self.env.context.get("default_picking_type_id")
            if picking_type_id:
                picking_type = PickingType.browse(picking_type_id)
                if "branch_id" not in vals and picking_type.branch_id:
                    vals["branch_id"] = picking_type.branch_id.id
                continue
            if "branch_id" in vals:
                branch = self.env["res.branch"].browse(vals["branch_id"])
            else:
                company = self.env["res.company"].browse(vals.get("company_id") or self.env.company.id)
                branch = self.with_company(company)._default_branch_id()
            picking_type = self._get_branch_pos_picking_type(branch)
            if picking_type:
                vals["picking_type_id"] = picking_type.id
        return super().create(vals_list)

    @api.onchange("branch_id")
    def _onchange_branch_id_picking_type(self):
        if not self.branch_id or self.picking_type_id.branch_id == self.branch_id:
            return
        picking_type = self._get_branch_pos_picking_type(self.branch_id)
        if picking_type:
            self.picking_type_id = picking_type

    @api.constrains("branch_id", "picking_type_id")
    def _check_picking_type_branch(self):
        for config in self:
            type_branch = config.picking_type_id.branch_id
            if config.branch_id and type_branch and type_branch != config.branch_id:
                _logger.info(
                    "Branch mismatch on PoS %s: branch %s vs operation type branch %s",
                    config.id, config.branch_id.id, type_branch.id,
                )
                raise ValidationError(self.env._(
                    "Point of Sale %(config)s belongs to branch %(branch)s but uses operation "
                    "type %(type)s of branch %(type_branch)s.",
                    config=config.display_name,
                    branch=config.branch_id.display_name,
                    type=config.picking_type_id.display_name,
                    type_branch=type_branch.display_name,
                ))
