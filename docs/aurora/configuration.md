# Configuration

## Storefront settings (per website)

**Website > Configuration > Storefront Settings**, then open a website.
Every value is stored on the website, so two websites of the same database can
be configured differently.

| Setting | Default | Effect |
| --- | --- | --- |
| Quick View | on | "Quick view" button on product cards; dialog with variants, quantity, add to cart, wishlist and compare |
| Cart Drawer | on | The header cart icon opens a side drawer (quantities, remove, subtotal, checkout) |
| Open Drawer After Add To Cart | on | The drawer opens by itself after a product is added; eCommerce's own "added" popup is then skipped |
| Brand Pages | on | `/brands`, `/brand/<brand>`, brand filter on `/shop`, brands in the website search |
| Recent Searches | on | Last 6 searches of the visitor, stored in their own browser only, offered as suggestions |
| Product Card Style | Classic | Classic, Elevated, Minimal or Compact cards on the shop |
| Announcement Bar | off | A line of text (and optional link) above the header |
| B2B Mode | off | See below |

**Reset to defaults** restores these settings only. Products, brands,
customers, orders and pages are never touched.

## B2B mode

When **B2B Mode** is on, a visitor who is not signed in:

* sees no price when *Hide Prices From Guests* is set (shop, product page,
  quick view, brand pages, product blocks);
* cannot add to cart when *Hide Add To Cart From Guests* is set, or when prices
  are hidden;
* sees the *Guest Message* with a **Sign in** button, and an **Inquire** link
  when *Show Inquiry Button* is set.

This is enforced by the server: prices are removed from the data sent to the
browser, and `/shop/cart/add` refuses the product. Signed-in customers buy
normally and see the *Wholesale Information* on product pages.

## Brands

**Website > eCommerce > Products > Brands**. A brand has a logo, a banner, a
description, an external website and SEO fields. A brand linked to a website is
only shown there; a brand without website is shared. Unpublished brands are
never shown. Set the brand of a product in its *Sales* tab (eCommerce section).

## Headers and footers

Website editor > click the header (or footer) > **Template**. The eight Aurora
headers and footers are listed with Odoo's own. Every header contains the
search, cart, wishlist, account and language/pricelist selectors, and uses
Odoo's mobile header on small screens.

| Header | Layout |
| --- | --- |
| Classic | logo, centered menu, icons |
| Centered | search, centered logo, icons; menu below |
| Mega | contact bar; logo, large search, cart; menu bar for mega menus |
| Minimal | logo and icons; menu in a side panel |
| Split | menu, centered logo, icons (try "Header over the content") |
| B2B | phone/e-mail bar with "Request a quote"; prominent sign in |
| Modern | floating rounded bar with a cart button |
| Compact | menu button, logo, icons on every screen |

Footers: Store, Centered, Mega Dark, Minimal, Call to Action, Business, Split,
Services.

## Colors and fonts

Theme tab > Colors: four Aurora palettes (Indigo, Emerald, Rose, Midnight).
Fonts default to Inter (text) and Manrope (headings) and can be changed there.
