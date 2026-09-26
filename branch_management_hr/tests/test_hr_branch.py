from odoo import Command
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import Form, tagged

from odoo.addons.branch_management.tests.common import BranchTestCommon


@tagged("post_install", "-at_install", "branch_management")
class TestHrBranch(BranchTestCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        hr_user = cls.env.ref("hr.group_hr_user")
        # user_a / user_b are HR officers of their branch; user_none stays a
        # plain employee (directory access only)
        (cls.user_a | cls.user_b | cls.user_multi | cls.branch_admin).write({
            "group_ids": [Command.link(hr_user.id)],
        })
        Employee = cls.env["hr.employee"]
        cls.dep_srt = cls.env["hr.department"].create({
            "name": "Surat Workshop", "company_id": cls.company_a.id, "branch_id": cls.branch_srt.id,
        })
        cls.emp_ahm = Employee.create({
            "name": "Ahmedabad Employee", "company_id": cls.company_a.id, "branch_id": cls.branch_ahm.id,
        })
        cls.emp_srt = Employee.create({
            "name": "Surat Employee", "company_id": cls.company_a.id, "branch_id": cls.branch_srt.id,
            "parent_id": cls.emp_ahm.id,
        })
        cls.emp_shared = Employee.create({
            "name": "Employee without branch", "company_id": cls.company_a.id, "branch_id": False,
        })
        cls.all_employees = cls.emp_ahm | cls.emp_srt | cls.emp_shared
        cls.work_location = cls.env["hr.work.location"].create({
            "name": "Office A", "company_id": cls.company_a.id,
            "address_id": cls.company_a.partner_id.id,
        })

    def test_default_branch_is_current_branch(self):
        employee = self.env_for(self.user_a)["hr.employee"].create({"name": "New"})
        self.assertEqual(employee.branch_id, self.branch_ahm)
        employee = self.env_for(self.user_multi, branch=self.branch_srt)["hr.employee"].create({"name": "New 2"})
        self.assertEqual(employee.branch_id, self.branch_srt)

    def test_department_branch_onchange(self):
        with Form(self.env_for(self.user_multi, branch=self.branch_ahm)["hr.employee"]) as form:
            form.name = "Worker"
            form.work_location_id = self.work_location
            self.assertEqual(form.branch_id, self.branch_ahm)
            form.department_id = self.dep_srt
            self.assertEqual(form.branch_id, self.branch_srt)

    def test_department_branch_company(self):
        with self.assertRaises(ValidationError):
            self.env["hr.department"].create({
                "name": "Wrong", "company_id": self.company_b.id, "branch_id": self.branch_ahm.id,
            })

    def test_unauthorized_branch_rejected(self):
        Employee = self.env_for(self.user_a)["hr.employee"]
        with self.assertRaises(ValidationError):
            Employee.create({"name": "X", "branch_id": self.branch_srt.id})
        with self.assertRaises(ValidationError):
            Employee.browse(self.emp_ahm.id).write({"branch_id": self.branch_srt.id})

    def test_other_company_branch_rejected(self):
        with self.assertRaises(ValidationError):
            self.env["hr.employee"].create({
                "name": "X", "company_id": self.company_a.id, "branch_id": self.branch_mum.id,
            })

    def test_hr_officer_branch_security(self):
        Employee = self.env_for(self.user_a)["hr.employee"]
        visible = Employee.search([("id", "in", self.all_employees.ids)])
        self.assertEqual(set(visible.ids), {self.emp_ahm.id, self.emp_shared.id})
        with self.assertRaises(AccessError):
            Employee.browse(self.emp_srt.id).read(["name", "private_email"])
        with self.assertRaises(AccessError):
            Employee.browse(self.emp_srt.id).write({"job_title": "Hacked"})
        with self.assertRaises(AccessError):
            Employee.browse(self.emp_srt.id).unlink()
        # the contract data (hr.version) of the hidden employee is protected too
        with self.assertRaises(AccessError):
            self.env_for(self.user_a)["hr.version"].browse(self.emp_srt.version_id.id).read(["wage"])
        # many2one values keep their display name (read as superuser by the ORM)
        emp_srt_b = self.env_for(self.user_b)["hr.employee"].browse(self.emp_srt.id)
        self.assertEqual(emp_srt_b.read(["parent_id"])[0]["parent_id"][1], "Ahmedabad Employee")

        admin_visible = self.env_for(self.branch_admin)["hr.employee"].search(
            [("id", "in", self.all_employees.ids)])
        self.assertEqual(admin_visible, self.all_employees)

    def test_directory_not_restricted(self):
        """Plain employees keep the company-wide directory (hr.employee.public)."""
        env = self.env_for(self.user_none)
        public = env["hr.employee.public"].search([("id", "in", self.all_employees.ids)])
        self.assertEqual(len(public), 3)
        self.assertEqual(env["hr.employee.public"].browse(self.emp_srt.id).branch_id, self.branch_srt)
        # hr.employee is served from the public model for non HR users
        employees = env["hr.employee"].search([("id", "in", self.all_employees.ids)])
        self.assertEqual(len(employees), 3)
        self.assertEqual(env["hr.employee"].browse(self.emp_srt.id).read(["name", "branch_id"])[0]["branch_id"][0],
                         self.branch_srt.id)
        # org chart: manager / subordinates across branches
        self.assertEqual(env["hr.employee.public"].browse(self.emp_ahm.id).child_ids.ids, [self.emp_srt.id])

    def test_user_linked_to_employee_in_other_branch(self):
        """A user whose employee is in a branch they are not allowed in keeps
        reading their own profile (related user fields are read as sudo)."""
        self.emp_srt.user_id = self.user_a
        me = self.env_for(self.user_a)["res.users"].browse(self.user_a.id)
        self.assertEqual(me.employee_id, self.emp_srt)
        self.assertTrue(me.read(["job_title", "work_email"]))

    def test_current_branch_filter(self):
        env = self.env_for(self.user_multi, branch=self.branch_srt)
        employees = env["hr.employee"].search([("is_current_branch", "=", True),
                                               ("id", "in", self.all_employees.ids)])
        self.assertEqual(employees, self.emp_srt)
        public = env["hr.employee.public"].search([("is_current_branch", "=", True),
                                                   ("id", "in", self.all_employees.ids)])
        self.assertEqual(public.ids, self.emp_srt.ids)

    def test_group_by_branch(self):
        groups = dict(self.env["hr.employee"]._read_group(
            [("id", "in", self.all_employees.ids)], ["branch_id"], ["__count"]))
        self.assertEqual(groups[self.branch_ahm], 1)
        self.assertEqual(groups[self.branch_srt], 1)
        result = self.env_for(self.user_a)["hr.employee"].formatted_read_group(
            [("id", "in", self.all_employees.ids)], ["branch_id"], ["__count"])
        self.assertEqual({group["branch_id"] and group["branch_id"][0] for group in result},
                         {self.branch_ahm.id, False})
        # public directory grouping
        result = self.env_for(self.user_none)["hr.employee.public"].formatted_read_group(
            [("id", "in", self.all_employees.ids)], ["branch_id"], ["__count"])
        self.assertEqual(len(result), 3)

    def test_branch_smart_button(self):
        branch = self.env_for(self.user_a)["res.branch"].browse(self.branch_ahm.id)
        self.assertEqual(branch.employee_count, 1)
        action = branch.action_view_employees()
        self.assertEqual(self.env["hr.employee"].search(action["domain"]), self.emp_ahm)
