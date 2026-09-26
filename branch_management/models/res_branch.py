import logging

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.fields import Domain

_logger = logging.getLogger(__name__)

# Code prefix of the ir.sequence records created on demand for branch
# numbering (see ``_get_next_sequence_number``).
BRANCH_SEQUENCE_CODE = "branch_management.branch.%(branch_id)s.%(doc_code)s"


class ResBranch(models.Model):
    """A branch (unit, office, store...) of a company.

    A branch is *not* a company: it always belongs to exactly one company and
    only adds a finer-grained dimension (and security boundary) inside it.
    """

    _name = "res.branch"
    _description = "Branch"
    _parent_name = "parent_id"
    _parent_store = True
    _rec_name = "complete_name"
    _order = "company_id, sequence, complete_name, id"
    _check_company_auto = True

    name = fields.Char(required=True, index="trigram", translate=False)
    complete_name = fields.Char(
        compute="_compute_complete_name",
        store=True,
        recursive=True,
        index=True,
    )
    code = fields.Char(
        required=True,
        index=True,
        help="Short code of the branch, unique inside a company (e.g. AHM). "
        "It is used as default prefix for branch-specific numbering.",
    )
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    company_id = fields.Many2one(
        "res.company",
        required=True,
        index=True,
        ondelete="restrict",
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(related="company_id.currency_id")
    parent_id = fields.Many2one(
        "res.branch",
        string="Parent Branch",
        index=True,
        ondelete="restrict",
        check_company=True,
    )
    parent_path = fields.Char(index=True)
    child_ids = fields.One2many("res.branch", "parent_id", string="Sub-branches")
    manager_id = fields.Many2one(
        "res.users",
        string="Manager",
        index="btree_not_null",
        domain="[('share', '=', False)]",
        check_company=True,
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Contact",
        help="Optional contact representing the branch (e.g. for deliveries).",
        check_company=True,
    )
    street = fields.Char()
    street2 = fields.Char()
    zip = fields.Char(change_default=True)
    city = fields.Char()
    state_id = fields.Many2one(
        "res.country.state",
        string="State",
        ondelete="restrict",
        domain="[('country_id', '=?', country_id)]",
    )
    country_id = fields.Many2one("res.country", string="Country", ondelete="restrict")
    phone = fields.Char()
    mobile = fields.Char()
    email = fields.Char()
    website = fields.Char()
    logo = fields.Image(max_width=512, max_height=512)
    sequence_prefix = fields.Char(
        help="Prefix used for branch-specific document numbering when it is "
        "enabled on the company (defaults to the branch code).",
    )
    user_ids = fields.Many2many(
        "res.users",
        "res_branch_res_users_rel",
        "branch_id",
        "user_id",
        string="Users",
        domain="[('share', '=', False)]",
        help="Users allowed to work in this branch.",
    )
    user_count = fields.Integer(compute="_compute_user_count", string="# Users")
    is_user_allowed = fields.Boolean(
        compute="_compute_is_user_allowed",
        search="_search_is_user_allowed",
        string="Is one of My Branches",
    )

    _code_company_uniq = models.UniqueIndex(
        "(company_id, lower(code))",
        "The branch code must be unique per company.",
    )

    # ------------------------------------------------------------------
    # Computes
    # ------------------------------------------------------------------

    @api.depends("name", "parent_id.complete_name")
    def _compute_complete_name(self):
        for branch in self:
            if branch.parent_id:
                branch.complete_name = f"{branch.parent_id.complete_name} / {branch.name}"
            else:
                branch.complete_name = branch.name

    @api.depends("user_ids")
    def _compute_user_count(self):
        for branch in self:
            branch.user_count = len(branch.user_ids)

    @api.depends_context("uid")
    def _compute_is_user_allowed(self):
        allowed = self.env.user.allowed_branch_ids
        for branch in self:
            branch.is_user_allowed = branch in allowed

    def _search_is_user_allowed(self, operator, value):
        if operator not in ("in", "not in"):
            return NotImplemented
        domain = Domain("id", "in", self.env.user.allowed_branch_ids.ids)
        positive = (operator == "in") == (True in value)
        return domain if positive else ~domain

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------

    @api.constrains("parent_id")
    def _check_parent_id(self):
        if self._has_cycle():
            raise ValidationError(self.env._("You cannot create recursive branch hierarchies."))
        for branch in self:
            if branch.parent_id and branch.parent_id.company_id != branch.company_id:
                raise ValidationError(self.env._(
                    "The parent branch %(parent)s must belong to the same company as %(branch)s.",
                    parent=branch.parent_id.display_name,
                    branch=branch.display_name,
                ))

    @api.constrains("company_id", "user_ids")
    def _check_users_company(self):
        for branch in self:
            wrong_users = branch.user_ids.filtered(
                lambda user: branch.company_id not in user.company_ids
            )
            if wrong_users:
                raise ValidationError(self.env._(
                    "Users %(users)s cannot be assigned to branch %(branch)s because they "
                    "are not allowed in its company %(company)s.",
                    users=", ".join(wrong_users.mapped("name")),
                    branch=branch.display_name,
                    company=branch.company_id.name,
                ))

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("code"):
                vals["code"] = vals["code"].strip().upper()
        branches = super().create(vals_list)
        if any(branch.user_ids for branch in branches):
            self._invalidate_branch_access()
        return branches

    def write(self, vals):
        if vals.get("code"):
            vals["code"] = vals["code"].strip().upper()
        if "company_id" in vals:
            for branch in self:
                if branch.company_id.id != vals["company_id"] and branch._has_dependent_records():
                    raise UserError(self.env._(
                        "You cannot move branch %s to another company because documents "
                        "already reference it.",
                        branch.display_name,
                    ))
        res = super().write(vals)
        if {"user_ids", "active", "company_id"} & set(vals):
            self._invalidate_branch_access()
        if "user_ids" in vals:
            # users removed from the branch can't keep it as default branch
            # (sudo: fixing a preference that the authorized write invalidated)
            orphans = self.env["res.users"].sudo().with_context(active_test=False).search([
                ("default_branch_id", "in", self.ids),
                ("allowed_branch_ids", "not in", self.ids),
            ])
            orphans._sanitize_branches()
        if vals.get("active") is False:
            self._reset_users_default_branch()
        return res

    def copy_data(self, default=None):
        default = dict(default or {})
        vals_list = super().copy_data(default=default)
        for branch, vals in zip(self, vals_list):
            if "name" not in default:
                vals["name"] = self.env._("%s (copy)", branch.name)
            if "code" not in default:
                vals["code"] = branch._get_copy_code()
            # users are not duplicated: access to a new branch must be granted
            vals.pop("user_ids", None)
        return vals_list

    def _get_copy_code(self):
        self.ensure_one()
        existing = set(
            self.with_context(active_test=False)
            .search([("company_id", "=", self.company_id.id)])
            .mapped("code")
        )
        index = 1
        while (code := f"{self.code}{index}") in existing:
            index += 1
        return code

    @api.ondelete(at_uninstall=False)
    def _unlink_except_used(self):
        for branch in self:
            if branch._has_dependent_records():
                raise UserError(self.env._(
                    "Branch %s is used by existing documents and cannot be deleted. "
                    "Archive it instead to keep its history.",
                    branch.display_name,
                ))

    def unlink(self):
        res = super().unlink()
        self._invalidate_branch_access()
        return res

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @api.model
    def _get_branch_reference_fields(self):
        """Return the stored many2one fields (of real tables) pointing to
        res.branch, excluding the branch hierarchy itself."""
        result = []
        for model in self.env.registry.values():
            if model._abstract or not model._auto or model._name == self._name:
                continue
            for field in model._fields.values():
                if (
                    field.type == "many2one"
                    and field.comodel_name == self._name
                    and field.store
                    and not field.inherited
                ):
                    result.append(field)
        return result

    def _has_dependent_records(self):
        """Whether documents reference this branch.

        Uses sudo(): the check must see every document regardless of the
        current user's access, otherwise a user could delete a branch that
        is used by documents they cannot read.
        """
        self.ensure_one()
        for field in self._get_branch_reference_fields():
            model = self.env[field.model_name].sudo().with_context(active_test=False)
            if model.search_count([(field.name, "=", self.id)], limit=1):
                return True
        return False

    def _reset_users_default_branch(self):
        """Archived branches can't stay the default branch of a user."""
        users = self.env["res.users"].sudo().with_context(active_test=False).search(
            [("default_branch_id", "in", self.ids)]
        )
        for user in users:
            user.default_branch_id = user._get_fallback_default_branch()

    def _invalidate_branch_access(self):
        """Security domains depend on users' allowed branches: flush caches."""
        self.env.transaction.invalidate_access_cache()
        self.env.transaction.invalidate_ormcache()

    def _get_address_lines(self):
        """Return the non-empty address lines of the branch, for reports."""
        self.ensure_one()
        city_line = " ".join(filter(None, [self.zip, self.city]))
        return [
            line for line in (
                self.street,
                self.street2,
                city_line,
                self.state_id.name,
                self.country_id.name,
            ) if line
        ]

    def _get_next_sequence_number(self, doc_code, doc_prefix, padding=5):
        """Return the next number of a branch-specific sequence.

        Example: branch AHM, doc_prefix 'SO' -> ``AHM/SO/00001``.

        The sequence is created on demand. sudo() is used because creating
        and consuming technical ir.sequence records is not something business
        users are granted, while the branch itself was already validated for
        the current user by the caller (the document's branch constraint).
        Sequences use the 'standard' implementation (PostgreSQL sequence):
        numbering is concurrency safe but may contain gaps on rollback.
        """
        self.ensure_one()
        code = BRANCH_SEQUENCE_CODE % {"branch_id": self.id, "doc_code": doc_code}
        IrSequence = self.env["ir.sequence"].sudo()
        sequence = IrSequence.search(
            [("code", "=", code), ("company_id", "=", self.company_id.id)], limit=1
        )
        if not sequence:
            prefix = (self.sequence_prefix or self.code or "").strip()
            sequence = IrSequence.create({
                "name": f"{self.display_name} - {doc_prefix}",
                "code": code,
                "prefix": f"{prefix}/{doc_prefix}/",
                "padding": padding,
                "company_id": self.company_id.id,
                "implementation": "standard",
            })
        return sequence.next_by_id()

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_view_users(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Users"),
            "res_model": "res.users",
            "view_mode": "list,form",
            "domain": [("id", "in", self.user_ids.ids)],
            "context": {"create": False},
        }

    def _get_records_action(self, name, res_model, domain=None, context=None):
        """Helper for integration modules' smart buttons."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": name,
            "res_model": res_model,
            "view_mode": "list,form",
            "domain": Domain.AND([[("branch_id", "=", self.id)], domain or []]),
            "context": dict(context or {}, default_branch_id=self.id),
        }
