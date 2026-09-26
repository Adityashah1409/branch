from odoo import api, fields, models
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _name = "purchase.order"
    _inherit = ["purchase.order", "res.branch.mixin"]

    branch_id = fields.Many2one(tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            company = self.env["res.company"].browse(
                vals.get("company_id") or self.default_get(["company_id"]).get("company_id")
            )
            if "branch_id" not in vals and company:
                # the default branch must be one of the order's company
                vals["branch_id"] = self.with_company(company)._default_branch_id().id
            branch = self.env["res.branch"].browse(vals.get("branch_id"))
            if (
                branch
                and company.branch_sequence_enabled
                and vals.get("name", self.env._("New")) == self.env._("New")
            ):
                vals["name"] = branch._get_next_sequence_number("purchase.order", "PO")
        return super().create(vals_list)

    @api.onchange("company_id")
    def _onchange_company_id_branch(self):
        self._branch_sync_with_company()

    def _prepare_invoice(self):
        # used by "Create Bill" and by the purchase auto-complete of a bill
        invoice_vals = super()._prepare_invoice()
        invoice_vals["branch_id"] = self.branch_id.id
        return invoice_vals

    def action_create_invoice(self, attachment_ids=False):
        # Odoo groups the bills by (company, vendor, currency) only: bill the
        # orders branch by branch so that a bill never mixes branches.
        orders_by_branch = self.grouped("branch_id")
        if len(orders_by_branch) <= 1:
            return super().action_create_invoice(attachment_ids=attachment_ids)
        if attachment_ids:
            raise UserError(self.env._(
                "You can only upload a bill for orders of a single branch at a time."
            ))
        invoices = self.env["account.move"]
        for orders in orders_by_branch.values():
            existing = orders.invoice_ids
            super(PurchaseOrder, orders).action_create_invoice()
            orders.invalidate_recordset(["invoice_ids"])
            invoices |= orders.invoice_ids - existing
        return self.action_view_invoice(invoices)
