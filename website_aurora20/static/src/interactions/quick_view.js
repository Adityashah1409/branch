import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { BootstrapInstance } from "@web/core/utils/bootstrap_plugin";
import { usePlugin } from "@odoo/owl";
import { replaceContent, showError, userErrorMessage } from "@website_aurora20/js/storefront_utils";

/**
 * Product quick view.
 *
 * One instance lives on the (single) dialog of the page; the "Quick view"
 * buttons of the product tiles are handled by delegation, so tiles re-rendered
 * by the shop filters keep working without new listeners.
 */
export class AuroraQuickView extends Interaction {
    static selector = "#o_aurora_quick_view";
    dynamicContent = {
        _document: { "t-on-click": this.onDocumentClick },
        _root: {
            "t-on-shown.bs.modal": this.onShown,
            "t-on-hidden.bs.modal": this.onHidden,
        },
        ".o_aurora_quick_view_body": {
            "t-on-change": this.onVariantChange,
            "t-on-click": this.onBodyClick,
            "t-on-product_added_to_cart": this.onAddedToCart,
        },
    };

    setup() {
        this.bootstrap = usePlugin(BootstrapInstance);
        this.bodyEl = this.el.querySelector(".o_aurora_quick_view_body");
        this.titleEl = this.el.querySelector("#o_aurora_quick_view_title");
        this.loadingHtml = this.bodyEl.innerHTML;
        this.triggerEl = null;
        this.productTemplateId = null;
        // Ignore answers to requests superseded by a newer one.
        this.requestId = 0;
        // Bootstrap ignores hide() while the opening animation runs.
        this.isOpening = false;
        this.hideWhenShown = false;
    }

    get modal() {
        return this.bootstrap.getOrCreateInstance(window.Modal, this.el);
    }

    onDocumentClick(ev) {
        const button = ev.target.closest(".o_aurora_quick_view_btn");
        if (!button || !document.body.contains(button)) {
            return;
        }
        ev.preventDefault();
        this.triggerEl = button;
        this.productTemplateId = parseInt(button.dataset.productTemplateId);
        this.bodyEl.innerHTML = this.loadingHtml;
        this.isOpening = true;
        this.hideWhenShown = false;
        this.modal.show(button);
        this.load();
    }

    async load(combination = []) {
        const requestId = ++this.requestId;
        let result;
        try {
            result = await this.waitFor(
                rpc("/aurora/quick_view", {
                    product_template_id: this.productTemplateId,
                    combination,
                })
            );
        } catch (error) {
            if (requestId === this.requestId) {
                showError(this.bodyEl, userErrorMessage(error));
            }
            return;
        }
        if (requestId !== this.requestId) {
            return;
        }
        replaceContent(this.services["public.interactions"], this.bodyEl, result.html);
        this.titleEl.textContent = result.name;
    }

    /** A variant was picked: render the dialog again for that combination. */
    onVariantChange(ev) {
        if (!ev.target.matches(".js_variant_change")) {
            return;
        }
        const productEl = this.bodyEl.querySelector(".js_product");
        const combination = [
            ...productEl.querySelectorAll(
                "input.js_variant_change:checked, select.js_variant_change"
            ),
        ].map((el) => parseInt(el.value));
        this.load(combination);
    }

    onBodyClick(ev) {
        const minus = ev.target.closest(".o_aurora_qty_minus");
        const plus = ev.target.closest(".o_aurora_qty_plus");
        if (!minus && !plus) {
            return;
        }
        const input = this.bodyEl.querySelector("input[name='add_qty']");
        const current = parseInt(input.value) || 1;
        input.value = Math.max(1, current + (plus ? 1 : -1));
    }

    onAddedToCart() {
        if (this.isOpening) {
            this.hideWhenShown = true;
        } else {
            this.modal.hide();
        }
    }

    onShown() {
        this.isOpening = false;
        if (this.hideWhenShown) {
            this.hideWhenShown = false;
            this.modal.hide();
        }
    }

    onHidden() {
        // Give the focus back to the button that opened the dialog.
        if (this.triggerEl && document.body.contains(this.triggerEl)) {
            this.triggerEl.focus();
        }
        this.services["public.interactions"].stopInteractions(this.bodyEl);
        this.bodyEl.innerHTML = this.loadingHtml;
        this.requestId++;
    }
}

registry.category("public.interactions").add("website_aurora20.quick_view", AuroraQuickView);
