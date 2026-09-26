from odoo import api, models


class StockMove(models.Model):
    _inherit = "stock.move"

    @api.depends(
        "picking_id.branch_id", "picking_type_id", "location_id", "location_dest_id",
        "production_id.branch_id", "raw_material_production_id.branch_id",
        "unbuild_id.branch_id", "consume_unbuild_id.branch_id",
    )
    def _compute_branch_id(self):
        return super()._compute_branch_id()

    def _get_branch_from_origin(self):
        self.ensure_one()
        return (
            self.production_id.branch_id
            or self.raw_material_production_id.branch_id
            or self.unbuild_id.branch_id
            or self.consume_unbuild_id.branch_id
            or super()._get_branch_from_origin()
        )
