from odoo import api, fields, models


class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = ["sale.order", "res.branch.mixin"]

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
                vals["name"] = branch._get_next_sequence_number("sale.order", "SO")
        return super().create(vals_list)

    @api.onchange("company_id")
    def _onchange_company_id_branch(self):
        self._branch_sync_with_company()

    def _prepare_invoice(self):
        # invoices, and down payment invoices (sale.advance.payment.inv
        # reuses this method), are created in the branch of the order
        invoice_vals = super()._prepare_invoice()
        invoice_vals["branch_id"] = self.branch_id.id
        return invoice_vals

    def _get_invoice_grouping_keys(self):
        # never merge orders of different branches into one invoice
        return [*super()._get_invoice_grouping_keys(), "branch_id"]
