from odoo import Command
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import tagged

from odoo.addons.branch_management.tests.common import BranchTestCommon


@tagged("post_install", "-at_install", "branch_management")
class TestProjectBranch(BranchTestCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        manager = cls.env.ref("project.group_project_manager")
        user = cls.env.ref("project.group_project_user")
        # user_a / user_multi / branch_admin are project managers ("see all"
        # permission: the branch restriction still applies), user_b a user
        (cls.user_a | cls.user_multi | cls.branch_admin).write({"group_ids": [Command.link(manager.id)]})
        cls.user_b.write({"group_ids": [Command.link(user.id)]})

        Project = cls.env["project.project"]
        common = {"company_id": cls.company_a.id, "privacy_visibility": "employees"}
        cls.proj_ahm = Project.create(dict(common, name="AHM Project", branch_id=cls.branch_ahm.id))
        cls.proj_srt = Project.create(dict(common, name="SRT Project", branch_id=cls.branch_srt.id))
        cls.proj_shared = Project.create(dict(common, name="Shared Project", branch_id=False))
        Task = cls.env["project.task"]
        cls.task_ahm = Task.create({"name": "AHM task", "project_id": cls.proj_ahm.id})
        cls.task_srt = Task.create({
            "name": "SRT task", "project_id": cls.proj_srt.id,
            # assigned to user_a: assignment does not bypass the branch boundary
            "user_ids": [Command.set((cls.user_a | cls.user_b).ids)],
        })
        cls.task_shared = Task.create({"name": "Shared task", "project_id": cls.proj_shared.id})
        cls.task_private = Task.create({
            "name": "Private task", "project_id": False,
            "user_ids": [Command.set(cls.user_a.ids)],
        })
        cls.all_tasks = cls.task_ahm | cls.task_srt | cls.task_shared | cls.task_private
        cls.all_projects = cls.proj_ahm | cls.proj_srt | cls.proj_shared

    def test_default_branch_is_current_branch(self):
        project = self.env_for(self.user_a)["project.project"].create({"name": "New"})
        self.assertEqual(project.branch_id, self.branch_ahm)
        project = self.env_for(self.user_multi, branch=self.branch_srt)["project.project"].create({"name": "New 2"})
        self.assertEqual(project.branch_id, self.branch_srt)

    def test_task_branch_follows_project(self):
        self.assertEqual(self.task_ahm.branch_id, self.branch_ahm)
        self.assertEqual(self.task_srt.branch_id, self.branch_srt)
        self.assertFalse(self.task_private.branch_id)
        task = self.env_for(self.user_multi, branch=self.branch_srt)["project.task"].create({
            "name": "In AHM project", "project_id": self.proj_ahm.id,
        })
        self.assertEqual(task.branch_id, self.branch_ahm, "the task branch comes from the project")
        task.project_id = self.proj_srt
        self.assertEqual(task.branch_id, self.branch_srt)
        self.proj_srt.branch_id = self.branch_ahm
        self.assertEqual(self.task_srt.branch_id, self.branch_ahm)
        self.assertTrue(self.env["project.task"]._fields["branch_id"].readonly)

    def test_unauthorized_branch_rejected(self):
        Project = self.env_for(self.user_a)["project.project"]
        with self.assertRaises(ValidationError):
            Project.create({"name": "X", "branch_id": self.branch_srt.id})
        with self.assertRaises(ValidationError):
            Project.browse(self.proj_ahm.id).write({"branch_id": self.branch_srt.id})

    def test_other_company_branch_rejected(self):
        with self.assertRaises(ValidationError):
            self.env["project.project"].create({
                "name": "X", "company_id": self.company_a.id, "branch_id": self.branch_mum.id,
            })

    def test_project_security(self):
        for user in (self.user_a, self.user_b):
            Project = self.env_for(user)["project.project"]
            own = self.proj_ahm if user == self.user_a else self.proj_srt
            other = self.proj_srt if user == self.user_a else self.proj_ahm
            visible = Project.search([("id", "in", self.all_projects.ids)])
            self.assertEqual(set(visible.ids), {own.id, self.proj_shared.id})
            with self.assertRaises(AccessError):
                Project.browse(other.id).read(["name"])
        with self.assertRaises(AccessError):
            self.env_for(self.user_a)["project.project"].browse(self.proj_srt.id).write({"name": "Hacked"})
        admin = self.env_for(self.branch_admin)["project.project"].search([("id", "in", self.all_projects.ids)])
        self.assertEqual(admin, self.all_projects)

    def test_task_security(self):
        Task = self.env_for(self.user_a)["project.task"]
        visible = Task.search([("id", "in", self.all_tasks.ids)])
        self.assertEqual(set(visible.ids), {self.task_ahm.id, self.task_shared.id, self.task_private.id},
                         "private tasks and tasks without branch stay visible")
        with self.assertRaises(AccessError):
            Task.browse(self.task_srt.id).read(["name"])
        with self.assertRaises(AccessError):
            Task.browse(self.task_srt.id).write({"name": "Hacked"})
        # a private task can still be created and edited
        private = Task.create({"name": "My todo", "user_ids": [Command.set(self.user_a.ids)]})
        private.name = "My todo (edited)"
        self.assertFalse(private.branch_id)
        # project user of Surat sees the Surat task
        Task_b = self.env_for(self.user_b)["project.task"]
        self.assertIn(self.task_srt, Task_b.search([("id", "in", self.all_tasks.ids)]))
        admin = self.env_for(self.branch_admin)["project.task"].search(
            [("id", "in", (self.task_ahm | self.task_srt | self.task_shared).ids)])
        self.assertEqual(len(admin), 3)

    def test_current_branch_filter(self):
        env = self.env_for(self.user_multi, branch=self.branch_srt)
        self.assertEqual(env["project.project"].search([
            ("is_current_branch", "=", True), ("id", "in", self.all_projects.ids)]), self.proj_srt)
        self.assertEqual(env["project.task"].search([
            ("is_current_branch", "=", True), ("id", "in", self.all_tasks.ids)]), self.task_srt)

    def test_group_by_branch(self):
        groups = dict(self.env["project.task"]._read_group(
            [("id", "in", self.all_tasks.ids)], ["branch_id"], ["__count"]))
        self.assertEqual(groups[self.branch_ahm], 1)
        self.assertEqual(groups[self.branch_srt], 1)
        self.assertEqual(groups[self.env["res.branch"]], 2)
        result = self.env_for(self.user_a)["project.project"].formatted_read_group(
            [("id", "in", self.all_projects.ids)], ["branch_id"], ["__count"])
        self.assertEqual({group["branch_id"] and group["branch_id"][0] for group in result},
                         {self.branch_ahm.id, False})

    def test_task_report_branch(self):
        self.env.flush_all()
        Report = self.env_for(self.user_a)["report.project.task.user"]
        rows = Report.search([("task_id", "in", self.all_tasks.ids)])
        self.assertEqual(set(rows.mapped("branch_id").ids), {self.branch_ahm.id})
        self.assertNotIn(self.task_srt, rows.task_id)
        groups = dict(self.env["report.project.task.user"]._read_group(
            [("task_id", "in", self.all_tasks.ids)], ["branch_id"], ["__count"]))
        self.assertEqual(groups[self.branch_srt], 1)

    def test_branch_smart_button(self):
        branch = self.env_for(self.user_a)["res.branch"].browse(self.branch_ahm.id)
        self.assertEqual(branch.project_count, 1)
        action = branch.action_view_projects()
        self.assertEqual(self.env["project.project"].search(action["domain"]), self.proj_ahm)
