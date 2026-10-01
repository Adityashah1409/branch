from odoo import fields, models
from odoo.tools import is_html_empty

CARD_STYLES = [
    ("classic", "Classic"),
    ("elevated", "Elevated (actions on image)"),
    ("minimal", "Minimal"),
    ("compact", "Compact"),
]

# Default value of every storefront setting, used by the reset action.
AURORA_DEFAULTS = {
    "aurora_enable_quick_view": True,
    "aurora_enable_cart_drawer": True,
    "aurora_cart_drawer_auto_open": True,
    "aurora_enable_brand_pages": True,
    "aurora_enable_recent_searches": True,
    "aurora_product_card_style": "classic",
    "aurora_announcement_enabled": False,
    "aurora_announcement_url": False,
    "aurora_b2b_mode": False,
    "aurora_b2b_hide_prices": True,
    "aurora_b2b_hide_add_to_cart": True,
    "aurora_b2b_show_inquiry": True,
}


class Website(models.Model):
    _inherit = "website"

    # Storefront features (all per website)
    aurora_enable_quick_view = fields.Boolean(string="Quick View", default=True)
    aurora_enable_cart_drawer = fields.Boolean(
        string="Cart Drawer",
        default=True,
        help="Open a side drawer with the cart content instead of leaving the page "
             "when the cart icon is clicked.",
    )
    aurora_cart_drawer_auto_open = fields.Boolean(
        string="Open Drawer After Add To Cart", default=True
    )
    aurora_enable_brand_pages = fields.Boolean(string="Brand Pages", default=True)
    aurora_enable_recent_searches = fields.Boolean(
        string="Recent Searches",
        default=True,
        help="Remember the last searches of the visitor in their own browser.",
    )
    aurora_product_card_style = fields.Selection(
        selection=CARD_STYLES, string="Product Card Style", default="classic", required=True
    )

    # Announcement bar
    aurora_announcement_enabled = fields.Boolean(string="Announcement Bar")
    aurora_announcement_text = fields.Char(
        string="Announcement", translate=True, default="Free shipping on orders over 50"
    )
    aurora_announcement_url = fields.Char(string="Announcement Link")

    # B2B storefront
    aurora_b2b_mode = fields.Boolean(
        string="B2B Mode",
        help="Restrict prices and purchasing to signed-in customers. The restriction "
             "is enforced by the server, not only hidden in the page.",
    )
    aurora_b2b_hide_prices = fields.Boolean(string="Hide Prices From Guests", default=True)
    aurora_b2b_hide_add_to_cart = fields.Boolean(
        string="Hide Add To Cart From Guests", default=True
    )
    aurora_b2b_show_inquiry = fields.Boolean(string="Show Inquiry Button", default=True)
    aurora_b2b_message = fields.Char(
        string="Guest Message",
        translate=True,
        default="Sign in to your business account to see prices and order.",
    )
    aurora_b2b_wholesale_info = fields.Html(
        string="Wholesale Information",
        translate=True,
        sanitize=True,
        help="Shown on product pages to signed-in customers when B2B mode is on.",
    )

    # ------------------------------------------------------------------
    # B2B helpers (used by templates *and* by the server-side checks)
    # ------------------------------------------------------------------

    def _aurora_b2b_guest(self):
        """True when B2B mode applies to the current visitor (a guest)."""
        self.ensure_one()
        return bool(self.aurora_b2b_mode and self.env.user._is_public())

    def aurora_hide_prices(self):
        self.ensure_one()
        return self._aurora_b2b_guest() and self.aurora_b2b_hide_prices

    def aurora_block_purchase(self):
        """Guests may not buy: either explicitly, or because they can't see prices."""
        self.ensure_one()
        return self._aurora_b2b_guest() and (
            self.aurora_b2b_hide_add_to_cart or self.aurora_b2b_hide_prices
        )

    def aurora_show_wholesale_info(self):
        """Wholesale information is for signed-in customers of a B2B storefront."""
        self.ensure_one()
        return bool(
            self.aurora_b2b_mode
            and not self.env.user._is_public()
            and not is_html_empty(self.aurora_b2b_wholesale_info)
        )

    # ------------------------------------------------------------------
    # Website search
    # ------------------------------------------------------------------

    def _search_get_details(self, search_type, order, options):
        result = super()._search_get_details(search_type, order, options)
        if (
            self.aurora_enable_brand_pages
            and self.has_ecommerce_access()
            and search_type in ("products", "aurora_brand", "all")
        ):
            result.append(
                self.env["aurora.product.brand"]._search_get_detail(self, order, options)
            )
        return result

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_aurora_reset_settings(self):
        """Restore the default storefront settings of these websites.

        Only presentation settings are reset: products, brands, customers,
        orders and pages are never touched.
        """
        self.write(AURORA_DEFAULTS)
        for website in self:
            website.with_context(lang=website.default_lang_id.code or "en_US").write({
                "aurora_announcement_text": "Free shipping on orders over 50",
                "aurora_b2b_message": (
                    "Sign in to your business account to see prices and order."
                ),
            })
        return True
