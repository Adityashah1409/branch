import logging

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class PosConfig(models.Model):
    _name = "pos.config"
    _inherit = ["pos.config", "res.branch.mixin"]

    branch_id = fields.Many2one(
        help="Branch operating this shop. Its sessions, orders, payments, invoices and "
        "session closing entries belong to this branch.",
    )

    @api.onchange("company_id")
    def _onchange_company_id_branch(self):
        self._branch_sync_with_company()

    def write(self, vals):
        if "branch_id" in vals:
            self._check_branch_change_allowed(vals["branch_id"])
        return super().write(vals)

    def _check_branch_change_allowed(self, new_branch_id):
        """Refuse to move a shop with a session in progress to another branch.

        Uses sudo(): the check must see every session of the shops, whatever
        the branches the user may read; only a count is computed.
        """
        changed = self.filtered(lambda config: config.branch_id.id != (new_branch_id or False))
        if not changed:
            return
        ongoing = self.env["pos.session"].sudo().search_count([
            ("config_id", "in", changed.ids), ("state", "!=", "closed"),
        ], limit=1)
        if ongoing:
            raise UserError(self.env._(
                "You cannot change the branch of %s while a session is in progress. "
                "Close the session first.",
                ", ".join(changed.mapped("display_name")),
            ))

    @api.constrains("branch_id", "journal_id", "closing_journal_id", "payment_method_ids")
    def _check_journals_branch(self):
        for config in self:
            journals = (
                config.journal_id | config.closing_journal_id | config.payment_method_ids.journal_id
            )
            foreign = journals.filtered(
                lambda journal: journal.branch_id and journal.branch_id != config.branch_id
            )
            if foreign:
                _logger.info(
                    "Branch mismatch on PoS %s: branch %s vs journals %s",
                    config.id, config.branch_id.id, foreign.ids,
                )
                raise ValidationError(self.env._(
                    "Point of Sale %(config)s (branch: %(branch)s) cannot use journal(s) "
                    "%(journals)s dedicated to another branch.",
                    config=config.display_name,
                    branch=config.branch_id.display_name or self.env._("none"),
                    journals=", ".join(foreign.mapped("display_name")),
                ))

    @api.constrains("branch_id", "trusted_config_ids")
    def _check_trusted_configs_branch(self):
        # the shop pushes its open orders to the sessions of the trusted
        # shops: their cashiers must be allowed to read them
        for config in self:
            foreign = config.trusted_config_ids.filtered(
                lambda other: other.branch_id and other.branch_id != config.branch_id
            )
            if foreign:
                raise ValidationError(self.env._(
                    "Point of Sale %(config)s can only share its orders with shops of its "
                    "own branch (%(branch)s): %(others)s.",
                    config=config.display_name,
                    branch=config.branch_id.display_name or self.env._("none"),
                    others=", ".join(foreign.mapped("display_name")),
                ))
