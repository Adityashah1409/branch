# Test plan

Automated: 40 tests (`website_aurora20/tests`, `theme_aurora20/tests`), run by
`tools/run_aurora_tests.sh` and CI.

| ID | Area | Scenario | Automated by |
| --- | --- | --- | --- |
| AT-01 | Install | Both modules install on a fresh Odoo 20 database | CI install step |
| AT-02 | Theme | Applying the theme enables the default header, footer and 3 assets | `test_theme_load_defaults` |
| AT-03 | Theme | Each of the 8 headers and 8 footers renders `/shop`; only one header active | `test_every_header_and_footer_renders` |
| AT-04 | Theme | Switching back to Odoo's header removes Aurora's | `test_switch_back_to_odoo_header` |
| AT-05 | Theme | Theme applies to one website only | `test_theme_isolated_per_website` |
| AT-06 | Theme | Frontend SCSS compiles with Aurora palette and styles | `test_frontend_assets_compile` |
| AT-07 | Brands | Guests can read published brands only | `test_public_brand_access_rules` |
| AT-08 | Brands | `/brands` lists published brands of the current website; search works | `test_brands_page_*` |
| AT-09 | Brands | Brand page shows published products; hidden or foreign brands give 404 | `test_brand_page*` |
| AT-10 | Brands | Disabled brand pages give 404; restricted eCommerce redirects to login | `test_brand_pages_*` |
| AT-11 | Shop | `/shop?brand=` filters; invalid values ignored; search finds brand names | `test_shop_brand_filter`, `test_product_search_finds_brand_name` |
| AT-12 | Search | Brands appear in website search only when enabled | `test_website_search_returns_brands` |
| AT-13 | Blocks | Brand logos endpoint caps the limit and filters featured | `test_brands_snippet` |
| AT-14 | Quick view | Renders published products; refuses unpublished and bad input | `test_quick_view*` |
| AT-15 | Quick view | Picked variant is shown; foreign values ignored | `test_quick_view_combination` |
| AT-16 | Cart drawer | Drawer content and quantity follow the cart | `test_cart_drawer` |
| AT-17 | Browser | Quick view > add 2 > drawer opens > +1 > remove | tour `website_aurora20_quick_view_drawer` |
| AT-18 | B2B | Guests get no prices in combination info or price batches | `test_guest_combination_info_hides_prices`, `test_guest_sales_prices_hidden` |
| AT-19 | B2B | Guests cannot add to cart, even by calling the route | `test_guest_cannot_add_to_cart_model`, `test_guest_add_to_cart_request_refused` |
| AT-20 | B2B | Signed-in customers buy normally; prices-only mode | `test_signed_in_customer_can_buy`, `test_prices_visible_when_only_cart_hidden` |
| AT-21 | B2B | Another website is unaffected | `test_b2b_off_on_other_website` |
| AT-22 | Settings | Settings are per website; reset restores defaults only | `test_settings_are_per_website`, `test_reset_settings` |
| AT-23 | Pages | 10 homepage designs are generated and render every block | `test_ten_designs_generated_and_render` |
| AT-24 | Layout | Containers and buttons follow the settings; announcement bar | `test_layout_renders_containers`, `test_announcement_bar` |

## Manual checks (done for this release, Chromium 1366px and 390px)

* All 8 headers and 8 footers visually, desktop and mobile header.
* Fashion and Marketplace homepage designs with live products.
* Recent searches suggestions, brand logos block, countdown block.
* No JavaScript errors on home, shop, product, brands pages.
