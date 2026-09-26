{
    "name": "Multi Branch Management - CRM",
    "version": "20.0.1.0.0",
    "category": "Sales/CRM",
    "summary": "Branch on leads and opportunities, branch-dedicated sales teams, "
               "branch security and reporting for CRM",
    "author": "Branch Management Contributors",
    "website": "https://github.com/Adityashah1409/branch",
    "license": "LGPL-3",
    "depends": ["branch_management", "crm"],
    "data": [
        "security/ir.access.csv",
        "views/crm_lead_views.xml",
        "views/crm_team_views.xml",
        "views/res_branch_views.xml",
        "report/crm_activity_report_views.xml",
    ],
    "installable": True,
}
