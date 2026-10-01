import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { getStorefrontConfig } from "@website_aurora20/js/storefront_utils";

const STORAGE_KEY = "aurora_recent_searches";
const MAX_ENTRIES = 6;

function readSearches() {
    try {
        const value = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
        return Array.isArray(value) ? value.filter((v) => typeof v === "string") : [];
    } catch {
        return [];
    }
}

function rememberSearch(term) {
    term = (term || "").trim().slice(0, 80);
    if (term) {
        writeSearches([term, ...readSearches().filter((s) => s !== term)]);
    }
}

function writeSearches(searches) {
    try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(searches.slice(0, MAX_ENTRIES)));
    } catch {
        // Storage disabled: recent searches are a convenience only.
    }
}

/**
 * Recent searches of the visitor, kept in their own browser only and offered
 * as native suggestions (datalist) of the website search boxes.
 */
export class AuroraRecentSearches extends Interaction {
    static selector = ".o_searchbar_form";
    dynamicContent = {
        _root: { "t-on-submit": this.onSubmit },
    };

    setup() {
        this.enabled = getStorefrontConfig().recentSearches;
        this.inputEl = this.el.querySelector("input[name='search']");
    }

    start() {
        if (!this.enabled || !this.inputEl) {
            return;
        }
        // Searches also arrive as links (suggestions, shared URLs): remember
        // the search of the current results page too.
        rememberSearch(new URLSearchParams(window.location.search).get("search"));
        const searches = readSearches();
        if (!searches.length) {
            return;
        }
        const datalist = document.createElement("datalist");
        datalist.id = `o_aurora_recent_searches_${Math.random().toString(36).slice(2, 9)}`;
        for (const search of searches) {
            const option = document.createElement("option");
            option.value = search;
            datalist.append(option);
        }
        this.insert(datalist, this.el);
        this.inputEl.setAttribute("list", datalist.id);
        this.registerCleanup(() => this.inputEl.removeAttribute("list"));
    }

    onSubmit() {
        if (!this.enabled || !this.inputEl) {
            return;
        }
        rememberSearch(this.inputEl.value);
    }
}

registry.category("public.interactions").add("website_aurora20.recent_searches", AuroraRecentSearches);
