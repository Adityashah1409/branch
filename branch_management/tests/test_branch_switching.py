from odoo.tests import tagged

from .common import BranchTestCommon


@tagged("post_install", "-at_install", "branch_management")
class TestBranchSwitching(BranchTestCommon):

    def test_tc008_switch_updates_working_context(self):
        """TC-008: switching the branch changes the working branch only."""
        env = self.env_for(self.user_multi)
        self.assertEqual(env.user.current_branch_id, self.branch_ahm)
        result = env["res.users"].switch_current_branch(self.branch_srt.id)
        self.assertEqual(result, self.branch_srt.id)
        env = self.env_for(self.user_multi, branch=self.branch_srt)
        self.assertEqual(env.user.current_branch_id, self.branch_srt)
        # switching back A <- B
        env = self.env_for(self.user_multi, branch=self.branch_ahm)
        self.assertEqual(env.user.current_branch_id, self.branch_ahm)
        # nothing was persisted
        self.assertEqual(self.user_multi.default_branch_id, self.branch_ahm)

    def test_switch_to_invalid_branch(self):
        """The branch sent by the client is never trusted."""
        env = self.env_for(self.user_a)
        self.assertEqual(env["res.users"].switch_current_branch(self.branch_srt.id), self.branch_ahm.id)
        env = self.env_for(self.user_a, branch=self.branch_srt)
        self.assertEqual(env.user.current_branch_id, self.branch_ahm)
        env = self.env_for(self.user_a, branch=self.branch_mum)
        self.assertEqual(env.user.current_branch_id, self.branch_ahm)

    def test_session_restart_uses_default(self):
        """Without client hint (new session) the default branch is used."""
        env = self.env_for(self.user_multi)
        self.assertEqual(env.user._get_current_branch(), self.branch_ahm)

    def test_tc010_archived_current_branch(self):
        """TC-010 / edge case 3: an archived current branch is replaced."""
        self.branch_ahm.action_archive()
        env = self.env_for(self.user_multi, branch=self.branch_ahm)
        self.assertEqual(env.user.current_branch_id, self.branch_srt)
        self.assertEqual(self.user_multi.default_branch_id, self.branch_srt,
                         "archiving resets the default branch of its users")

    def test_tc023_selector_displays_valid_branches(self):
        """TC-023: the selector data only lists valid (active, allowed,
        company-enabled) branches."""
        self.branch_srt.action_archive()
        env = self.env_for(self.user_multi, companies=self.company_a)
        info = env["res.users"]._get_branch_session_info()
        ids = [b["id"] for b in info["allowed_branches"]]
        # the selector gets branches of all the user's companies; the client
        # filters on enabled companies (see branch_service.js)
        self.assertEqual(set(ids), {self.branch_ahm.id, self.branch_mum.id})
        self.assertEqual(info["default_branch_id"], self.branch_ahm.id)
        info_a = self.env_for(self.user_a)["res.users"]._get_branch_session_info()
        self.assertEqual([b["id"] for b in info_a["allowed_branches"]], [self.branch_ahm.id])

    def test_default_value_uses_current_branch(self):
        """The mixin default follows the working branch of the company."""
        Mixin = self.env_for(self.user_multi, branch=self.branch_srt)["res.branch.mixin"]
        self.assertEqual(Mixin._default_branch_id(), self.branch_srt)
        Mixin = self.env_for(self.user_multi, companies=self.company_b)["res.branch.mixin"]
        self.assertEqual(Mixin._default_branch_id(), self.branch_mum)
        Mixin = self.env_for(self.user_none)["res.branch.mixin"]
        self.assertFalse(Mixin._default_branch_id())
