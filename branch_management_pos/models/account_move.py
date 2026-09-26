from odoo import api, models

from .pos_session import POS_BRANCH_CONTEXT_KEY

POS_SESSION_FIELDS = ("pos_session_sales_id", "pos_session_refunds_id", "pos_session_correction_id")


def _linked_ids(commands):
    """Ids linked by x2many ``commands`` (link / set)."""
    ids = []
    for command in commands or ():
        if isinstance(command, (list, tuple)):
            if command[0] == 4:
                ids.append(command[1])
            elif command[0] == 6:
                ids.extend(command[2])
        elif isinstance(command, int):
            ids.append(command)
    return ids


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.model_create_multi
    def create(self, vals_list):
        # PoS entries are created in sudo, where the mixin default would be
        # the working branch of the user closing the session: use the branch
        # of the PoS order / session instead.
        for vals in vals_list:
            if "branch_id" not in vals:
                branch = self._get_pos_branch_from_vals(vals)
                if branch is not None:
                    vals["branch_id"] = branch.id
        return super().create(vals_list)

    @api.model
    def _get_pos_branch_from_vals(self, vals):
        """Branch of the PoS document the entry comes from, ``None`` when the
        values do not come from a PoS flow.

        sudo(): only the branch of the PoS order / session referenced by the
        values of the entry being created is read; nothing is returned to the
        caller but that branch, which the entry is created with.
        """
        if vals.get("reversed_pos_order_id"):
            return self.env["pos.order"].sudo().browse(vals["reversed_pos_order_id"]).branch_id
        session_ids = [vals[fname] for fname in POS_SESSION_FIELDS if vals.get(fname)]
        session_ids += _linked_ids(vals.get("pos_session_ids"))
        if session_ids:
            return self.env["pos.session"].sudo().browse(session_ids[0]).branch_id
        if POS_BRANCH_CONTEXT_KEY in self.env.context:
            return self.env["res.branch"].browse(self.env.context[POS_BRANCH_CONTEXT_KEY])
        return None
