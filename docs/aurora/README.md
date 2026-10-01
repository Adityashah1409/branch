# Aurora: eCommerce theme for Odoo 20

An original, premium-style website and eCommerce theme for **Odoo 20.0**,
split into two modules:

| Module | Kind | What it holds |
| --- | --- | --- |
| [`website_aurora20`](../../website_aurora20) | Functional add-on (any theme) | Brands, quick view, cart drawer, B2B mode, recent searches, announcement bar, building blocks, mega menus, 10 homepage designs, per-website storefront settings |
| [`theme_aurora20`](../../theme_aurora20) | Website theme | 8 headers, 8 footers, 4 color palettes, typography, shop/product/mega menu/mobile/RTL/accessibility styles |

The split follows how Odoo loads themes: a theme module's views are copied per
website and its Python models are global, so data models and features that must
survive a theme switch live in `website_aurora20`, and `theme_aurora20` only
holds presentation.

All code, styles, images and texts are original. Nothing is copied from any
commercial theme. License: LGPL-3.

## Quick start

```bash
./odoo-bin -d mydb --addons-path=odoo/addons,<this repo> -i theme_aurora20
```

Then, in the website editor: **Theme > Switch theme > Aurora Theme**, or keep
your current theme and install only `website_aurora20` to get the eCommerce
features.

## Documentation

* [Installation](installation.md)
* [Configuration](configuration.md)
* [Building blocks and homepage designs](snippets.md)
* [Developer guide](developer.md)
* [Test plan](test_plan.md)
* [Troubleshooting and FAQ](troubleshooting.md)
* [Upgrade notes](upgrade.md)

## Tests

```bash
tools/run_aurora_tests.sh /path/to/odoo
```

CI runs the same script on every push (`.github/workflows/aurora.yml`).
