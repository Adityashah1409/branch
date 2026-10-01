# Troubleshooting and FAQ

**The Aurora headers are not in the Template list.**
The website must use the Aurora theme: the editor options of a theme are only
loaded on websites that use it.

**The quick view or cart drawer does nothing.**
Check *Storefront Settings* on that website. With a custom layout, make sure
the page has a `#wrapwrap` element: frontend interactions only start inside it.

**Prices still show for guests in B2B mode.**
Check that the visitor is really signed out and that the setting is on the
website they browse. Cached pages (CDN) may need purging after switching B2B
mode on.

**A product block shows nothing.**
Odoo hides product blocks without products: publish products, or pick another
data source in the block options (*Newest*, *Featured*, *On Sale*...).

**Fonts look different offline.**
Fonts come from Google Fonts. Pick a system font in Theme > Fonts for
intranets without internet access.

**Can I use only the eCommerce features?**
Yes, install `website_aurora20` alone.

**Is this a copy of another theme?**
No. Everything was written for this project; nothing comes from any commercial
theme.
