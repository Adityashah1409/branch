from odoo import Command

from odoo.addons.branch_management.tests.common import BranchTestCommon


class BranchAccountTestCommon(BranchTestCommon):
    """Branch fixtures + a chart of accounts on both test companies.

    The test users get the Invoicing (billing) rights.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        ChartTemplate = cls.env["account.chart.template"]
        for company in (cls.company_a, cls.company_b):
            ChartTemplate.try_loading("generic_coa", company=company, install_demo=False)
        cls._add_groups(
            cls.user_a | cls.user_b | cls.user_multi | cls.user_none | cls.manager | cls.branch_admin,
            "account.group_account_invoice",
        )
        cls.partner = cls.env["res.partner"].create({"name": "Branch Test Customer"})
        cls.sale_journal_a = cls._get_journal(cls.company_a, "sale")
        cls.purchase_journal_a = cls._get_journal(cls.company_a, "purchase")
        cls.bank_journal_a = cls._get_journal(cls.company_a, "bank")

    @classmethod
    def _add_groups(cls, users, *group_xmlids):
        groups = [Command.link(cls.env.ref(xmlid).id) for xmlid in group_xmlids]
        users.write({"group_ids": groups})

    @classmethod
    def _get_journal(cls, company, journal_type):
        return cls.env["account.journal"].search([
            ("company_id", "=", company.id), ("type", "=", journal_type),
        ], limit=1)

    @classmethod
    def _invoice_vals(cls, move_type="out_invoice", price=100.0, **values):
        return {
            "move_type": move_type,
            "partner_id": cls.partner.id,
            "invoice_date": "2026-01-15",
            "invoice_line_ids": [Command.create({
                "name": "Branch service", "quantity": 1, "price_unit": price, "tax_ids": [],
            })],
            **values,
        }

    def _create_invoice(self, env, post=False, **values):
        invoice = env["account.move"].create(self._invoice_vals(**values))
        if post:
            invoice.action_post()
        return invoice
