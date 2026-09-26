import logging

from odoo import api, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.depends("branch_id")
    def _compute_warehouse_id(self):
        """Ship from the branch's warehouse (Branch -> Warehouse -> operations).

        Odoo (sale_stock) proposes the ``ir.default`` / salesperson warehouse
        of quotations. When the order has a branch:

        * the branch's default warehouse wins;
        * when the branch has no warehouse and Odoo proposed a warehouse of
          another branch, a warehouse shared by the company (without branch)
          is used instead, if any;
        * otherwise Odoo's proposal is kept.

        Like Odoo, only quotations (and new records) are recomputed.
        """
        super()._compute_warehouse_id()
        for order in self:
            branch = order.branch_id
            if not branch or not (order.state in ("draft", "sent") or not order.ids):
                continue
            branch = branch.with_company(order.company_id)
            warehouse = branch._get_default_warehouse()
            proposed_branch = order.warehouse_id.branch_id
            if not warehouse and proposed_branch and proposed_branch != order.branch_id:
                warehouse = branch._get_default_warehouse(company_fallback=True)
            if warehouse:
                order.warehouse_id = warehouse

    @api.constrains("branch_id", "warehouse_id")
    def _check_warehouse_branch(self):
        for order in self:
            warehouse_branch = order.warehouse_id.branch_id
            if order.branch_id and warehouse_branch and warehouse_branch != order.branch_id:
                _logger.info(
                    "Branch mismatch on sales order %s: branch %s vs warehouse branch %s",
                    order.id, order.branch_id.id, warehouse_branch.id,
                )
                raise ValidationError(self.env._(
                    "Sales order %(order)s belongs to branch %(branch)s but ships from warehouse "
                    "%(warehouse)s of branch %(warehouse_branch)s. Choose a warehouse of the "
                    "order's branch (or a warehouse shared by all branches).",
                    order=order.display_name,
                    branch=order.branch_id.display_name,
                    warehouse=order.warehouse_id.display_name,
                    warehouse_branch=warehouse_branch.display_name,
                ))
