from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ResBranch(models.Model):
    _inherit = "res.branch"

    warehouse_ids = fields.One2many(
        "stock.warehouse", "branch_id", string="Warehouses",
        help="Warehouses operated by this branch.",
    )
    warehouse_count = fields.Integer(compute="_compute_warehouse_count", string="# Warehouses")
    default_warehouse_id = fields.Many2one(
        "stock.warehouse",
        string="Default Warehouse",
        check_company=True,
        domain="[('branch_id', '=', id)]",
        help="Warehouse used by default for the operations of this branch (sales, "
        "purchases, manufacturing...). When empty, the first warehouse of the branch is used.",
    )

    @api.depends("warehouse_ids")
    def _compute_warehouse_count(self):
        for branch in self:
            branch.warehouse_count = len(branch.warehouse_ids)

    @api.constrains("default_warehouse_id")
    def _check_default_warehouse(self):
        for branch in self:
            warehouse = branch.default_warehouse_id
            if warehouse and warehouse.branch_id != branch:
                raise ValidationError(self.env._(
                    "The default warehouse %(warehouse)s of branch %(branch)s must belong to that branch.",
                    warehouse=warehouse.display_name,
                    branch=branch.display_name,
                ))

    def _get_default_warehouse(self, company_fallback=False):
        """Return the warehouse to use for operations of this branch.

        Public helper for integration modules (sale, purchase, mrp bridges):

        1. the branch's default warehouse, if still active and in the branch;
        2. else the first active warehouse of the branch (warehouse sequence);
        3. else, with ``company_fallback``, the first active warehouse of the
           branch's company that has no branch;
        4. else an empty recordset.
        """
        self.ensure_one()
        Warehouse = self.env["stock.warehouse"]
        default = self.default_warehouse_id
        if default and default.active and default.branch_id == self:
            return default
        warehouse = Warehouse.search(
            [("branch_id", "=", self.id), ("company_id", "=", self.company_id.id)], limit=1
        )
        if not warehouse and company_fallback:
            warehouse = Warehouse.search(
                [("branch_id", "=", False), ("company_id", "=", self.company_id.id)], limit=1
            )
        return warehouse

    def action_view_warehouses(self):
        self.ensure_one()
        return self._get_records_action(self.env._("Warehouses"), "stock.warehouse")

    def action_view_pickings(self):
        self.ensure_one()
        return self._get_records_action(self.env._("Transfers"), "stock.picking")
