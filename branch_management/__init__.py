from . import models
from . import wizard


def uninstall_hook(env):
    """Drop the per-branch sequences created on demand by the module.

    They are technical records owned by no module (created with sudo when a
    document is numbered), so the ORM would otherwise leave them behind.
    """
    env["ir.sequence"].sudo().search(
        [("code", "=like", "branch_management.branch.%")]
    ).unlink()
