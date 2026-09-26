from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tests import Form, tagged

from odoo.addons.branch_management.tests.common import BranchTestCommon


@tagged("post_install", "-at_install", "branch_management")
class TestPartnerBranch(BranchTestCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        partner_manager = cls.env.ref("base.group_partner_manager")
        (cls.user_a | cls.user_multi).write({"group_ids": [Command.link(partner_manager.id)]})
        Partner = cls.env["res.partner"]
        cls.p_ahm = Partner.create({"name": "AHM Customer", "branch_ids": [Command.set(cls.branch_ahm.ids)]})
        cls.p_srt = Partner.create({"name": "SRT Vendor", "branch_ids": [Command.set(cls.branch_srt.ids)]})
        cls.p_both = Partner.create({
            "name": "AHM+SRT Customer", "branch_ids": [Command.set((cls.branch_ahm | cls.branch_srt).ids)],
        })
        cls.p_shared = Partner.create({"name": "Shared Customer"})
        cls.all_partners = cls.p_ahm | cls.p_srt | cls.p_both | cls.p_shared

    def test_default_branch_from_form(self):
        Partner = self.env_for(self.user_a)["res.partner"]
        # disabled by default
        with Form(Partner) as form:
            form.name = "No default"
        self.assertFalse(form.record.branch_ids)

        self.company_a.branch_partner_default = True
        with Form(Partner) as form:
            form.name = "From the contact form"
        self.assertEqual(form.record.branch_ids, self.branch_ahm)
        with Form(self.env_for(self.user_multi, branch=self.branch_srt)["res.partner"]) as form:
            form.name = "Surat contact"
        self.assertEqual(form.record.branch_ids, self.branch_srt)
        # contacts created by code (users, emails, imports) get no branch
        self.assertFalse(Partner.create({"name": "By code"}).branch_ids)
        # the smart button's context wins
        with Form(Partner.with_context(default_branch_ids=[])) as form:
            form.name = "Explicitly shared"
        self.assertFalse(form.record.branch_ids)

    def test_unauthorized_branch_rejected(self):
        Partner = self.env_for(self.user_a)["res.partner"]
        with self.assertRaises(ValidationError):
            Partner.create({"name": "X", "branch_ids": [Command.set(self.branch_srt.ids)]})
        with self.assertRaises(ValidationError):
            Partner.browse(self.p_ahm.id).write({"branch_ids": [Command.link(self.branch_srt.id)]})
        # branches linked by others are kept when the user edits the contact
        partner = Partner.browse(self.p_srt.id)
        partner.write({"branch_ids": [Command.link(self.branch_ahm.id)], "phone": "123"})
        self.assertEqual(self.p_srt.branch_ids, self.branch_ahm | self.branch_srt)

    def test_other_company_branch_rejected(self):
        with self.assertRaises(ValidationError):
            self.env["res.partner"].create({
                "name": "X", "company_id": self.company_b.id,
                "branch_ids": [Command.set(self.branch_ahm.ids)],
            })
        with self.assertRaises(ValidationError):
            self.p_ahm.company_id = self.company_b

    def test_my_branches_filter(self):
        Partner = self.env_for(self.user_a)["res.partner"]
        mine = Partner.search([("in_my_branches", "=", True), ("id", "in", self.all_partners.ids)])
        self.assertEqual(set(mine.ids), {self.p_ahm.id, self.p_both.id, self.p_shared.id})
        others = Partner.search([("in_my_branches", "=", False), ("id", "in", self.all_partners.ids)])
        self.assertEqual(others, self.p_srt)
        self.assertFalse(Partner.browse(self.p_srt.id).in_my_branches)
        admin = self.env_for(self.branch_admin)["res.partner"].search(
            [("in_my_branches", "=", True), ("id", "in", self.all_partners.ids)])
        self.assertEqual(admin, self.all_partners)

    def test_partners_are_not_a_security_boundary(self):
        Partner = self.env_for(self.user_a)["res.partner"]
        self.assertEqual(Partner.search([("id", "in", self.all_partners.ids)]), self.all_partners)
        self.assertEqual(Partner.browse(self.p_srt.id).read(["name"])[0]["name"], "SRT Vendor")

    def test_group_by_branch(self):
        groups = dict(self.env["res.partner"]._read_group(
            [("id", "in", self.all_partners.ids)], ["branch_ids"], ["__count"]))
        self.assertEqual(groups[self.branch_ahm], 2)
        self.assertEqual(groups[self.branch_srt], 2)
        self.assertEqual(groups[self.env["res.branch"]], 1)

    def test_branch_smart_button(self):
        branch = self.env_for(self.user_a)["res.branch"].browse(self.branch_srt.id)
        self.assertEqual(branch.partner_count, 2)
        action = branch.action_view_partners()
        self.assertEqual(self.env["res.partner"].search(action["domain"]), self.p_srt | self.p_both)
