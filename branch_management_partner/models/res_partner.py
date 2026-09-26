from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.fields import Domain

# context key set while the web client computes the defaults of a new
# contact form (see ``onchange``)
FORM_DEFAULTS_KEY = "branch_partner_form_defaults"


class ResPartner(models.Model):
    """Branches of a contact.

    This is *informative*: contacts are shared data (users, companies,
    messaging, accounting all read them), so branches never restrict their
    visibility. An empty ``branch_ids`` means "shared by every branch".
    """

    _inherit = "res.partner"

    branch_ids = fields.Many2many(
        "res.branch",
        "res_partner_res_branch_rel",
        "partner_id",
        "branch_id",
        string="Branches",
        default=lambda self: self._default_branch_ids(),
        domain="company_id and [('company_id', '=', company_id)] or []",
        # external users have no access to branches
        groups="base.group_user",
        help="Branches working with this contact. Leave empty to share it "
        "with every branch.",
    )
    in_my_branches = fields.Boolean(
        string="In My Branches",
        compute="_compute_in_my_branches",
        search="_search_in_my_branches",
        groups="base.group_user",
    )

    # ------------------------------------------------------------------
    # Defaults
    # ------------------------------------------------------------------

    @api.model
    def _default_branch_ids(self):
        """Working branch of the user, for contacts created from a form.

        Only when the company enables it, and never for contacts created by
        code (user creation, incoming emails, imports...).
        """
        if not self.env.context.get(FORM_DEFAULTS_KEY) or self.env.su:
            return self.env["res.branch"]
        company_id = self.env.context.get("default_company_id")
        company = self.env["res.company"].browse(company_id) if company_id else self.env.company
        if not company.branch_partner_default:
            return self.env["res.branch"]
        return self.env.user._get_current_branch(company)

    def onchange(self, values, field_names, fields_spec):
        # first call for a new record: the client asks for the default values
        if not field_names and not self:
            self = self.with_context(**{FORM_DEFAULTS_KEY: True})  # noqa: PLW0642
        return super().onchange(values, field_names, fields_spec)

    # ------------------------------------------------------------------
    # "My Branches" filter
    # ------------------------------------------------------------------

    @api.depends("branch_ids")
    @api.depends_context("uid")
    def _compute_in_my_branches(self):
        user = self.env.user
        unrestricted = user._is_branch_unrestricted()
        allowed = user.allowed_branch_ids
        for partner in self:
            partner.in_my_branches = (
                unrestricted or not partner.branch_ids or bool(partner.branch_ids & allowed)
            )

    def _search_in_my_branches(self, operator, value):
        if operator not in ("in", "not in"):
            return NotImplemented
        user = self.env.user
        if user._is_branch_unrestricted():
            domain = Domain.TRUE
        else:
            domain = Domain("branch_ids", "=", False) | Domain(
                "branch_ids", "in", user.allowed_branch_ids.ids
            )
        positive = (operator == "in") == (True in value)
        return domain if positive else ~domain

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    @api.constrains("branch_ids", "company_id")
    def _check_branch_company(self):
        for partner in self:
            if not partner.company_id:
                continue
            wrong = partner.branch_ids.filtered(lambda b: b.company_id != partner.company_id)
            if wrong:
                raise ValidationError(self.env._(
                    "Contact %(partner)s belongs to company %(company)s: it cannot be "
                    "linked to branches of another company (%(branches)s).",
                    partner=partner.display_name,
                    company=partner.company_id.name,
                    branches=", ".join(wrong.mapped("display_name")),
                ))

    @api.model_create_multi
    def create(self, vals_list):
        partners = super().create(vals_list)
        if any("branch_ids" in vals for vals in vals_list):
            # sudo: see every linked branch, including those of companies the
            # user cannot read, so that they are checked too
            partners._check_added_branches_allowed(partners.sudo().branch_ids)
        return partners

    def write(self, vals):
        if "branch_ids" not in vals:
            return super().write(vals)
        # sudo: compare the complete link sets, including branches of other
        # companies the user cannot read (read-only technical access)
        before = {partner.id: partner.sudo().branch_ids for partner in self}
        res = super().write(vals)
        added = self.env["res.branch"]
        for partner in self:
            added |= partner.sudo().branch_ids - before[partner.id]
        self._check_added_branches_allowed(added)
        return res

    def _check_added_branches_allowed(self, branches):
        """A user may only link contacts to branches they are allowed in.

        Branches already linked by someone else are kept untouched. Done in
        create/write rather than in a constraint: Odoo 20 runs constraint
        methods as superuser, which would hide the user.
        """
        if self.env.su or not branches:
            return
        user = self.env.user
        if user._is_branch_unrestricted():
            return
        forbidden = branches - user.allowed_branch_ids
        if forbidden:
            raise ValidationError(self.env._(
                "You are not allowed to use branch %(branch)s.",
                # sudo: only the name of a branch the user submitted is disclosed
                branch=forbidden[:1].sudo().display_name,
            ))
