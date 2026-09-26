import logging

from odoo import api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

# Groups exempted from the branch security boundary.
BRANCH_ADMIN_GROUP = "branch_management.group_branch_admin"


class ResUsers(models.Model):
    _inherit = "res.users"

    allowed_branch_ids = fields.Many2many(
        "res.branch",
        "res_branch_res_users_rel",
        "user_id",
        "branch_id",
        string="Allowed Branches",
        # archived branches stay in the security boundary so that historical
        # documents of an archived branch remain readable
        context={"active_test": False},
        help="Branches whose documents this user can access (security boundary).",
    )
    default_branch_id = fields.Many2one(
        "res.branch",
        string="Default Branch",
        user_writeable=True,
        help="Branch selected when no other working branch was chosen in the branch selector.",
    )
    current_branch_id = fields.Many2one(
        "res.branch",
        string="Current Branch",
        compute="_compute_current_branch_id",
        help="Working branch of the current session: the branch chosen in the "
        "branch selector if still valid, else the default branch.",
    )
    branch_unrestricted = fields.Boolean(
        compute="_compute_branch_unrestricted",
        compute_sudo=True,
        help="Technical: the branch security boundary does not apply to this "
        "user (branch administrators and external users, whose access is "
        "governed by their own rules).",
    )

    # ------------------------------------------------------------------
    # Computes
    # ------------------------------------------------------------------

    @api.depends("allowed_branch_ids", "default_branch_id")
    @api.depends_context("current_branch_id", "allowed_company_ids", "uid")
    def _compute_current_branch_id(self):
        for user in self:
            user.current_branch_id = user._get_current_branch()

    @api.depends("group_ids", "share")
    def _compute_branch_unrestricted(self):
        for user in self:
            user.branch_unrestricted = user._is_branch_unrestricted()

    def _is_branch_unrestricted(self):
        self.ensure_one()
        user = self.sudo()
        return user.share or user._has_group(BRANCH_ADMIN_GROUP)

    # ------------------------------------------------------------------
    # Current branch mechanism
    # ------------------------------------------------------------------

    def _get_selectable_branches(self, companies=None):
        """Branches the user may pick as working branch.

        Only active branches of the given companies (default: the companies
        currently enabled in the company switcher) are returned. Branch
        administrators may pick any branch of these companies.
        """
        self.ensure_one()
        companies = companies if companies is not None else self.env.companies
        Branch = self.env["res.branch"].sudo()
        if self._is_branch_unrestricted() and not self.share:
            return Branch.search([("company_id", "in", companies.ids)])
        return self.sudo().allowed_branch_ids.filtered(
            lambda branch: branch.active and branch.company_id in companies
        )

    def _get_current_branch(self, company=None):
        """Return the valid working branch of the user for ``company``.

        The branch requested by the client (context key
        ``current_branch_id``, set by the branch selector) is never trusted:
        it is only used if it is one of the selectable branches of the
        company. Otherwise fall back to the default branch, then to the first
        allowed branch of the company, then to no branch at all.
        """
        self.ensure_one()
        Branch = self.env["res.branch"]
        if not self.id or self.share:
            return Branch
        company = company or self.env.company
        selectable = self._get_selectable_branches(company)
        requested_id = self.env.context.get("current_branch_id")
        if requested_id:
            requested = selectable.filtered(lambda branch: branch.id == requested_id)
            if requested:
                return Branch.browse(requested.id)
            _logger.debug(
                "Branch validation failed: user %s requested branch %s outside of "
                "the selectable branches of company %s",
                self.id, requested_id, company.id,
            )
        if self.default_branch_id in selectable:
            return Branch.browse(self.default_branch_id.id)
        allowed = selectable & self.sudo().allowed_branch_ids
        return Branch.browse(allowed[:1].id)

    def _get_fallback_default_branch(self):
        """Valid default branch after a change of allowed branches/companies."""
        self.ensure_one()
        candidates = self.allowed_branch_ids.filtered(
            lambda branch: branch.active and branch.company_id in self.company_ids
        )
        if self.default_branch_id in candidates:
            return self.default_branch_id
        return (
            candidates.filtered(lambda branch: branch.company_id == self.company_id)[:1]
            or candidates[:1]
        )

    @api.model
    def switch_current_branch(self, branch_id):
        """Validate a branch chosen in the branch selector.

        Nothing is written in the database: the working branch lives in the
        browser session (cookie + user context). Returns the branch actually
        usable (which can differ from the requested one if it is invalid).
        """
        user = self.env.user
        branch = user.with_context(current_branch_id=branch_id)._get_current_branch()
        if branch.id != branch_id:
            _logger.info(
                "Branch validation failed: user %s cannot switch to branch %s", user.id, branch_id,
            )
        else:
            _logger.debug("Current branch changed: user %s -> branch %s", user.id, branch_id)
        return branch.id or False

    @api.model
    def _get_branch_session_info(self):
        """Branch data sent to the web client (see ir.http.session_info)."""
        user = self.env.user
        companies = self.env["res.company"].browse(user._get_company_ids())
        branches = user._get_selectable_branches(companies)
        default = user.default_branch_id if user.default_branch_id in branches else False
        return {
            "default_branch_id": default.id if default else False,
            "allowed_branches": [
                {
                    "id": branch.id,
                    "name": branch.name,
                    "display_name": branch.complete_name,
                    "code": branch.code,
                    "company_id": branch.company_id.id,
                    "allowed": branch in user.allowed_branch_ids,
                }
                for branch in branches
            ],
        }

    # ------------------------------------------------------------------
    # Constraints & CRUD
    # ------------------------------------------------------------------

    @api.constrains("allowed_branch_ids", "company_ids")
    def _check_allowed_branches_company(self):
        if self.env.context.get("branch_defer_company_check"):
            return
        for user in self:
            wrong = user.allowed_branch_ids.filtered(
                lambda branch: branch.company_id not in user.company_ids
            )
            if wrong:
                raise ValidationError(self.env._(
                    "User %(user)s cannot be allowed in branches %(branches)s: "
                    "they belong to companies the user has no access to.",
                    user=user.name,
                    branches=", ".join(wrong.mapped("display_name")),
                ))

    @api.constrains("default_branch_id", "allowed_branch_ids")
    def _check_default_branch(self):
        if self.env.context.get("branch_defer_default_check"):
            return
        for user in self:
            if user.default_branch_id and user.default_branch_id not in user.allowed_branch_ids:
                raise ValidationError(self.env._(
                    "The default branch of %(user)s must be one of their allowed branches.",
                    user=user.name,
                ))

    @api.model_create_multi
    def create(self, vals_list):
        users = super().create(vals_list)
        users._sanitize_branches()
        return users

    def write(self, vals):
        branch_fields = {"allowed_branch_ids", "company_ids", "company_id", "default_branch_id"}
        if not branch_fields & set(vals):
            return super().write(vals)
        # Removing an allowed branch (or a company) automatically fixes the
        # default branch and drops the branches of lost companies: defer the
        # related constraints until the sanitation is done. Explicitly
        # written values are still checked strictly.
        deferred = self.with_context(
            branch_defer_default_check="default_branch_id" not in vals,
            branch_defer_company_check="allowed_branch_ids" not in vals,
        )
        res = super(ResUsers, deferred).write(vals)
        self._sanitize_branches()
        self._check_allowed_branches_company()
        self._check_default_branch()
        if {"allowed_branch_ids", "group_ids"} & set(vals):
            self.env.transaction.invalidate_access_cache()
        return res

    def _sanitize_branches(self):
        """Keep allowed/default branches coherent with the user's companies.

        Runs as superuser: it only removes branches that became invalid for
        the user (company access lost) or fixes the default branch, which are
        consequences of a write the caller was already authorized to do.
        """
        for user in self.sudo():
            invalid = user.allowed_branch_ids.filtered(
                lambda branch: branch.company_id not in user.company_ids
            )
            if invalid:
                user.allowed_branch_ids = [fields.Command.unlink(b.id) for b in invalid]
            fallback = user._get_fallback_default_branch()
            if user.default_branch_id != fallback:
                user.default_branch_id = fallback

    def _get_invalidation_fields(self):
        # the security domains depend on the allowed branches
        return super()._get_invalidation_fields() | {"allowed_branch_ids"}
