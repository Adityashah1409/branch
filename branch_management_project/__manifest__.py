{
    "name": "Multi Branch Management - Project",
    "version": "20.0.1.0.0",
    "category": "Services/Project",
    "summary": "Branch on projects and tasks, branch security and reporting for Project",
    "author": "Branch Management Contributors",
    "website": "https://github.com/Adityashah1409/branch",
    "license": "LGPL-3",
    "depends": ["branch_management", "project"],
    "data": [
        "security/ir.access.csv",
        "views/project_project_views.xml",
        "views/project_task_views.xml",
        "views/res_branch_views.xml",
        "report/project_report_views.xml",
    ],
    "installable": True,
}
