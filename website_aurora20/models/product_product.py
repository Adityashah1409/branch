from odoo import models


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _is_add_to_cart_allowed(self) -> bool:
        """B2B mode: guests can't buy, whatever the page shows.

        This is the check used by ``/shop/cart/add`` and by the cart lines, so a
        hand-crafted request can't bypass a hidden button.
        """
        website = self.env.website
        if website and website.aurora_block_purchase() and not self._is_donation():
            return False
        return super()._is_add_to_cart_allowed()
