import { Plugin } from "@html_editor/plugin";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { HeaderTemplateChoice } from "@website/builder/plugins/options/header/header_template_option";
import { FooterTemplateChoice } from "@website/builder/plugins/options/footer_template_option";

const IMG = "/theme_aurora20/static/src/img";

// Headers with their menu in an offcanvas never auto-hide menu entries.
// key, views and varName must match views/headers.xml and the
// 'header-template' value in primary_variables.scss.
const HEADERS = [
    ["classic", _t("Aurora Classic")],
    ["centered", _t("Aurora Centered")],
    ["mega", _t("Aurora Mega")],
    ["minimal", _t("Aurora Minimal"), ["website.no_autohide_menu"]],
    ["split", _t("Aurora Split")],
    ["b2b", _t("Aurora B2B")],
    ["modern", _t("Aurora Modern")],
    ["compact", _t("Aurora Compact"), ["website.no_autohide_menu"]],
];

const FOOTERS = [
    ["store", _t("Aurora Store")],
    ["centered_brand", _t("Aurora Centered")],
    ["mega_dark", _t("Aurora Mega Dark")],
    ["minimal_line", _t("Aurora Minimal")],
    ["cta", _t("Aurora Call to Action")],
    ["b2b", _t("Aurora Business")],
    ["split", _t("Aurora Split")],
    ["service", _t("Aurora Services")],
];

const dashed = (name) => name.replaceAll("_", "-");

class AuroraHeaderFooterOptionPlugin extends Plugin {
    static id = "auroraHeaderFooterOption";
    resources = {
        header_templates_providers: [
            () =>
                HEADERS.map(([name, title, extraViews = []]) => ({
                    key: `aurora_${name}`,
                    Component: HeaderTemplateChoice,
                    props: {
                        id: `header_aurora_${name}_opt`,
                        imgSrc: `${IMG}/header/${name}.svg`,
                        menuShadowClass: "shadow-sm",
                        title,
                        varName: `aurora-${dashed(name)}`,
                        views: [`theme_aurora20.template_header_${name}`, ...extraViews],
                    },
                })),
        ],
        footer_templates_providers: [
            () =>
                FOOTERS.map(([name, title]) => ({
                    key: `aurora_${name}`,
                    Component: FooterTemplateChoice,
                    props: {
                        imgSrc: `${IMG}/footer/${name}.svg`,
                        title,
                        varName: `aurora-${dashed(name)}`,
                        view: `theme_aurora20.template_footer_${name}`,
                    },
                })),
        ],
    };
}

registry
    .category("website-plugins")
    .add(AuroraHeaderFooterOptionPlugin.id, AuroraHeaderFooterOptionPlugin);
