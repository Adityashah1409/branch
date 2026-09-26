from odoo import api, fields, models
from odoo.exceptions import UserError


class StockWarehouse(models.Model):
    _name = "stock.warehouse"
    _inherit = ["stock.warehouse", "res.branch.mixin"]

    branch_id = fields.Many2one(
        help="Branch operating this warehouse. Its operation types, locations, "
        "transfers and stock moves belong to this branch.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        # The mixin default uses the current company, whereas warehouses are
        # often created for another company (e.g. automatically when a company
        # is created): pick the default branch of the warehouse's own company.
        for vals in vals_list:
            if "branch_id" not in vals and vals.get("company_id"):
                company = self.env["res.company"].browse(vals["company_id"])
                vals["branch_id"] = self.env.user._get_current_branch(company).id
        return super().create(vals_list)

    def write(self, vals):
        if "branch_id" in vals:
            self._check_branch_change_allowed(vals["branch_id"])
        return super().write(vals)

    def _check_branch_change_allowed(self, new_branch_id):
        """Refuse to move a warehouse with ongoing transfers to another branch.

        Uses sudo(): the check must count the transfers of every branch (the
        user may not see all of them); only a count is computed, nothing is
        returned to the caller.
        """
        changed = self.filtered(lambda wh: wh.branch_id.id != (new_branch_id or False))
        if not changed:
            return
        ongoing = self.env["stock.picking"].sudo().search_count([
            ("picking_type_id.warehouse_id", "in", changed.ids),
            ("state", "not in", ("done", "cancel")),
        ], limit=1)
        if ongoing:
            raise UserError(self.env._(
                "You cannot change the branch of warehouse(s) %s while they have "
                "ongoing transfers. Validate or cancel them first.",
                ", ".join(changed.mapped("display_name")),
            ))
