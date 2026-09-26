from odoo import api, fields, models

INVOICE_TYPES = ("out_invoice", "out_refund", "out_receipt")
BILL_TYPES = ("in_invoice", "in_refund", "in_receipt")
ACCOUNT_GROUPS = "account.group_account_invoice,account.group_account_readonly"


class ResBranch(models.Model):
    _inherit = "res.branch"

    invoice_count = fields.Integer(compute="_compute_account_counts", groups=ACCOUNT_GROUPS)
    bill_count = fields.Integer(compute="_compute_account_counts", groups=ACCOUNT_GROUPS)
    payment_count = fields.Integer(compute="_compute_account_counts", groups=ACCOUNT_GROUPS)

    @api.depends_context("uid", "allowed_company_ids")
    def _compute_account_counts(self):
        # counts go through the user's access rights: a user only counts the
        # documents they are allowed to see
        Move = self.env["account.move"]
        invoices = dict(Move._read_group(
            [("branch_id", "in", self.ids), ("move_type", "in", INVOICE_TYPES)],
            ["branch_id"], ["__count"],
        ))
        bills = dict(Move._read_group(
            [("branch_id", "in", self.ids), ("move_type", "in", BILL_TYPES)],
            ["branch_id"], ["__count"],
        ))
        payments = dict(self.env["account.payment"]._read_group(
            [("branch_id", "in", self.ids)], ["branch_id"], ["__count"],
        ))
        for branch in self:
            branch.invoice_count = invoices.get(branch, 0)
            branch.bill_count = bills.get(branch, 0)
            branch.payment_count = payments.get(branch, 0)

    def _get_branch_document_action(self, xmlid, domain=None, context=None):
        """Standard window action ``xmlid`` restricted to the documents of the
        branch; new documents created from it default to the branch.

        Keeps the views, help and search view of the application's own action
        (unlike the generic ``_get_records_action``).
        """
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(xmlid)
        action["domain"] = [("branch_id", "=", self.id), *(domain or [])]
        action["context"] = dict(context or {}, default_branch_id=self.id)
        action["name"] = self.env._(
            "%(documents)s of %(branch)s", documents=action["name"], branch=self.display_name,
        )
        return action

    def action_view_invoices(self):
        return self._get_branch_document_action(
            "account.action_move_out_invoice_type",
            [("move_type", "in", INVOICE_TYPES)],
            {"default_move_type": "out_invoice"},
        )

    def action_view_bills(self):
        return self._get_branch_document_action(
            "account.action_move_in_invoice_type",
            [("move_type", "in", BILL_TYPES)],
            {"default_move_type": "in_invoice"},
        )

    def action_view_payments(self):
        return self._get_branch_document_action("account.action_account_all_payments")
