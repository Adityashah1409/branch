from odoo.http import request, route

from odoo.addons.website_sale.controllers.main import WebsiteSale


def _parse_brand(value):
    """``brand`` query parameter -> brand id, or None if missing/invalid."""
    if not value:
        return None
    try:
        brand_id = int(value)
    except (TypeError, ValueError):
        return None
    return brand_id if brand_id > 0 else None


class AuroraWebsiteSale(WebsiteSale):
    """Brand filter on the shop (``/shop?brand=<id>``)."""

    def _get_search_options(self, category=None, attribute_value_dict=None, tags=None,
                            min_price=0.0, max_price=0.0, conversion_rate=1, **post):
        options = super()._get_search_options(
            category=category,
            attribute_value_dict=attribute_value_dict,
            tags=tags,
            min_price=min_price,
            max_price=max_price,
            conversion_rate=conversion_rate,
            **post,
        )
        brand_id = _parse_brand(post.get("brand"))
        if brand_id and request.env.website.aurora_enable_brand_pages:
            options["aurora_brand_id"] = brand_id
        return options

    def _shop_get_query_url_kwargs(self, search, min_price, max_price, order=None, tags=None,
                                   on_sale=None, in_stock=None, **kwargs):
        values = super()._shop_get_query_url_kwargs(
            search, min_price, max_price,
            order=order, tags=tags, on_sale=on_sale, in_stock=in_stock, **kwargs,
        )
        brand_id = _parse_brand(kwargs.get("brand"))
        if brand_id:
            values["brand"] = brand_id
        return values

    @route()
    def shop(self, page=0, category=None, search="", min_price=0.0, max_price=0.0, tags="",
             on_sale=None, in_stock=None, **post):
        response = super().shop(
            page=page, category=category, search=search, min_price=min_price,
            max_price=max_price, tags=tags, on_sale=on_sale, in_stock=in_stock, **post,
        )
        qcontext = getattr(response, "qcontext", None)
        website = request.env.website
        if qcontext is None or not website.aurora_enable_brand_pages:
            return response
        Brand = request.env["aurora.product.brand"]
        brands = Brand.search(
            website.website_domain() + [("website_published", "=", True)],
            order="is_featured desc, sequence, name",
        )
        brand_id = _parse_brand(post.get("brand"))
        qcontext.update({
            "aurora_brands": brands,
            "aurora_brand": brands.filtered(lambda b: b.id == brand_id)[:1] if brand_id else Brand,
        })
        return response
