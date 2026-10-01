import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

/** Fills the "Brand Logos" building block with the published brands. */
export class AuroraBrandLogos extends Interaction {
    static selector = ".s_aurora_brands";

    async willStart() {
        const { limit, featuredOnly } = this.el.dataset;
        try {
            const result = await this.waitFor(
                rpc("/aurora/brands/snippet", {
                    limit: parseInt(limit) || 12,
                    featured_only: featuredOnly === "1",
                })
            );
            this.html = result.html;
        } catch {
            // A missing brand strip must not break the page: keep it empty.
            this.html = "";
        }
    }

    start() {
        const contentEl = this.el.querySelector(".s_aurora_brands_content");
        if (!contentEl) {
            return;
        }
        const previous = [...contentEl.childNodes];
        contentEl.innerHTML = this.html;
        this.el.classList.toggle("d-none", !this.html);
        this.registerCleanup(() => {
            contentEl.replaceChildren(...previous);
            this.el.classList.remove("d-none");
        });
    }
}

registry.category("public.interactions").add("website_aurora20.brand_logos", AuroraBrandLogos);
