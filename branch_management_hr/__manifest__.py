{
    "name": "Multi Branch Management - Employees",
    "version": "20.0.1.0.0",
    "category": "Human Resources/Employees",
    "summary": "Branch on employees and departments, branch security for HR officers",
    "author": "Branch Management Contributors",
    "website": "https://github.com/Adityashah1409/branch",
    "license": "LGPL-3",
    "depends": ["branch_management", "hr"],
    "data": [
        "security/ir.access.csv",
        "views/hr_employee_views.xml",
        "views/hr_employee_public_views.xml",
        "views/hr_department_views.xml",
        "views/res_branch_views.xml",
    ],
    "installable": True,
}
