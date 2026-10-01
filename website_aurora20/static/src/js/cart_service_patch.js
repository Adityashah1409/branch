import { patch } from "@web/core/utils/patch";
import { CartService } from "@website_sale/js/cart_service";
import { getStorefrontConfig } from "@website_aurora20/js/storefront_utils";

/**
 * When the cart drawer opens by itself after "Add to cart", it already shows
 * what was added: skip eCommerce's own "added to cart" popup so the two don't
 * overlap. Warnings (stock, errors) are always shown.
 */
patch(CartService.prototype, {
    _showCartNotification(notification) {
        if (notification?.type !== "warning" && getStorefrontConfig().drawerAutoOpen) {
            return;
        }
        return super._showCartNotification(...arguments);
    },
});
