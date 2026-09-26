{
    "name": "Multi Branch Management",
    "version": "20.0.1.0.0",
    "category": "Administration",
    "summary": "Manage multiple branches (units) inside one company: "
               "branch master, user access, branch switching and branch security",
    "description": """
Multi Branch Management
=======================

Foundation module of the branch framework. It provides:

* the ``res.branch`` model (hierarchy, code unique per company, address, logo)
* allowed / default / current branch on users
* branch security groups (User, Manager, Administrator)
* a systray branch selector that sets the working branch per browser session
* ``res.branch.mixin``: the reusable abstract model that integration modules
  use to make a document branch-aware (default value, validations, filters)
* optional branch-specific sequence prefixes

Application integrations (sales, purchase, inventory, accounting, ...) live
in separate ``branch_management_*`` modules.
""",
    "author": "Branch Management Contributors",
    "website": "https://github.com/Adityashah1409/branch",
    "license": "LGPL-3",
    "depends": ["base", "web", "base_setup"],
    "data": [
        "security/branch_security.xml",
        "security/ir.access.csv",
        "wizard/branch_user_assign_views.xml",
        "views/res_branch_views.xml",
        "views/res_users_views.xml",
        "views/res_config_settings_views.xml",
        "views/branch_menus.xml",
        "report/branch_report_templates.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "branch_management/static/src/branch_selector/*",
        ],
        "web.assets_tests": [
            "branch_management/static/tests/tours/*",
        ],
    },
    "installable": True,
    "application": True,
    "uninstall_hook": "uninstall_hook",
}
