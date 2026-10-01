import logging

from werkzeug.exceptions import NotFound

from odoo.fields import Domain
from odoo.http import Controller, request, route
from odoo.tools import is_html_empty

_logger = logging.getLogger(__name__)

# Upper bound of records a visitor can ask for in one request.
MAX_SNIPPET_BRANDS = 24
BRAND_PAGE_PRODUCTS = 24


class AuroraStorefront(Controller):

    # ------------------------------------------------------------------
    # Brands
    # ------------------------------------------------------------------

    def _check_brand_pages(self):
        website = request.env.website
        if not website.aurora_enable_brand_pages:
            raise NotFound()
        if not website.has_ecommerce_access():
            return request.redirect("/web/login?redirect=%s" % request.httprequest.path)
        return None

    def _published_brands_domain(self, website, search=None):
        domain = Domain.AND([
            website.website_domain(),
            Domain("website_published", "=", True),
        ])
        if search:
            domain &= Domain("name", "ilike", search)
        return domain

    @route("/brands", type="http", auth="public", website=True, sitemap=True)
    def brands(self, search="", **kwargs):
        redirect = self._check_brand_pages()
        if redirect:
            return redirect
        website = request.env.website
        search = (search or "").strip()[:100]
        brands = request.env["aurora.product.brand"].search(
            self._published_brands_domain(website, search),
            order="is_featured desc, sequence, name",
        )
        return request.render("website_aurora20.brands_page", {
            "brands": brands,
            "search": search,
        })

    @route(
        "/brand/<model('aurora.product.brand'):brand>",
        type="http", auth="public", website=True, sitemap=True,
    )
    def brand(self, brand, **kwargs):
        redirect = self._check_brand_pages()
        if redirect:
            return redirect
        website = request.env.website
        # The URL converter browses the record: make sure the visitor may see it.
        if not brand.exists() or not brand.website_published or (
            brand.website_id and brand.website_id != website
        ):
            raise NotFound()
        products = request.env["product.template"].search(
            Domain.AND([
                website.sale_product_domain(),
                Domain("aurora_brand_id", "=", brand.id),
            ]),
            order="website_sequence, id",
            limit=BRAND_PAGE_PRODUCTS,
        )
        product_count = request.env["product.template"].search_count(
            Domain.AND([
                website.sale_product_domain(),
                Domain("aurora_brand_id", "=", brand.id),
            ])
        )
        return request.render("website_aurora20.brand_page", {
            "brand": brand,
            "products": products,
            "product_count": product_count,
            "prices": self._get_card_prices(products),
            "main_object": brand,
            "is_html_empty": is_html_empty,
        })

    def _get_card_prices(self, products):
        """Prices of the product cards, computed in one batch (pricelist, taxes)."""
        if not products:
            return {}
        website = request.env.website
        return products._get_sales_prices(
            website.pricelist_id.sudo(), request.fiscal_position.sudo(), website
        )

    @route("/aurora/brands/snippet", type="jsonrpc", auth="public", website=True, readonly=True)
    def brands_snippet(self, limit=12, featured_only=False, **kwargs):
        """HTML of the brand logos building block (rendered on page load)."""
        website = request.env.website
        if not website.aurora_enable_brand_pages or not website.has_ecommerce_access():
            return {"html": ""}
        try:
            limit = max(1, min(int(limit), MAX_SNIPPET_BRANDS))
        except (TypeError, ValueError):
            limit = 12
        domain = self._published_brands_domain(website)
        if featured_only:
            domain &= Domain("is_featured", "=", True)
        brands = request.env["aurora.product.brand"].search(
            domain, order="is_featured desc, sequence, name", limit=limit
        )
        html = request.env["ir.ui.view"]._render_template(
            "website_aurora20.brand_logos", {"brands": brands}
        )
        return {"html": html}

    # ------------------------------------------------------------------
    # Quick view
    # ------------------------------------------------------------------

    @route("/aurora/quick_view", type="jsonrpc", auth="public", website=True, readonly=True)
    def quick_view(self, product_template_id, combination=None, **kwargs):
        """Render the quick view of a product.

        :param int product_template_id: the product to show.
        :param list[int] combination: selected ``product.template.attribute.value``
            ids, sent again each time the visitor picks another variant.
        """
        website = request.env.website
        if not website.aurora_enable_quick_view or not website.has_ecommerce_access():
            raise NotFound()
        try:
            product_template_id = int(product_template_id)
            ptav_ids = [int(ptav_id) for ptav_id in combination or []]
        except (TypeError, ValueError):
            raise NotFound() from None
        # Searching with the shop domain applies the publication, website and
        # access rules: an unpublished product can't be previewed this way.
        product = request.env["product.template"].search(
            Domain.AND([website.sale_product_domain(), Domain("id", "=", product_template_id)]),
            limit=1,
        )
        if not product:
            raise NotFound()
        # Only keep values that belong to this product.
        selected = product.valid_product_template_attribute_line_ids.product_template_value_ids
        selected = selected.filtered(lambda ptav: ptav.id in ptav_ids)
        combination = product._get_first_available_combination(necessary_values=selected or None)
        if selected:
            # Keep exactly what the visitor picked, completed for the other attributes.
            picked_attributes = selected.attribute_id
            combination = selected | combination.filtered(
                lambda ptav: ptav.attribute_id not in picked_attributes
            )
        combination_info = product._get_combination_info(combination=combination)
        html = request.env["ir.ui.view"]._render_template(
            "website_aurora20.quick_view_content",
            {
                "product": product,
                "product_variant": request.env["product.product"].browse(
                    combination_info["product_id"]
                ),
                "combination": combination,
                "combination_info": combination_info,
                "website": website,
            },
        )
        return {"html": html, "name": product.display_name}

    # ------------------------------------------------------------------
    # Cart drawer
    # ------------------------------------------------------------------

    @route("/aurora/cart/drawer", type="jsonrpc", auth="public", website=True, readonly=True)
    def cart_drawer(self, **kwargs):
        order = request.cart
        html = request.env["ir.ui.view"]._render_template(
            "website_aurora20.cart_drawer_content",
            {"website_sale_order": order, "website": request.env.website},
        )
        return {
            "html": html,
            "cart_quantity": order.cart_quantity if order else 0,
        }
