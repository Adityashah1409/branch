import { cookie } from "@web/core/browser/cookie";
import { rpc } from "@web/core/network/rpc";
import { registry } from "@web/core/registry";
import { user } from "@web/core/user";
import { session } from "@web/session";

export const BRANCH_COOKIE = "branch_id";

/**
 * Pick the working branch for the active company.
 *
 * Only branches of the active (first) company are candidates, because new
 * documents are created in that company. The cookie value is only a hint:
 * the server validates the branch again on every request.
 */
export function computeCurrentBranch(branches, companyId, cookieBranchId, defaultBranchId) {
    const candidates = branches.filter((b) => b.company_id === companyId);
    return (
        candidates.find((b) => b.id === cookieBranchId) ||
        candidates.find((b) => b.id === defaultBranchId) ||
        candidates.find((b) => b.allowed) ||
        null
    );
}

export const branchService = {
    start() {
        const info = session.user_branches || { allowed_branches: [], default_branch_id: false };
        delete session.user_branches;
        const companyIds = (user.activeCompanies || []).map((c) => c.id);
        const activeCompanyId = user.activeCompany?.id;
        // branches of every enabled company are listed; only the ones of the
        // active company can become the working branch
        const branches = info.allowed_branches.filter((b) => companyIds.includes(b.company_id));
        const cookieBranchId = parseInt(cookie.get(BRANCH_COOKIE) || "0", 10);
        let current = computeCurrentBranch(
            branches,
            activeCompanyId,
            cookieBranchId,
            info.default_branch_id
        );
        if (current) {
            user.updateContext({ current_branch_id: current.id });
        }
        if (current?.id !== cookieBranchId) {
            // the stored branch is invalid for the active company: forget it
            if (current) {
                cookie.set(BRANCH_COOKIE, String(current.id));
            } else {
                cookie.delete(BRANCH_COOKIE);
            }
        }

        return {
            get branches() {
                return branches;
            },
            get currentBranch() {
                return current;
            },
            get activeCompanyBranches() {
                return branches.filter((b) => b.company_id === activeCompanyId);
            },
            /**
             * Ask the server to validate the branch, then store it for the
             * browser session. No database write happens.
             */
            async switchBranch(branchId) {
                const validId = await rpc("/web/dataset/call_kw/res.users/switch_current_branch", {
                    model: "res.users",
                    method: "switch_current_branch",
                    args: [branchId],
                    kwargs: { context: user.context },
                });
                const branch = branches.find((b) => b.id === validId) || null;
                current = branch;
                if (branch) {
                    cookie.set(BRANCH_COOKIE, String(branch.id));
                    user.updateContext({ current_branch_id: branch.id });
                } else {
                    cookie.delete(BRANCH_COOKIE);
                    user.updateContext({ current_branch_id: false });
                }
                return branch;
            },
        };
    },
};

registry.category("services").add("branch", branchService);
