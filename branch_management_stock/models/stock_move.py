from odoo import api, fields, models
from odoo.fields import Domain


class StockMove(models.Model):
    _inherit = "stock.move"

    branch_id = fields.Many2one(
        "res.branch",
        string="Branch",
        compute="_compute_branch_id",
        store=True,
        readonly=False,
        index="btree_not_null",
        help="Branch of the transfer, else of the operation type's warehouse, "
        "else of the source / destination location.",
    )
    dest_branch_id = fields.Many2one(
        "res.branch",
        string="Destination Branch",
        compute="_compute_dest_branch_id",
        store=True,
        index="btree_not_null",
    )

    @api.depends("picking_id.branch_id", "picking_type_id", "location_id", "location_dest_id")
    def _compute_branch_id(self):
        for move in self:
            branch = move._get_branch_from_origin()
            # keep a branch set explicitly (procurement values) when nothing
            # else determines it
            if branch or not move.branch_id:
                move.branch_id = branch

    def _get_branch_from_origin(self):
        """Branch implied by the document(s) the move belongs to.

        Extension point: other modules (mrp: production/unbuild orders) add
        their own origin before falling back to this implementation.
        """
        self.ensure_one()
        return (
            self.picking_id.branch_id
            or self.picking_type_id.branch_id
            or self.location_id.branch_id
            or self.location_dest_id.branch_id
        )

    @api.depends("location_dest_id")
    def _compute_dest_branch_id(self):
        for move in self:
            move.dest_branch_id = move.location_dest_id.branch_id

    # ------------------------------------------------------------------
    # Propagation to transfers
    # ------------------------------------------------------------------

    def _get_new_picking_values(self):
        vals = super()._get_new_picking_values()
        if len(self.branch_id) == 1:
            vals["branch_id"] = self.branch_id.id
        return vals

    def _key_assign_picking(self):
        return super()._key_assign_picking() + (self.branch_id,)

    def _search_picking_for_assignation_domain(self):
        domain = super()._search_picking_for_assignation_domain()
        return Domain.AND([domain, [("branch_id", "=", self.branch_id.id)]])

    @api.model
    def _prepare_merge_moves_distinct_fields(self):
        return super()._prepare_merge_moves_distinct_fields() + ["branch_id"]

    def _prepare_move_split_vals(self, qty):
        vals = super()._prepare_move_split_vals(qty)
        vals["branch_id"] = self.branch_id.id
        return vals
