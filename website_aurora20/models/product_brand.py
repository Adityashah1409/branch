from odoo import api, fields, models
from odoo.tools.translate import html_translate


class AuroraProductBrand(models.Model):
    """A product brand (manufacturer / label) shown on the storefront.

    Brands are optional: products without a brand behave exactly as in standard
    Odoo. A brand restricted to one website (``website_id``) is only listed on
    that website; a brand without website is shared by all websites.
    """

    _name = "aurora.product.brand"
    _description = "Product Brand"
    _inherit = [
        "image.mixin",
        "website.published.multi.mixin",
        "website.searchable.mixin",
        "website.seo.metadata",
    ]
    _order = "sequence, name, id"

    # Brand names are proper nouns: the same in every language.
    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    description = fields.Html(translate=html_translate, sanitize_overridable=True)
    brand_website = fields.Char(
        string="Brand Website",
        help="External URL of the brand, displayed on the brand page.",
    )
    banner = fields.Image(
        max_width=1920,
        max_height=1080,
        help="Wide image displayed at the top of the brand page.",
    )
    is_featured = fields.Boolean(
        string="Featured",
        help="Featured brands come first in the brand building blocks and on /brands.",
    )
    product_tmpl_ids = fields.One2many(
        comodel_name="product.template",
        inverse_name="aurora_brand_id",
        string="Products",
    )
    product_count = fields.Integer(compute="_compute_product_count")

    _name_website_unique = models.Constraint(
        "UNIQUE(name, website_id)",
        "A brand with this name already exists on this website.",
    )

    @api.depends("product_tmpl_ids")
    def _compute_product_count(self):
        counts = dict(
            self.env["product.template"]._read_group(
                [("aurora_brand_id", "in", self.ids)],
                groupby=["aurora_brand_id"],
                aggregates=["__count"],
            )
        )
        for brand in self:
            brand.product_count = counts.get(brand, 0)

    def _compute_website_url(self):
        super()._compute_website_url()
        for brand in self:
            if brand.id:
                brand.website_url = "/brand/%s" % self.env["ir.http"]._slug(brand)

    def _get_published_product_count(self, website):
        """Number of products of the brand that the current visitor can see on ``website``."""
        self.ensure_one()
        return self.env["product.template"].search_count(
            website.sale_product_domain()
            + [("aurora_brand_id", "=", self.id), ("is_published", "=", True)]
        )

    def action_view_products(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "website_sale.product_template_action_website"
        )
        action["domain"] = [("aurora_brand_id", "=", self.id)]
        action["context"] = {"default_aurora_brand_id": self.id}
        return action

    # ------------------------------------------------------------------
    # Website search (``/website/search`` and the search box suggestions)
    # ------------------------------------------------------------------

    @api.model
    def _search_get_detail(self, website, order, options):
        return {
            "model": "aurora.product.brand",
            "base_domain": [
                website.website_domain(),
                [("website_published", "=", True)],
            ],
            "search_fields": ["name"],
            "fetch_fields": ["id", "name", "website_url"],
            "mapping": {
                "name": {"name": "name", "type": "text", "match": True},
                "website_url": {"name": "website_url", "type": "text", "truncate": False},
                "image_url": {"name": "image_url", "type": "html"},
            },
            "icon": "sell",
            "order": "name desc, id desc" if "name desc" in order else "name asc, id desc",
            "group_name": self.env._("Brands"),
            "sequence": 35,
        }

    def _search_render_results(self, fetch_fields, mapping, icon, limit):
        results_data = super()._search_render_results(fetch_fields, mapping, icon, limit)
        for data in results_data:
            data["image_url"] = "/web/image/aurora.product.brand/%s/image_128" % data["id"]
        return results_data
