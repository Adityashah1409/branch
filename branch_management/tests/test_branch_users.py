from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tests import new_test_user, tagged

from .common import BranchTestCommon


@tagged("post_install", "-at_install", "branch_management")
class TestBranchUsers(BranchTestCommon):

    def test_tc004_assign_branch_to_user(self):
        """TC-004: assign a branch to a user, from the user or the branch."""
        self.user_a.allowed_branch_ids = [Command.link(self.branch_srt.id)]
        self.assertIn(self.branch_srt, self.user_a.allowed_branch_ids)
        self.assertIn(self.user_a, self.branch_srt.user_ids)
        self.branch_ho.user_ids = [Command.link(self.user_a.id)]
        self.assertIn(self.branch_ho, self.user_a.allowed_branch_ids)

    def test_default_branch_set_automatically(self):
        self.assertEqual(self.user_a.default_branch_id, self.branch_ahm)
        self.assertEqual(self.user_multi.default_branch_id, self.branch_ahm)

    def test_tc007_default_branch_must_be_allowed(self):
        """TC-007: the default/current branch must belong to the allowed branches."""
        with self.assertRaises(ValidationError):
            self.user_a.default_branch_id = self.branch_srt

    def test_branch_of_foreign_company_rejected(self):
        with self.assertRaises(ValidationError):
            self.user_a.allowed_branch_ids = [Command.link(self.branch_mum.id)]
        with self.assertRaises(ValidationError):
            self.branch_mum.user_ids = [Command.link(self.user_a.id)]

    def test_case2_removing_current_branch(self):
        """Edge case 2: removing the default branch selects another valid one."""
        self.user_multi.allowed_branch_ids = [Command.unlink(self.branch_ahm.id)]
        self.assertEqual(self.user_multi.default_branch_id, self.branch_srt)
        # removing it from the branch side is handled too
        self.branch_srt.user_ids = [Command.unlink(self.user_multi.id)]
        self.assertEqual(self.user_multi.default_branch_id, self.branch_mum)

    def test_losing_company_drops_its_branches(self):
        self.user_multi.company_ids = [Command.unlink(self.company_b.id)]
        self.assertNotIn(self.branch_mum, self.user_multi.allowed_branch_ids)

    def test_tc024_user_without_branch(self):
        """TC-024: a user with zero branches does not crash."""
        env = self.env_for(self.user_none)
        user = env.user
        self.assertFalse(user.allowed_branch_ids)
        self.assertFalse(user.default_branch_id)
        self.assertFalse(user.current_branch_id)
        self.assertFalse(user._get_current_branch())
        self.assertEqual(env["res.users"]._get_branch_session_info()["allowed_branches"], [])
        self.assertFalse(env["res.users"].switch_current_branch(self.branch_ahm.id))
        # can still read the branch master of the company
        self.assertTrue(env["res.branch"].search([]))

    def test_new_user_default_branch(self):
        user = new_test_user(
            self.env, login="branch_new_user", groups="base.group_user",
            company_id=self.company_a.id, company_ids=[(6, 0, self.company_a.ids)],
            allowed_branch_ids=[(6, 0, (self.branch_srt | self.branch_ahm).ids)],
        )
        self.assertIn(user.default_branch_id, self.branch_srt | self.branch_ahm)

    def test_assign_wizard(self):
        wizard = self.env["branch.user.assign"].with_user(self.manager).create({
            "branch_ids": [(6, 0, self.branch_srt.ids)],
            "user_ids": [(6, 0, self.user_a.ids)],
            "mode": "add",
            "set_default": True,
        })
        wizard.action_apply()
        self.assertIn(self.branch_srt, self.user_a.allowed_branch_ids)
        self.assertEqual(self.user_a.default_branch_id, self.branch_srt)
        wizard = self.env["branch.user.assign"].with_user(self.manager).create({
            "branch_ids": [(6, 0, self.branch_srt.ids)],
            "user_ids": [(6, 0, self.user_a.ids)],
            "mode": "remove",
        })
        wizard.action_apply()
        self.assertNotIn(self.branch_srt, self.user_a.allowed_branch_ids)
        self.assertEqual(self.user_a.default_branch_id, self.branch_ahm)
