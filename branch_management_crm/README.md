# Multi Branch Management - CRM

Integration of `branch_management` with the CRM application (Odoo 20.0).

## Features

* **Branch on leads and opportunities** (`crm.lead.branch_id`, tracked).
* **Branch-dedicated sales teams**: optional `crm.team.branch_id`.
* **Branch security**: leads of a branch are only visible to users allowed in
  that branch (branch administrators see everything). Leads without branch
  stay visible to everybody allowed by the other CRM rules.
* **Reporting**: branch column in lead/opportunity lists, `Branch` search
  field, *Current Branch* filter and *Branch* group-by on the lead, pipeline
  and pipeline analysis (pivot/graph) search views; `branch_id` added to the
  *Activities Analysis* SQL report (`crm.activity.report`), with the same
  restriction.
* **Smart button** *Leads/Opportunities* on the branch form (salesmen only).

## How the branch of a lead is chosen

`crm.lead.branch_id` is a stored, editable computed field (precomputed at
creation, depends on the sales team):

1. an explicit value (form, import, RPC, `default_branch_id` context) always wins;
2. otherwise, if the lead's sales team is dedicated to a branch (of the
   lead's company), the lead goes to that branch;
3. otherwise the branch already set is kept (if it belongs to the lead's company);
4. otherwise a new lead gets the user's current (working) branch.

Changing the team of an existing lead to a team dedicated to a branch moves
the lead to that branch; changing it to a team without branch keeps the
branch. This was preferred over an onchange on the team because it also
applies to leads created by code (website forms, mail gateway, assignment):
the team is the business signal CRM itself uses to route leads.

A team dedicated to a branch must belong to the branch's company (choosing a
branch on a team without company sets the company).

When opportunities are merged, the result keeps the branch of the first lead
having one.

## Security

`security/ir.access.csv` declares group-less `ir.access` **restrictions**
(AND-ed with the CRM permissions) on `crm.lead` and `crm.activity.report`:

```
[] if user.branch_unrestricted else
['|', ('branch_id', '=', False), ('branch_id', 'in', user.allowed_branch_ids.ids)]
```

Leads may have no company in CRM ("visible to all"), so the branch field does
not use `check_company`: the branch/company consistency is enforced by the
`res.branch.mixin` constraint whenever the lead has a company.

Using a branch the user is not allowed in raises a `ValidationError`
(explicit values) or an `AccessError` (branch coming from a dedicated team,
refused by the restriction).
