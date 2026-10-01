from odoo import models
from odoo.modules import Manifest


class IrModuleModule(models.Model):
    _inherit = "ir.module.module"

    def _generate_primary_page_templates(self):
        """Generate the Aurora homepage designs.

        The standard implementation formats ``module.snippet`` keys with a list
        (``str.split``), which only works for snippets of the ``website``
        module. Aurora's designs also use their own blocks, so this module
        builds its page templates itself, the same way.
        """
        if self.name != "website_aurora20":
            return super()._generate_primary_page_templates()
        View = self.env["ir.ui.view"]
        templates = Manifest.for_addon(self.name)["new_page_templates"]
        values_by_key = {}
        for group, group_templates in templates.items():
            for template_name, snippet_keys in group_templates.items():
                key = f"{self.name}.new_page_template_sections_{group}_{template_name}"
                calls = []
                for snippet_key in snippet_keys:
                    module, snippet = (
                        snippet_key.split(".", 1) if "." in snippet_key else ("website", snippet_key)
                    )
                    calls.append(
                        f'<t t-snippet-call="{module}.new_page_template_{group}_{template_name}_{snippet}"/>'
                    )
                values_by_key[key] = {
                    "name": f"New page template: {template_name!r} in {group!r}",
                    "type": "qweb",
                    "key": key,
                    "arch": '<div id="wrap">\n    %s\n</div>' % "\n    ".join(calls),
                }
        existing = View.search([("mode", "=", "primary"), ("key", "in", list(values_by_key))])
        for view in existing:
            view.with_context(no_cow=True).write({"arch": values_by_key.pop(view.key)["arch"]})
        if values_by_key:
            self._create_model_data(View.create(list(values_by_key.values())))
        return None
