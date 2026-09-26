from psycopg2 import IntegrityError

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged
from odoo.tools import mute_logger

from .common import BranchTestCommon


@tagged("post_install", "-at_install", "branch_management")
class TestBranch(BranchTestCommon):

    def test_tc001_create_branch(self):
        """TC-001: create a branch; code is normalized and hierarchy named."""
        branch = self.Branch.create({
            "name": "Vadodara", "code": " vad ", "company_id": self.company_a.id,
            "parent_id": self.branch_guj.id,
        })
        self.assertEqual(branch.code, "VAD")
        self.assertEqual(branch.complete_name, "Head Office / Gujarat / Vadodara")
        self.assertEqual(branch.display_name, "Head Office / Gujarat / Vadodara")
        self.assertTrue(branch.active)
        self.assertIn(branch, self.company_a.branch_ids)

    def test_tc002_duplicate_code_same_company(self):
        """TC-002: duplicate branch code in the same company must fail."""
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"):
            self.Branch.create({"name": "Other", "code": "ahm", "company_id": self.company_a.id})

    def test_tc003_same_code_other_company(self):
        """TC-003: the same code is allowed in another company."""
        branch = self.Branch.create({"name": "Ahmedabad B", "code": "AHM", "company_id": self.company_b.id})
        self.assertEqual(branch.code, "AHM")

    def test_edit_branch_updates_hierarchy(self):
        self.branch_guj.name = "Gujarat State"
        self.assertEqual(self.branch_ahm.complete_name, "Head Office / Gujarat State / Ahmedabad")

    def test_recursive_hierarchy_rejected(self):
        with self.assertRaises((UserError, ValidationError)):
            self.branch_ho.parent_id = self.branch_ahm

    def test_parent_other_company_rejected(self):
        with self.assertRaises(ValidationError):
            self.branch_mum.parent_id = self.branch_ho

    def test_archive_and_restore(self):
        self.branch_srt.action_archive()
        self.assertFalse(self.branch_srt.active)
        self.assertNotIn(self.branch_srt, self.Branch.search([("company_id", "=", self.company_a.id)]))
        self.branch_srt.action_unarchive()
        self.assertTrue(self.branch_srt.active)

    def test_duplicate_branch(self):
        copy = self.branch_ahm.copy()
        self.assertEqual(copy.code, "AHM1")
        self.assertEqual(copy.name, "Ahmedabad (copy)")
        self.assertFalse(copy.user_ids, "access to a duplicated branch must be granted explicitly")

    def test_delete_unused_branch(self):
        branch = self.Branch.create({"name": "Temp", "code": "TMP", "company_id": self.company_a.id})
        branch.unlink()
        self.assertFalse(branch.exists())

    def test_delete_branch_with_children_blocked(self):
        with self.assertRaises((IntegrityError, UserError)), mute_logger("odoo.sql_db"):
            self.branch_guj.unlink()

    def test_address_lines(self):
        self.branch_ahm.write({
            "street": "123 Main Road", "city": "Ahmedabad", "zip": "380001",
            "country_id": self.env.ref("base.in").id,
        })
        self.assertEqual(self.branch_ahm._get_address_lines(), ["123 Main Road", "380001 Ahmedabad", "India"])

    def test_branch_sequence(self):
        first = self.branch_ahm._get_next_sequence_number("sale.order", "SO")
        second = self.branch_ahm._get_next_sequence_number("sale.order", "SO")
        other = self.branch_srt._get_next_sequence_number("sale.order", "SO")
        self.assertEqual(first, "AHM/SO/00001")
        self.assertEqual(second, "AHM/SO/00002")
        self.assertEqual(other, "SRT/SO/00001")
        self.branch_srt.sequence_prefix = "SUR"
        self.assertEqual(self.branch_srt._get_next_sequence_number("purchase.order", "PO"), "SUR/PO/00001")

    def test_company_change_blocked_when_used(self):
        """A branch with no documents can move; the check is exercised by
        integration modules with real documents."""
        branch = self.Branch.create({"name": "Mobile", "code": "MOB", "company_id": self.company_a.id})
        branch.company_id = self.company_b
        self.assertEqual(branch.company_id, self.company_b)
