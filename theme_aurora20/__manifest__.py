{
    "name": "Aurora Theme",
    "version": "20.0.1.0.0",
    "category": "Theme/eCommerce",
    "summary": "Premium eCommerce theme: 8 headers, 8 footers, mega menus, "
               "10 homepage designs, quick view, cart drawer, brands and B2B mode",
    "description": """
Aurora Theme
============

A modern storefront theme for Odoo 20 websites. It brings:

* eight headers (classic, centered, mega, minimal, split, B2B, modern, compact)
  and eight footers, all selectable in the website editor;
* four color palettes and a refined type scale;
* product card styles, sticky add-to-cart friendly product pages and polished
  shop pages, with right-to-left and keyboard support;
* all the storefront features of *Aurora Storefront* (``website_aurora20``):
  brands, quick view, cart drawer, B2B mode, building blocks, mega menus and
  ten homepage designs.
""",
    "author": "Aurora Theme Contributors",
    "website": "https://github.com/Adityashah1409/branch",
    "license": "LGPL-3",
    "depends": ["website_aurora20"],
    "data": [
        "data/generate_primary_template.xml",
        "data/ir_asset.xml",
        "views/headers.xml",
        "views/footers.xml",
    ],
    "images": [
        "static/description/aurora_cover.png",
        "static/description/aurora_screenshot.png",
    ],
    "configurator_snippets": {
        "homepage": [
            "s_carousel_intro", "s_key_benefits", "s_image_text",
            "s_masonry_block", "s_quotes_carousel", "s_cta_centered",
        ],
    },
    "configurator_snippets_addons": {
        "website_sale": {
            "homepage": [
                ("website_sale.s_dynamic_snippet_category_list", "after", "s_key_benefits"),
            ],
        },
    },
    "assets": {
        "website.website_builder_assets": [
            "theme_aurora20/static/src/builder/**/*",
        ],
    },
    "installable": True,
    "application": False,
}
