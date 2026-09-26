from odoo import Command
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import tagged

from .common import BranchTestCommon


@tagged("post_install", "-at_install", "branch_management")
class TestBranchSecurity(BranchTestCommon):

    def test_groups_hierarchy(self):
        self.assertTrue(self.user_a.has_group("branch_management.group_branch_user"),
                        "every internal user is a branch user")
        self.assertFalse(self.user_a.has_group("branch_management.group_branch_manager"))
        self.assertTrue(self.manager.has_group("branch_management.group_branch_user"))
        self.assertTrue(self.branch_admin.has_group("branch_management.group_branch_manager"))
        self.assertFalse(self.branch_admin.has_group("base.group_system"),
                         "branch admins do not get Odoo administrator rights")
        self.assertTrue(self.env.ref("base.user_admin").has_group("branch_management.group_branch_admin"))

    def test_unrestricted_flag(self):
        self.assertFalse(self.user_a.branch_unrestricted)
        self.assertFalse(self.manager.branch_unrestricted)
        self.assertTrue(self.branch_admin.branch_unrestricted)
        portal = self.env["res.users"].create({
            "name": "Portal", "login": "branch_portal",
            "group_ids": [Command.set(self.env.ref("base.group_portal").ids)],
        })
        self.assertTrue(portal.branch_unrestricted)

    def test_branch_user_cannot_manage_branches(self):
        env = self.env_for(self.user_a)
        with self.assertRaises(AccessError):
            env["res.branch"].create({"name": "X", "code": "X", "company_id": self.company_a.id})
        with self.assertRaises(AccessError):
            env["res.branch"].browse(self.branch_ahm.id).write({"name": "Hacked"})
        with self.assertRaises(AccessError):
            env["res.branch"].browse(self.branch_ahm.id).unlink()

    def test_branch_user_cannot_assign_himself(self):
        """A branch user cannot extend their own allowed branches, whatever the path."""
        env = self.env_for(self.user_a)
        # (env.user is a sudo record: go through the model like an RPC does)
        with self.assertRaises(AccessError):
            env["res.users"].browse(self.user_a.id).write({"allowed_branch_ids": [Command.link(self.branch_srt.id)]})
        with self.assertRaises(AccessError):
            env["res.branch"].browse(self.branch_srt.id).write({"user_ids": [Command.link(self.user_a.id)]})
        self.assertNotIn(self.branch_srt, self.user_a.allowed_branch_ids)

    def test_user_can_change_own_default_branch_within_allowed(self):
        self.user_a.allowed_branch_ids = [Command.link(self.branch_srt.id)]
        me = self.env_for(self.user_a)["res.users"].browse(self.user_a.id)
        me.write({"default_branch_id": self.branch_srt.id})
        self.assertEqual(self.user_a.default_branch_id, self.branch_srt)
        with self.assertRaises(ValidationError):
            me.write({"default_branch_id": self.branch_ho.id})

    def test_tc006_manager_manages_permitted_branches(self):
        """TC-006: a manager edits their branches only, and assigns users there."""
        env = self.env_for(self.manager)
        env["res.branch"].browse(self.branch_ahm.id).write({"phone": "+91 79 0000 0000"})
        self.assertEqual(self.branch_ahm.phone, "+91 79 0000 0000")
        with self.assertRaises(AccessError):
            env["res.branch"].browse(self.branch_ho.id).write({"phone": "1"})
        # assign users to a permitted branch
        env["res.branch"].browse(self.branch_srt.id).write({"user_ids": [Command.link(self.user_a.id)]})
        self.assertIn(self.branch_srt, self.user_a.allowed_branch_ids)
        # cannot add themselves to a branch they don't manage
        with self.assertRaises(AccessError):
            env["res.branch"].browse(self.branch_ho.id).write({"user_ids": [Command.link(self.manager.id)]})
        # managers create branches but cannot delete them
        new_branch = env["res.branch"].create({"name": "Rajkot", "code": "RJT", "company_id": self.company_a.id})
        with self.assertRaises(AccessError):
            new_branch.unlink()

    def test_admin_full_configuration(self):
        env = self.env_for(self.branch_admin, companies=self.company_a | self.company_b)
        branch = env["res.branch"].create({"name": "Nashik", "code": "NSK", "company_id": self.company_b.id})
        branch.write({"name": "Nashik City"})
        branch.unlink()
        env["res.branch"].browse(self.branch_ho.id).write({"phone": "42"})

    def test_branch_reference_fields_discovery(self):
        """Deletion protection scans every stored many2one to res.branch."""
        fields_ = self.Branch._get_branch_reference_fields()
        self.assertTrue(all(f.comodel_name == "res.branch" and f.store for f in fields_))
        self.assertNotIn("parent_id", [f.name for f in fields_ if f.model_name == "res.branch"])

    def test_tc025_superuser_behavior(self):
        """TC-025: superuser and sudo() keep full access and behave safely."""
        env_su = self.env(su=True)
        self.assertTrue(env_su.user._is_branch_unrestricted())
        self.assertEqual(
            env_su["res.branch"].with_context(active_test=False).search_count([]),
            self.Branch.sudo().with_context(active_test=False).search_count([]),
        )
        # sudo bypasses the user access check of branch-aware documents
        records = self.env_for(self.user_a)["res.branch"].sudo().search([("company_id", "=", self.company_b.id)])
        self.assertIn(self.branch_mum, records)

    def test_archived_branch_stays_in_security_boundary(self):
        """Archived branches stay allowed so that history remains readable."""
        self.branch_ahm.action_archive()
        self.assertIn(self.branch_ahm, self.user_a.allowed_branch_ids)
        self.assertNotIn(self.branch_ahm, self.env_for(self.user_a).user._get_selectable_branches())
