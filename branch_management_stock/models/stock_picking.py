import logging

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _name = "stock.picking"
    _inherit = ["stock.picking", "res.branch.mixin"]

    # Branch -> Warehouse -> Operation type: the transfer belongs to the
    # branch of its operation type's warehouse. Editable (and settable in
    # create values) so that flows without a branch-owned warehouse can still
    # carry the branch of the originating document.
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
    dest_branch_id = fields.Many2one(
        "res.branch",
        string="Destination Branch",
        compute="_compute_cross_branch",
        store=True,
        index="btree_not_null",
        help="Branch of the destination location.",
    )
    is_cross_branch = fields.Boolean(
        string="Cross-Branch Transfer",
        compute="_compute_cross_branch",
        store=True,
        help="The source and destination of this transfer belong to different branches.",
    )

    # ------------------------------------------------------------------
    # Computes
    # ------------------------------------------------------------------

    @api.depends("picking_type_id")
    def _compute_branch_id(self):
        # Only depends on the operation type (not on its branch): changing the
        # branch of a warehouse later must not rewrite the history.
        for picking in self:
            type_branch = picking.picking_type_id.branch_id
            if type_branch:
                picking.branch_id = type_branch
            elif not picking.branch_id and not self.env.su and picking.company_id:
                # interactive creation on a warehouse without branch: use the
                # working branch, like any other branch-aware document
                picking.branch_id = self.env.user._get_current_branch(picking.company_id)

    @api.depends("branch_id", "location_id", "location_dest_id")
    def _compute_cross_branch(self):
        for picking in self:
            dest_branch = picking.location_dest_id.branch_id
            picking.dest_branch_id = dest_branch
            branches = picking.branch_id | picking.location_id.branch_id | dest_branch
            picking.is_cross_branch = len(branches) > 1

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------

    @api.constrains("branch_id", "picking_type_id")
    def _check_picking_type_branch(self):
        for picking in self:
            type_branch = picking.picking_type_id.branch_id
            if picking.branch_id and type_branch and picking.branch_id != type_branch:
                _logger.info(
                    "Branch mismatch on transfer %s: branch %s vs operation type branch %s",
                    picking.id, picking.branch_id.id, type_branch.id,
                )
                raise ValidationError(self.env._(
                    "The branch %(branch)s of transfer %(picking)s does not match the branch "
                    "%(type_branch)s of its operation type %(type)s.",
                    branch=picking.branch_id.display_name,
                    picking=picking.display_name,
                    type_branch=type_branch.display_name,
                    type=picking.picking_type_id.display_name,
                ))

    def _check_cross_branch_transfer(self):
        """Refuse to validate cross-branch transfers unless the company allows them."""
        for picking in self:
            if not picking.is_cross_branch or picking.company_id.branch_allow_cross_transfer:
                continue
            source = picking.location_id.branch_id or picking.branch_id
            _logger.info(
                "Cross-branch transfer %s blocked (company %s does not allow them)",
                picking.id, picking.company_id.id,
            )
            raise UserError(self.env._(
                "Transfer %(picking)s moves goods from branch %(source_branch)s to branch "
                "%(destination)s. Cross-branch transfers are not allowed for company "
                "%(company)s (Settings > Branches).",
                picking=picking.display_name,
                source_branch=source.display_name,
                destination=(picking.dest_branch_id or picking.branch_id).display_name,
                company=picking.company_id.name,
            ))

    # ------------------------------------------------------------------
    # Business flow
    # ------------------------------------------------------------------

    def copy_data(self, default=None):
        vals_list = super().copy_data(default=default)
        default = default or {}
        for picking, vals in zip(self, vals_list):
            if "branch_id" in default:
                continue
            picking_type = self.env["stock.picking.type"].browse(
                vals.get("picking_type_id") or picking.picking_type_id.id
            )
            # keep an explicitly chosen branch (backorders, returns) when the
            # operation type does not impose one
            if not picking_type.branch_id and picking.branch_id:
                vals["branch_id"] = picking.branch_id.id
        return vals_list

    def button_validate(self):
        # fail before any wizard (backorder, ...) is displayed
        self.filtered(lambda p: p.state != "done")._check_cross_branch_transfer()
        return super().button_validate()

    def _action_done(self):
        self._check_cross_branch_transfer()
        return super()._action_done()
