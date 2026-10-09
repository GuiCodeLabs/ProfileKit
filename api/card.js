/** Serve the generated GitHub SVG with a visit count refreshed on origin requests. */

const SOURCE_REPOSITORY = process.env.PROFILE_REPOSITORY || "GuiCodeLabs/github-profile-card";
const PROFILE_USER = process.env.PROFILE_USER || "GuiCodeLabs";
const LOCALES = { "pt-BR": "", en: "-en", es: "-es" };
const CARD_TYPES = new Set(["stats", "languages", "rhythm"]);

export function parseVisitsFromSvg(svg) {
  const matches = [...svg.matchAll(/<text\b[^>]*>([\d,]+)<\/text>/g)];
  if (!matches.length) return null;
  const value = Number(matches.at(-1)[1].replaceAll(",", ""));
  return Number.isSafeInteger(value) && value >= 0 ? value : null;
}

export function injectVisits(svg, visits, locale) {
  if (!Number.isSafeInteger(visits) || visits < 0) return svg;
  const rendered = locale === "pt-BR" ? visits.toLocaleString("pt-BR") : visits.toLocaleString("en-US");
  return svg
    .replace(/data-visits="[^"]*"/, `data-visits="${visits}"`)
    .replace(/(<text id="visits-value"[^>]*>)[^<]*(<\/text>)/,
      (_match, before, after) => `${before}${rendered}${after}`);
}

export default async function handler(request, response) {
  if (request.method !== "GET") {
    response.setHeader("Allow", "GET");
    return response.status(405).end();
  }
  const url = new URL(request.url, "https://profile-card.invalid");
  const kind = url.searchParams.get("type") || "stats";
  const locale = url.searchParams.get("locale") || "pt-BR";
  if ([...url.searchParams.keys()].some(key => !["type", "locale"].includes(key)) ||
      !CARD_TYPES.has(kind) || !Object.hasOwn(LOCALES, locale)) {
    return response.status(400).send("Invalid card type or locale");
  }
  const file = `${kind}${LOCALES[locale]}.svg`;
  const source = `https://raw.githubusercontent.com/${SOURCE_REPOSITORY}/main/profile/${file}`;
  try {
    const upstream = await fetch(source, { cache: "no-store", signal: AbortSignal.timeout(8000) });
    if (!upstream.ok) throw new Error(`SVG source returned ${upstream.status}`);
    let svg = await upstream.text();
    if (kind === "stats") {
      try {
        const badge = await fetch(
          `https://komarev.com/ghpvc/?username=${encodeURIComponent(PROFILE_USER)}&style=flat-square`,
          { cache: "no-store", signal: AbortSignal.timeout(4000) },
        );
        if (badge.ok) svg = injectVisits(svg, parseVisitsFromSvg(await badge.text()), locale);
      } catch (error) {
        console.error("Visit count unavailable; using the last snapshot:", error);
      }
    }
    response.setHeader("Content-Type", "image/svg+xml; charset=utf-8");
    response.setHeader("X-Content-Type-Options", "nosniff");
    response.setHeader("Cache-Control", "public, max-age=0, s-maxage=60, stale-while-revalidate=30");
    return response.status(200).send(svg);
  } catch (error) {
    console.error("Card SVG unavailable:", error);
    response.setHeader("Cache-Control", "no-store");
    return response.status(503).send("Card temporarily unavailable");
  }
}
