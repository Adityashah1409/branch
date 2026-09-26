from odoo import api, fields, models
from odoo.exceptions import UserError


class PosOrder(models.Model):
    _name = "pos.order"
    _inherit = ["pos.order", "res.branch.mixin"]

    branch_id = fields.Many2one(
        compute="_compute_branch_id",
        store=True,
        readonly=True,
        default=None,
        help="Branch of the shop the order was made in.",
    )

    @api.depends("config_id")
    def _compute_branch_id(self):
        for order in self:
            # an order detached from its session (future preset orders) keeps
            # its branch
            if order.config_id:
                order.branch_id = order.config_id.branch_id
            else:
                order.branch_id = order.branch_id

    def _prepare_invoice_vals(self):
        vals = super()._prepare_invoice_vals()
        branches = self.branch_id
        if len(branches) > 1:
            raise UserError(self.env._(
                "You cannot invoice orders of different branches (%s) together.",
                ", ".join(branches.mapped("display_name")),
            ))
        vals["branch_id"] = branches.id
        return vals
