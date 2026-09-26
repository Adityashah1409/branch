import logging

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.fields import Domain

_logger = logging.getLogger(__name__)


class ResBranchMixin(models.AbstractModel):
    """Make a model branch-aware.

    Inheriting models get:

    * ``branch_id``: defaults to the user's current (working) branch when it
      belongs to the document's default company;
    * validations: the branch must belong to the document's company and must
      be one of the user's allowed branches (server side, whatever the client
      sends);
    * ``is_current_branch``: searchable flag used by the "Current Branch"
      filters (the working context of security mode C).

    The *security boundary* itself is an ``ir.access`` restriction declared by
    each integration module on its models (see ``BRANCH_ACCESS_DOMAIN`` in the
    documentation), so that it applies to every ORM / RPC access, not only to
    the UI.
    """

    _name = "res.branch.mixin"
    _description = "Branch-aware Document"

    branch_id = fields.Many2one(
        "res.branch",
        string="Branch",
        index="btree_not_null",
        ondelete="restrict",
        check_company=True,
        default=lambda self: self._default_branch_id(),
    )
    is_current_branch = fields.Boolean(
        string="In Current Branch",
        compute="_compute_is_current_branch",
        search="_search_is_current_branch",
    )

    @api.model
    def _default_branch_id(self):
        company = self._branch_default_company()
        return self.env.user._get_current_branch(company)

    @api.model
    def _branch_default_company(self):
        """Company used to pick the default branch of a new record."""
        company_id = self.env.context.get("default_company_id")
        if company_id:
            return self.env["res.company"].browse(company_id)
        return self.env.company

    @api.depends("branch_id")
    @api.depends_context("current_branch_id", "allowed_company_ids", "uid")
    def _compute_is_current_branch(self):
        current = self.env.user._get_current_branch()
        for record in self:
            record.is_current_branch = record.branch_id == current

    def _search_is_current_branch(self, operator, value):
        if operator not in ("in", "not in"):
            return NotImplemented
        current = self.env.user._get_current_branch()
        domain = Domain("branch_id", "=", current.id or False)
        positive = (operator == "in") == (True in value)
        return domain if positive else ~domain

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def _branch_company(self):
        """Company the branch of this record must belong to (False: any)."""
        self.ensure_one()
        return self["company_id"] if "company_id" in self._fields else False

    @api.constrains("branch_id")
    def _check_branch_consistency(self):
        self._check_branch_company_match()
        self._check_branch_user_access()

    def _check_branch_company_match(self):
        for record in self:
            company = record._branch_company()
            if record.branch_id and company and record.branch_id.company_id != company:
                _logger.info(
                    "Cross-company branch mismatch on %s: branch %s (company %s) vs company %s",
                    record, record.branch_id.id, record.branch_id.company_id.id, company.id,
                )
                raise ValidationError(self.env._(
                    "Branch %(branch)s belongs to company %(branch_company)s, "
                    "but %(document)s belongs to company %(company)s.",
                    branch=record.branch_id.display_name,
                    branch_company=record.branch_id.company_id.name,
                    document=record.display_name,
                    company=company.name,
                ))

    def _check_branch_user_access(self):
        """The branch set on a document must be allowed for the user.

        Skipped in sudo mode: server-side flows (crons, automatic document
        generation) are already authorized by the business action that
        triggered them.
        """
        if self.env.su:
            return
        user = self.env.user
        if user._is_branch_unrestricted():
            return
        allowed = user.allowed_branch_ids
        for record in self:
            if record.branch_id and record.branch_id not in allowed:
                _logger.info(
                    "Unauthorized branch access: user %s tried to use branch %s on %s",
                    user.id, record.branch_id.id, record._name,
                )
                raise ValidationError(self.env._(
                    "You are not allowed to use branch %(branch)s.",
                    branch=record.branch_id.display_name,
                ))

    def _branch_sync_with_company(self):
        """Reset the branch when it does not match the record's company.

        Call it from an ``@api.onchange('company_id')`` in models that have
        a company field (not declared here since the mixin can be used on
        models without company).
        """
        for record in self:
            company = record._branch_company()
            if record.branch_id and company and record.branch_id.company_id != company:
                record.branch_id = record.env.user._get_current_branch(company)
