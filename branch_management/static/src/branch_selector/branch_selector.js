import { Component } from "@odoo/owl";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { router } from "@web/core/browser/router";
import { useService } from "@web/core/utils/hooks";

export class BranchSelector extends Component {
    static template = "branch_management.BranchSelector";
    static components = { Dropdown, DropdownItem };

    setup() {
        this.branchService = useService("branch");
        this.notification = useService("notification");
    }

    get branches() {
        return this.branchService.activeCompanyBranches;
    }

    get currentBranch() {
        return this.branchService.currentBranch;
    }

    get title() {
        return this.currentBranch
            ? _t("Current branch: %s", this.currentBranch.display_name)
            : _t("No branch selected");
    }

    isCurrent(branch) {
        return this.currentBranch?.id === branch.id;
    }

    async selectBranch(branch) {
        if (this.isCurrent(branch)) {
            return;
        }
        const result = await this.branchService.switchBranch(branch.id);
        if (!result || result.id !== branch.id) {
            this.notification.add(_t("You cannot work in branch %s.", branch.display_name), {
                type: "danger",
            });
        }
        // reload the current view so that defaults and "current branch"
        // filters use the new working branch
        router.pushState({}, { reload: true });
    }
}

export const branchSelectorItem = {
    Component: BranchSelector,
    isDisplayed: (env) => env.services.branch.activeCompanyBranches.length > 0,
};

registry.category("systray").add("BranchSelector", branchSelectorItem, { sequence: 2 });
