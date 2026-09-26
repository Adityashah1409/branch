from odoo.tests import tagged

from .common import BranchTestCommon


@tagged("post_install", "-at_install", "branch_management")
class TestBranchMultiCompany(BranchTestCommon):

    def test_tc020_branch_isolation_between_companies(self):
        """TC-020: a user of company A never sees company B branches."""
        env = self.env_for(self.user_a)
        branches = env["res.branch"].search([])
        self.assertIn(self.branch_ahm, branches)
        self.assertNotIn(self.branch_mum, branches)
        self.assertFalse(env["res.branch"].search([("id", "=", self.branch_mum.id)]))

    def test_multi_company_user_sees_enabled_companies_only(self):
        env = self.env_for(self.user_multi, companies=self.company_a)
        self.assertNotIn(self.branch_mum, env["res.branch"].search([]))
        env = self.env_for(self.user_multi, companies=self.company_a | self.company_b)
        self.assertIn(self.branch_mum, env["res.branch"].search([]))

    def test_tc009_switching_company_invalidates_branch(self):
        """TC-009: branches of a company that is not active are not usable."""
        env = self.env_for(self.user_multi, companies=self.company_b, branch=self.branch_ahm)
        self.assertEqual(env.user._get_current_branch(), self.branch_mum)
        env = self.env_for(self.user_multi, companies=self.company_a, branch=self.branch_mum)
        self.assertEqual(env.user._get_current_branch(), self.branch_ahm)

    def test_selectable_branches_follow_companies(self):
        env = self.env_for(self.user_multi, companies=self.company_a)
        self.assertEqual(env.user._get_selectable_branches(), self.branch_ahm | self.branch_srt)
        env = self.env_for(self.user_multi, companies=self.company_a | self.company_b)
        self.assertEqual(
            env.user._get_selectable_branches(), self.branch_ahm | self.branch_srt | self.branch_mum
        )

    def test_admin_selectable_branches_all_of_company(self):
        env = self.env_for(self.branch_admin, companies=self.company_b)
        self.assertEqual(env.user._get_selectable_branches(), self.branch_mum | self.branch_pun)
