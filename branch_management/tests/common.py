from odoo.tests import TransactionCase, new_test_user


class BranchTestCommon(TransactionCase):
    """Shared fixtures: two companies, a branch tree and users.

    Company A: Head Office > Gujarat > (Ahmedabad, Surat)
    Company B: Mumbai, Pune
    Nothing depends on demo data.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Branch = cls.env["res.branch"]
        cls.company_a = cls.env["res.company"].create({"name": "Branch Test Company A"})
        cls.company_b = cls.env["res.company"].create({"name": "Branch Test Company B"})

        cls.branch_ho = cls.Branch.create({
            "name": "Head Office", "code": "HO", "company_id": cls.company_a.id,
        })
        cls.branch_guj = cls.Branch.create({
            "name": "Gujarat", "code": "GUJ", "company_id": cls.company_a.id,
            "parent_id": cls.branch_ho.id,
        })
        cls.branch_ahm = cls.Branch.create({
            "name": "Ahmedabad", "code": "AHM", "company_id": cls.company_a.id,
            "parent_id": cls.branch_guj.id,
        })
        cls.branch_srt = cls.Branch.create({
            "name": "Surat", "code": "SRT", "company_id": cls.company_a.id,
            "parent_id": cls.branch_guj.id,
        })
        cls.branch_mum = cls.Branch.create({
            "name": "Mumbai", "code": "MUM", "company_id": cls.company_b.id,
        })
        cls.branch_pun = cls.Branch.create({
            "name": "Pune", "code": "PUN", "company_id": cls.company_b.id,
        })

        companies_ab = [(6, 0, (cls.company_a | cls.company_b).ids)]
        cls.user_a = new_test_user(
            cls.env, login="branch_user_a", groups="base.group_user",
            company_id=cls.company_a.id, company_ids=[(6, 0, cls.company_a.ids)],
            allowed_branch_ids=[(6, 0, cls.branch_ahm.ids)],
        )
        cls.user_b = new_test_user(
            cls.env, login="branch_user_b", groups="base.group_user",
            company_id=cls.company_a.id, company_ids=[(6, 0, cls.company_a.ids)],
            allowed_branch_ids=[(6, 0, cls.branch_srt.ids)],
        )
        cls.user_multi = new_test_user(
            cls.env, login="branch_user_multi", groups="base.group_user",
            company_id=cls.company_a.id, company_ids=companies_ab,
            allowed_branch_ids=[(6, 0, (cls.branch_ahm | cls.branch_srt | cls.branch_mum).ids)],
            default_branch_id=cls.branch_ahm.id,
        )
        cls.user_none = new_test_user(
            cls.env, login="branch_user_none", groups="base.group_user",
            company_id=cls.company_a.id, company_ids=[(6, 0, cls.company_a.ids)],
        )
        cls.manager = new_test_user(
            cls.env, login="branch_manager", groups="base.group_user,branch_management.group_branch_manager",
            company_id=cls.company_a.id, company_ids=[(6, 0, cls.company_a.ids)],
            allowed_branch_ids=[(6, 0, (cls.branch_ahm | cls.branch_srt).ids)],
        )
        cls.branch_admin = new_test_user(
            cls.env, login="branch_admin", groups="base.group_user,branch_management.group_branch_admin",
            company_id=cls.company_a.id, company_ids=companies_ab,
        )

    def env_for(self, user, company=None, branch=None, companies=None):
        """Environment of ``user`` as the web client would build it."""
        companies = companies or company or user.company_id
        context = {"allowed_company_ids": companies.ids}
        if branch is not None:
            context["current_branch_id"] = branch.id if branch else False
        return self.env(user=user, context=dict(self.env.context, **context))
