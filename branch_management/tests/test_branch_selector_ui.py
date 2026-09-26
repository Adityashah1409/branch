from odoo.tests import HttpCase, new_test_user, tagged


@tagged("post_install", "-at_install", "branch_management")
class TestBranchSelectorUI(HttpCase):
    """TC-008 / TC-023 in the real web client: the systray selector lists
    valid branches only, switching changes the working branch, and the
    choice survives a new page load (cookie) without any database write."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        company = cls.env["res.company"].create({"name": "Branch UI Company"})
        other = cls.env["res.company"].create({"name": "Branch UI Other Company"})
        Branch = cls.env["res.branch"]
        cls.ahm = Branch.create({"name": "Ahmedabad", "code": "AHM", "company_id": company.id})
        cls.srt = Branch.create({"name": "Surat", "code": "SRT", "company_id": company.id})
        Branch.create({"name": "Pune", "code": "PUN", "company_id": company.id})
        mum = Branch.create({"name": "Mumbai", "code": "MUM", "company_id": other.id})
        cls.user = new_test_user(
            cls.env, login="branch_ui_user", password="branch_ui_user",
            groups="base.group_user",
            company_id=company.id, company_ids=[(6, 0, (company | other).ids)],
            allowed_branch_ids=[(6, 0, (cls.ahm | cls.srt | mum).ids)],
            default_branch_id=cls.ahm.id,
        )

    def test_branch_selector_switch(self):
        self.start_tour("/odoo", "branch_selector_switch", login="branch_ui_user")
        self.assertEqual(self.user.default_branch_id, self.ahm, "switching must not persist")
