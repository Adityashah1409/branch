import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { BootstrapInstance } from "@web/core/utils/bootstrap_plugin";
import { usePlugin } from "@odoo/owl";
import {
    getStorefrontConfig,
    replaceContent,
    showError,
    updateCartBadges,
    userErrorMessage,
} from "@website_aurora20/js/storefront_utils";

// Pages where the cart icon must keep its normal behaviour.
const CART_PAGES = ["/shop/cart", "/shop/checkout", "/shop/payment", "/shop/confirmation"];

/**
 * Right-side cart drawer (mini cart).
 *
 * The header cart icon opens the drawer instead of leaving the page, and the
 * drawer opens by itself after a product is added (when configured).
 * Quantities are changed with Odoo's own cart route, so every cart rule
 * (stock, prices, promotions) still applies.
 */
export class AuroraCartDrawer extends Interaction {
    static selector = "#o_aurora_cart_drawer";
    dynamicContent = {
        _document: {
            "t-on-click": this.onDocumentClick,
            "t-on-product_added_to_cart": this.onProductAdded,
        },
        ".o_aurora_cart_drawer_body": {
            "t-on-click": this.locked(this.onBodyClick),
            "t-on-change": this.locked(this.onQuantityInput),
        },
    };

    setup() {
        this.bootstrap = usePlugin(BootstrapInstance);
        this.bodyEl = this.el.querySelector(".o_aurora_cart_drawer_body");
        this.config = getStorefrontConfig();
    }

    get offcanvas() {
        return this.bootstrap.getOrCreateInstance(window.Offcanvas, this.el);
    }

    onDocumentClick(ev) {
        const link = ev.target.closest(".o_wsale_my_cart a[href='/shop/cart']");
        if (!link || CART_PAGES.some((path) => window.location.pathname.startsWith(path))) {
            return;
        }
        ev.preventDefault();
        this.open(link);
    }

    onProductAdded(ev) {
        // The quick view dialog closes itself; let it finish before opening.
        if (this.config.drawerAutoOpen) {
            this.waitForTimeout(() => this.open(ev.target), 150);
        }
    }

    open(triggerEl) {
        this.offcanvas.show(triggerEl);
        return this.refresh();
    }

    async refresh() {
        let result;
        try {
            result = await this.waitFor(rpc("/aurora/cart/drawer"));
        } catch (error) {
            showError(this.bodyEl, userErrorMessage(error));
            return;
        }
        replaceContent(this.services["public.interactions"], this.bodyEl, result.html);
        updateCartBadges(result.cart_quantity);
    }

    async setQuantity(lineEl, quantity) {
        try {
            await this.waitFor(
                rpc("/shop/cart/update", {
                    line_id: parseInt(lineEl.dataset.lineId),
                    product_id: parseInt(lineEl.dataset.productId),
                    quantity: Math.max(0, quantity),
                })
            );
        } catch (error) {
            showError(this.bodyEl, userErrorMessage(error));
            return;
        }
        await this.refresh();
    }

    async onBodyClick(ev) {
        const lineEl = ev.target.closest(".o_aurora_cart_line");
        if (!lineEl) {
            return;
        }
        if (ev.target.closest(".o_aurora_cart_remove")) {
            await this.setQuantity(lineEl, 0);
            return;
        }
        const qtyButton = ev.target.closest(".o_aurora_cart_qty");
        if (qtyButton) {
            const input = lineEl.querySelector(".o_aurora_cart_qty_input");
            const current = parseInt(input.value) || 0;
            await this.setQuantity(lineEl, current + parseInt(qtyButton.dataset.delta));
        }
    }

    async onQuantityInput(ev) {
        if (!ev.target.matches(".o_aurora_cart_qty_input")) {
            return;
        }
        const lineEl = ev.target.closest(".o_aurora_cart_line");
        const quantity = parseInt(ev.target.value);
        if (Number.isNaN(quantity)) {
            return;
        }
        await this.setQuantity(lineEl, quantity);
    }
}

registry.category("public.interactions").add("website_aurora20.cart_drawer", AuroraCartDrawer);
