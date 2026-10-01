from odoo import models

AURORA_HEADERS = [
    "theme_aurora20.template_header_classic",
    "theme_aurora20.template_header_centered",
    "theme_aurora20.template_header_mega",
    "theme_aurora20.template_header_minimal",
    "theme_aurora20.template_header_split",
    "theme_aurora20.template_header_b2b",
    "theme_aurora20.template_header_modern",
    "theme_aurora20.template_header_compact",
]

AURORA_FOOTERS = [
    "theme_aurora20.template_footer_store",
    "theme_aurora20.template_footer_centered_brand",
    "theme_aurora20.template_footer_mega_dark",
    "theme_aurora20.template_footer_minimal_line",
    "theme_aurora20.template_footer_cta",
    "theme_aurora20.template_footer_b2b",
    "theme_aurora20.template_footer_split",
    "theme_aurora20.template_footer_service",
]


class ThemeUtils(models.AbstractModel):
    _inherit = "theme.utils"

    # Registering the templates makes them mutually exclusive with Odoo's own
    # headers and footers: enabling one disables the others (see enable_view).
    @property
    def _header_templates(self):
        return AURORA_HEADERS + super()._header_templates

    @property
    def _footer_templates(self):
        return AURORA_FOOTERS + super()._footer_templates

    def _theme_aurora20_post_copy(self, mod):
        """Default look of a website when the Aurora theme is applied."""
        self.enable_view("theme_aurora20.template_header_classic")
        self.enable_view("theme_aurora20.template_footer_store")
        self.enable_view("website.option_footer_scrolltop")
