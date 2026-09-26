from odoo import models


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    def session_info(self):
        result = super().session_info()
        user = self.env.user
        if result.get("uid") and user._is_internal():
            # sent with the session to avoid an extra RPC when the web client
            # starts; the data is informative only, the server re-validates
            # the working branch on every request
            result["user_branches"] = self.env["res.users"]._get_branch_session_info()
        return result
