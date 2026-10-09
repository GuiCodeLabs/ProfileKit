const LOCALE_SUFFIX = Object.freeze({ "pt-BR": "", en: "-en", es: "-es" });
const CARD_LABELS = Object.freeze({
  "pt-BR": { stats: "Status do GitHub", languages: "Linguagens do GitHub", rhythm: "Ritmo de contribuições" },
  en: { stats: "GitHub status", languages: "GitHub languages", rhythm: "Contribution rhythm" },
  es: { stats: "Estado de GitHub", languages: "Lenguajes de GitHub", rhythm: "Ritmo de contribuciones" },
});
const CARD_TYPES = new Set(["stats", "languages", "rhythm"]);

export function detectLocale(language) {
  const normalized = String(language || "").toLowerCase();
  if (normalized.startsWith("es")) return "es";
  if (normalized.startsWith("en")) return "en";
  return "pt-BR";
}

export function validateOptions(options) {
  const username = String(options.username || "").trim();
  const repository = String(options.repository || "").trim();
  const cards = Array.isArray(options.cards) ? options.cards.filter(card => CARD_TYPES.has(card)) : [];
  if (!/^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$/.test(username)) {
    return { ok: false, code: "username" };
  }
  if (!/^[A-Za-z0-9._-]{1,100}$/.test(repository) || repository === "." || repository === "..") {
    return { ok: false, code: "repository" };
  }
  if (!cards.length) return { ok: false, code: "cards" };

  const locale = Object.hasOwn(LOCALE_SUFFIX, options.locale) ? options.locale : "pt-BR";
  const format = options.format === "markdown" ? "markdown" : "html";
  return { ok: true, value: { username, repository, cards, locale, format } };
}

function cardUrl(value, card) {
  const suffix = LOCALE_SUFFIX[value.locale];
  const file = card === "rhythm" ? `rhythm${suffix}.svg` : `${card}${suffix}.svg`;
  return `https://raw.githubusercontent.com/${value.username}/${value.repository}/stats-output/profile/${file}`;
}

function htmlEscape(value) {
  return String(value).replaceAll("&", "&amp;").replaceAll('"', "&quot;")
    .replaceAll("<", "&lt;").replaceAll(">", "&gt;");
}

function renderHtml(value) {
  const labels = CARD_LABELS[value.locale];
  const selectedTop = value.cards.filter(card => card === "stats" || card === "languages");
  const sections = [];
  if (selectedTop.length) {
    const images = selectedTop.map(card => {
      const src = htmlEscape(cardUrl(value, card));
      const alt = htmlEscape(labels[card]);
      const width = card === "stats" || card === "languages" ? 410 : 840;
      return `  <img src="${src}" width="${width}" alt="${alt}" />`;
    });
    sections.push(`<p align="center">\n${images.join("\n")}\n</p>`);
  }
  if (value.cards.includes("rhythm")) {
    const suffix = LOCALE_SUFFIX[value.locale];
    const base = `https://raw.githubusercontent.com/${value.username}/${value.repository}/stats-output/profile/`;
    sections.push(`<p align="center">\n  <picture>\n    <source media="(max-width: 600px)" srcset="${htmlEscape(`${base}rhythm-mobile${suffix}.svg`)}" />\n    <img src="${htmlEscape(`${base}rhythm${suffix}.svg`)}" width="840" alt="${htmlEscape(labels.rhythm)}" />\n  </picture>\n</p>`);
  }
  return sections.join("\n\n");
}

function renderMarkdown(value) {
  const labels = CARD_LABELS[value.locale];
  return value.cards.map(card => `![${labels[card]}](${cardUrl(value, card)})`).join("\n\n");
}

export function buildReadmeSnippet(options) {
  const result = validateOptions(options);
  if (!result.ok) {
    const error = new TypeError(`Invalid ProfileKit options: ${result.code}`);
    error.code = result.code;
    throw error;
  }
  return result.value.format === "markdown" ? renderMarkdown(result.value) : renderHtml(result.value);
}
