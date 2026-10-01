# Installation

## Requirements

* Odoo **20.0** (Community or Enterprise), Python 3.12, PostgreSQL 14+.
* Modules: `website_sale` (installed automatically as a dependency).

## Install

1. Put this repository on the Odoo addons path:
   `--addons-path=odoo/addons,/path/to/this/repo`
2. Update the apps list (Apps > Update Apps List, developer mode).
3. Install **Aurora Theme** (`theme_aurora20`). It installs
   **Aurora Storefront** (`website_aurora20`) with it.

From the command line:

```bash
./odoo-bin -d mydb --addons-path=odoo/addons,/path/to/repo -i theme_aurora20 --stop-after-init
```

## Apply the theme to a website

Website editor > **Theme** tab > **Switch theme** > *Aurora Theme*. On first
use the theme enables the *Aurora Classic* header, the *Aurora Store* footer and
the back-to-top button. Other websites of the same database keep their own
theme.

## Without the theme

Install only `website_aurora20` to get brands, quick view, cart drawer, B2B
mode, building blocks and homepage designs with any other theme.

## Uninstall

Switch the website to another theme first, then uninstall `theme_aurora20`.
Uninstalling `website_aurora20` deletes the brands and the brand of every
product.
