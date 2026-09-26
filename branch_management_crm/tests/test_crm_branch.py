from odoo import Command
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import Form, tagged

from odoo.addons.branch_management.tests.common import BranchTestCommon


@tagged("post_install", "-at_install", "branch_management")
class TestCrmBranch(BranchTestCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        all_leads = cls.env.ref("sales_team.group_sale_salesman_all_leads")
        (cls.user_a | cls.user_b | cls.user_multi | cls.branch_admin).write({
            "group_ids": [Command.link(all_leads.id)],
        })
        cls.team_srt = cls.env["crm.team"].create({
            "name": "Surat Team",
            "company_id": cls.company_a.id,
            "branch_id": cls.branch_srt.id,
        })
        cls.team_plain = cls.env["crm.team"].create({
            "name": "Company A Team",
            "company_id": cls.company_a.id,
        })
        Lead = cls.env["crm.lead"]
        cls.lead_ahm = Lead.create({
            "name": "AHM lead", "company_id": cls.company_a.id, "branch_id": cls.branch_ahm.id,
            "team_id": cls.team_plain.id, "user_id": False,
        })
        cls.lead_srt = Lead.create({
            "name": "SRT lead", "company_id": cls.company_a.id, "branch_id": cls.branch_srt.id,
            "team_id": cls.team_plain.id, "user_id": False,
        })
        cls.lead_shared = Lead.create({
            "name": "Lead without branch", "company_id": cls.company_a.id, "branch_id": False,
            "team_id": cls.team_plain.id, "user_id": False,
        })

    def _lead_model(self, user, branch=None):
        return self.env_for(user, branch=branch)["crm.lead"]

    # ------------------------------------------------------------------
    # Defaults and propagation
    # ------------------------------------------------------------------

    def test_default_branch_is_current_branch(self):
        lead = self._lead_model(self.user_a).create({"name": "New", "team_id": self.team_plain.id})
        self.assertEqual(lead.branch_id, self.branch_ahm)
        lead = self._lead_model(self.user_multi, branch=self.branch_srt).create({
            "name": "New", "team_id": self.team_plain.id,
        })
        self.assertEqual(lead.branch_id, self.branch_srt)

    def test_default_branch_in_form(self):
        with Form(self._lead_model(self.user_a).with_context(default_type="opportunity")) as form:
            form.name = "From the form"
            self.assertEqual(form.branch_id, self.branch_ahm)
        self.assertEqual(form.record.branch_id, self.branch_ahm)

    def test_team_branch_wins_over_current_branch(self):
        Lead = self._lead_model(self.user_multi, branch=self.branch_ahm)
        lead = Lead.create({"name": "Team lead", "team_id": self.team_srt.id})
        self.assertEqual(lead.branch_id, self.branch_srt)
        # an explicit branch is kept
        lead = Lead.create({"name": "Explicit", "team_id": self.team_srt.id,
                            "branch_id": self.branch_ahm.id})
        self.assertEqual(lead.branch_id, self.branch_ahm)
        # moving an existing lead to a dedicated team moves it to its branch
        lead.team_id = self.team_srt
        self.assertEqual(lead.branch_id, self.branch_srt)
        # moving it to a team without branch keeps the branch
        lead.team_id = self.team_plain
        self.assertEqual(lead.branch_id, self.branch_srt)

    def test_team_branch_company_consistency(self):
        with self.assertRaises(ValidationError):
            self.env["crm.team"].create({
                "name": "Wrong", "company_id": self.company_b.id, "branch_id": self.branch_ahm.id,
            })
        with Form(self.env["crm.team"]) as form:
            form.name = "No company yet"
            form.company_id = self.env["res.company"]
            form.branch_id = self.branch_srt
            self.assertEqual(form.company_id, self.company_a)

    def test_merge_keeps_branch(self):
        lead = self.env["crm.lead"].create({
            "name": "Dup", "company_id": self.company_a.id, "branch_id": self.branch_srt.id,
            "team_id": self.team_plain.id, "user_id": False, "type": "opportunity",
        })
        other = self.env["crm.lead"].create({
            "name": "Dup 2", "company_id": self.company_a.id, "branch_id": False,
            "team_id": self.team_plain.id, "user_id": False, "type": "opportunity",
        })
        merged = (lead | other)._merge_opportunity(auto_unlink=False, max_length=None)
        self.assertEqual(merged.branch_id, self.branch_srt)

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def test_unauthorized_branch_rejected(self):
        with self.assertRaises(ValidationError):
            self._lead_model(self.user_a).create({"name": "X", "branch_id": self.branch_srt.id})
        lead = self._lead_model(self.user_a).browse(self.lead_ahm.id)
        # (moving the lead out of the user's branches is also an access violation)
        with self.assertRaises((ValidationError, AccessError)):
            lead.write({"branch_id": self.branch_srt.id})
        # a team dedicated to a forbidden branch cannot be used to sneak in
        # (refused by the branch access restriction)
        with self.assertRaises((ValidationError, AccessError)):
            self._lead_model(self.user_a).create({"name": "Y", "team_id": self.team_srt.id})

    def test_other_company_branch_rejected(self):
        with self.assertRaises(ValidationError):
            self.env["crm.lead"].create({
                "name": "X", "company_id": self.company_a.id, "branch_id": self.branch_mum.id,
                "team_id": self.team_plain.id,
            })

    # ------------------------------------------------------------------
    # Security
    # ------------------------------------------------------------------

    def test_branch_security(self):
        Lead = self._lead_model(self.user_a)
        visible = Lead.search([("id", "in", (self.lead_ahm | self.lead_srt | self.lead_shared).ids)])
        self.assertIn(self.lead_ahm.id, visible.ids)
        self.assertIn(self.lead_shared.id, visible.ids, "leads without branch stay shared")
        self.assertNotIn(self.lead_srt.id, visible.ids)
        with self.assertRaises(AccessError):
            Lead.browse(self.lead_srt.id).read(["name"])
        with self.assertRaises(AccessError):
            Lead.browse(self.lead_srt.id).write({"name": "Hacked"})
        with self.assertRaises(AccessError):
            Lead.browse(self.lead_srt.id).unlink()

        admin_leads = self.env_for(self.branch_admin)["crm.lead"].search(
            [("id", "in", (self.lead_ahm | self.lead_srt).ids)])
        self.assertEqual(len(admin_leads), 2)

    def test_current_branch_filter(self):
        Lead = self._lead_model(self.user_multi, branch=self.branch_srt)
        leads = Lead.search([("is_current_branch", "=", True),
                             ("id", "in", (self.lead_ahm | self.lead_srt).ids)])
        self.assertEqual(leads, self.lead_srt)

    def test_group_by_branch(self):
        leads = self.lead_ahm | self.lead_srt | self.lead_shared
        groups = dict(self.env["crm.lead"]._read_group(
            [("id", "in", leads.ids)], ["branch_id"], ["__count"]))
        self.assertEqual(groups[self.branch_ahm], 1)
        self.assertEqual(groups[self.branch_srt], 1)
        # through the web client API, as a restricted user
        result = self._lead_model(self.user_a).formatted_read_group(
            [("id", "in", leads.ids)], ["branch_id"], ["__count"])
        branches = {group["branch_id"][0] if group["branch_id"] else False for group in result}
        self.assertEqual(branches, {self.branch_ahm.id, False})

    def test_activity_report_branch(self):
        activity_type = self.env.ref("mail.mail_activity_data_call")
        for lead in self.lead_ahm | self.lead_srt:
            lead.message_post(body="Called", mail_activity_type_id=activity_type.id)
        self.env.flush_all()
        report = self.env_for(self.user_a)["crm.activity.report"].search(
            [("lead_id", "in", (self.lead_ahm | self.lead_srt).ids)])
        self.assertTrue(report)
        self.assertEqual(set(report.mapped("branch_id").ids), {self.branch_ahm.id})

    def test_branch_smart_button(self):
        branch = self.env_for(self.user_a)["res.branch"].browse(self.branch_ahm.id)
        self.assertEqual(branch.crm_lead_count, 1)
        action = branch.action_view_crm_leads()
        self.assertEqual(action["res_model"], "crm.lead")
        self.assertEqual(self.env["crm.lead"].search(action["domain"]), self.lead_ahm)
