{
    "name": "Aurora Storefront (eCommerce features)",
    "version": "20.0.1.0.0",
    "category": "Website/Website",
    "summary": "Brands, quick view, cart drawer, B2B mode, storefront building "
               "blocks and per-website storefront settings",
    "description": """
Aurora Storefront
=================

Theme-independent eCommerce features used by the *Aurora* theme
(``theme_aurora20``). They work with any website theme:

* product brands with ``/brands`` and ``/brand/<brand>`` pages, a brand filter
  on ``/shop`` and brand results in the website search;
* product quick view (variants, quantity, add to cart, wishlist, compare);
* a right-side cart drawer (mini cart) with quantity controls;
* B2B storefront mode: hide prices and purchasing from guests, enforced on the
  server, with a login message and an inquiry button;
* announcement bar and product card styles;
* original building blocks (hero, promo banners, services, testimonials,
  newsletter strip, brand logos, mega menus);
* every setting is stored per website.
""",
    "author": "Aurora Theme Contributors",
    "website": "https://github.com/Adityashah1409/branch",
    "license": "LGPL-3",
    "depends": ["website_sale"],
    "data": [
        "security/ir.access.csv",
        "data/website_snippet_filter_data.xml",
        "views/website_views.xml",
        "views/product_brand_views.xml",
        "views/product_template_views.xml",
        "views/menus.xml",
        "views/layout_templates.xml",
        "views/brand_templates.xml",
        "views/shop_templates.xml",
        "views/product_templates.xml",
        "views/quick_view_templates.xml",
        "views/cart_drawer_templates.xml",
        "views/snippets/s_aurora_hero.xml",
        "views/snippets/s_aurora_promo_duo.xml",
        "views/snippets/s_aurora_services.xml",
        "views/snippets/s_aurora_testimonials.xml",
        "views/snippets/s_aurora_newsletter.xml",
        "views/snippets/s_aurora_category_tiles.xml",
        "views/snippets/s_aurora_countdown_banner.xml",
        "views/snippets/s_aurora_gallery.xml",
        "views/snippets/s_aurora_brands.xml",
        "views/snippets/s_aurora_mega_menus.xml",
        "views/snippets/s_aurora_products.xml",
        "views/snippets/snippets.xml",
        "views/new_page_templates.xml",
    ],
    "demo": [
        "data/demo.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "website_aurora20/static/src/scss/storefront.scss",
            "website_aurora20/static/src/scss/snippets.scss",
            "website_aurora20/static/src/js/storefront_utils.js",
            "website_aurora20/static/src/js/cart_service_patch.js",
            "website_aurora20/static/src/interactions/*.js",
        ],
        "website.website_builder_assets": [
            "website_aurora20/static/src/website_builder/**/*",
        ],
        "web.assets_tests": [
            "website_aurora20/static/tests/tours/*.js",
        ],
    },
    # Ten homepage designs, offered in the editor under + New > Page.
    "new_page_templates": {
        "aurora_home": {
            # Fashion and lifestyle
            "fashion": ["website_aurora20.s_aurora_hero", "website_aurora20.s_aurora_services", "website_aurora20.s_aurora_category_tiles",
                        "website_aurora20.s_aurora_products_newest", "website_aurora20.s_aurora_promo_duo",
                        "website_aurora20.s_aurora_testimonials", "website_aurora20.s_aurora_gallery", "website_aurora20.s_aurora_newsletter"],
            # Electronics and gadgets
            "electronics": ["s_carousel_intro", "website_aurora20.s_aurora_services", "website_aurora20.s_aurora_products_featured",
                            "website_aurora20.s_aurora_countdown_banner", "website_aurora20.s_aurora_products_on_sale",
                            "website_aurora20.s_aurora_brands", "s_faq_collapse"],
            # Furniture and home decor
            "furniture": ["s_cover", "website_aurora20.s_aurora_category_tiles", "s_image_text",
                          "website_aurora20.s_aurora_products_newest", "s_masonry_block", "website_aurora20.s_aurora_testimonials",
                          "website_aurora20.s_aurora_newsletter"],
            # Beauty and cosmetics
            "beauty": ["s_splash_intro", "website_aurora20.s_aurora_products_best_sellers", "s_text_image",
                       "website_aurora20.s_aurora_promo_duo", "website_aurora20.s_aurora_testimonials", "website_aurora20.s_aurora_gallery"],
            # Grocery and daily essentials
            "grocery": ["s_banner_categories", "website_aurora20.s_aurora_services", "website_aurora20.s_aurora_products_on_sale",
                        "website_aurora20.s_aurora_category_tiles", "website_aurora20.s_aurora_products_best_sellers",
                        "website_aurora20.s_aurora_newsletter"],
            # Jewelry and luxury
            "jewelry": ["s_parallax", "website_aurora20.s_aurora_products_featured", "s_image_text",
                        "website_aurora20.s_aurora_gallery", "s_quotes_carousel", "s_cta_centered"],
            # Sports and outdoor
            "sports": ["website_aurora20.s_aurora_hero", "website_aurora20.s_aurora_countdown_banner", "website_aurora20.s_aurora_category_tiles",
                       "website_aurora20.s_aurora_products_best_sellers", "s_key_benefits", "website_aurora20.s_aurora_brands"],
            # B2B and wholesale
            "b2b": ["s_banner", "s_key_benefits", "website_aurora20.s_aurora_category_tiles",
                    "website_aurora20.s_aurora_products_featured", "s_numbers_lite", "s_references",
                    "s_call_to_action"],
            # Single brand / minimal
            "minimal": ["s_title", "website_aurora20.s_aurora_products_newest", "s_text_block",
                        "website_aurora20.s_aurora_newsletter"],
            # Marketplace / multi-brand
            "marketplace": ["website_aurora20.s_aurora_hero", "website_aurora20.s_aurora_brands", "website_aurora20.s_aurora_promo_duo",
                            "website_aurora20.s_aurora_products_on_sale", "website_aurora20.s_aurora_category_tiles",
                            "website_aurora20.s_aurora_products_newest", "website_aurora20.s_aurora_services"],
        },
    },
    "images": ["static/description/icon.png"],
    "installable": True,
    "application": False,
}
