import { _t } from "@web/core/l10n/translation";
import { RPCError } from "@web/core/network/rpc";

/**
 * Shared helpers of the Aurora storefront interactions.
 */

/** Storefront settings rendered by the server on #wrapwrap (see layout_templates.xml). */
export function getStorefrontConfig() {
    const wrapwrap = document.getElementById("wrapwrap");
    const data = wrapwrap ? wrapwrap.dataset : {};
    return {
        quickView: data.auroraQuickView === "1",
        cartDrawer: data.auroraCartDrawer === "1",
        drawerAutoOpen: data.auroraDrawerAutoOpen === "1",
        recentSearches: data.auroraRecentSearches === "1",
    };
}

/**
 * Turn an RPC failure into a message that can be shown to a visitor.
 * Server tracebacks are never displayed.
 *
 * @param {Error} error
 * @returns {string}
 */
export function userErrorMessage(error) {
    if (error instanceof RPCError) {
        const name = error.data?.name || "";
        if (name.includes("SessionExpiredException")) {
            return _t("Your session has expired. Please reload the page.");
        }
        if (name.includes("AccessError") || name.includes("Forbidden")) {
            return _t("You are not allowed to do this.");
        }
        if (name.includes("NotFound")) {
            return _t("This product is not available anymore.");
        }
        if (name.includes("UserError") || name.includes("ValidationError")) {
            return error.data.message;
        }
        return _t("Something went wrong. Please try again.");
    }
    return _t("We could not reach the server. Check your connection and try again.");
}

/**
 * Update the cart quantity badges of the header (desktop and mobile).
 *
 * @param {number} cartQuantity
 */
export function updateCartBadges(cartQuantity) {
    try {
        sessionStorage.setItem("website_sale_cart_quantity", cartQuantity);
    } catch {
        // Storage may be disabled (private browsing): the badge still updates.
    }
    for (const badge of document.querySelectorAll(".my_cart_quantity")) {
        badge.textContent = cartQuantity;
        badge.classList.toggle("d-none", !cartQuantity);
    }
}

/**
 * Replace the content of a container and (re)start the interactions inside it.
 *
 * @param {Object} interactionsService the "public.interactions" service
 * @param {HTMLElement} containerEl
 * @param {string} html markup rendered by the server (QWeb, escaped)
 */
export function replaceContent(interactionsService, containerEl, html) {
    interactionsService.stopInteractions(containerEl);
    containerEl.innerHTML = html;
    interactionsService.startInteractions(containerEl);
}

/** Show an error message in a container (text only, never HTML). */
export function showError(containerEl, message) {
    const alertEl = document.createElement("p");
    alertEl.className = "alert alert-warning m-3";
    alertEl.setAttribute("role", "alert");
    alertEl.textContent = message;
    containerEl.replaceChildren(alertEl);
}
