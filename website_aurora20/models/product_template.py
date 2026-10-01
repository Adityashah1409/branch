from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    aurora_brand_id = fields.Many2one(
        comodel_name="aurora.product.brand",
        string="Brand",
        index="btree_not_null",
        ondelete="restrict",
    )
    # Stored copy of the brand name: the shop's fuzzy search only follows
    # x2many relations, so the name must live on the product itself.
    aurora_brand_name = fields.Char(
        related="aurora_brand_id.name", string="Brand Name", store=True, readonly=True,
    )

    # ------------------------------------------------------------------
    # Shop search: brand names are searchable, ``brand`` filters the shop
    # ------------------------------------------------------------------

    def _get_website_sale_search_fields(self, search_in_description=True):
        return super()._get_website_sale_search_fields(search_in_description) + [
            "aurora_brand_name"
        ]

    @api.model
    def _search_get_detail(self, website, order, options):
        detail = super()._search_get_detail(website, order, options)
        brand_id = options.get("aurora_brand_id")
        if brand_id:
            detail["base_domain"].append([("aurora_brand_id", "=", brand_id)])
        return detail

    # ------------------------------------------------------------------
    # B2B mode: never send prices to guests when they must be hidden
    # ------------------------------------------------------------------

    def _get_combination_info(self, combination=False, product_id=False, add_qty=1.0,
                              uom_id=False, only_template=False, pricelist=None,
                              fiscal_position=None):
        combination_info = super()._get_combination_info(
            combination=combination,
            product_id=product_id,
            add_qty=add_qty,
            uom_id=uom_id,
            only_template=only_template,
            pricelist=pricelist,
            fiscal_position=fiscal_position,
        )
        website = self.env.website
        if website and website.aurora_block_purchase():
            combination_info["prevent_sale"] = True
            if website.aurora_hide_prices():
                combination_info.update({
                    "hide_price": True,
                    "price": 0.0,
                    "list_price": 0.0,
                    "compare_list_price": 0.0,
                    "has_discounted_price": False,
                    "packaging_prices": {},
                })
                combination_info.pop("base_unit_price", None)
        return combination_info

    def _get_sales_prices(self, pricelist_sudo, fiscal_position_sudo, website):
        prices = super()._get_sales_prices(pricelist_sudo, fiscal_position_sudo, website)
        if website and website.aurora_hide_prices():
            return {template_id: {"price_reduce": 0.0} for template_id in prices}
        return prices

    def _website_show_quick_add(self, product=None):
        website = self.env.website
        if website and website.aurora_block_purchase():
            return False
        return super()._website_show_quick_add(product)
