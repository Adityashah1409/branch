# Multi Branch Management - Contacts

Links contacts (customers, vendors) to branches (Odoo 20.0). Depends only on
`branch_management` (`res.partner` is in `base`).

## Features

* `res.partner.branch_ids`: a contact can work with several branches; an
  **empty** value means the contact is shared by every branch.
* *My Branches* search filter: contacts without branch or linked to one of
  the user's allowed branches (searchable computed field `in_my_branches`;
  every contact for branch administrators). *Branch* group-by and column.
* Company setting **Default Contact Branch** (`res.company.branch_partner_default`,
  off by default, in *Settings > Branches*): contacts created from a contact
  form get the creator's working branch. Contacts created by code (users,
  incoming emails, imports, portal sign-up) never get one.
* **Smart button** *Contacts* on the branch form.
* Validation: branches must belong to the contact's company (when it has
  one) and a user can only add branches they are allowed in (branches linked
  by others are kept when they edit the contact).

## Why contacts are not a security boundary

Contacts are shared, structural data: every user is a partner, companies are
partners, and messaging, followers, activities, invoices, deliveries,
portal access and the address book all read them, often through other
records. Hiding contacts per branch with `ir.access` would break chatter
(authors and followers from other branches), user and company management,
and any document of a visible branch whose customer is also linked to
another branch. So branches on contacts are **organisational only**: use the
*My Branches* filter to focus the list. Sensitive documents (orders,
invoices, leads...) are protected by the branch restrictions of their own
integration modules.

`branch_ids` is restricted to internal users (`groups="base.group_user"`):
portal and public users cannot read branches.
