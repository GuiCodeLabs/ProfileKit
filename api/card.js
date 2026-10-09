/** Serve the generated GitHub SVG with a visit count refreshed on origin requests. */

const SOURCE_REPOSITORY = process.env.PROFILE_REPOSITORY || "GuiCodeLabs/github-profile-card";
const PROFILE_USER = process.env.PROFILE_USER || "GuiCodeLabs";
const LOCALES = { "pt-BR": "", en: "-en", es: "-es" };
const CARD_TYPES = new Set(["stats", "languages", "rhythm"]);
const LIVE_RESPONSE_HEADERS = {
  "Cache-Control": "no-cache, no-store, max-age=0, must-revalidate",
  "CDN-Cache-Control": "no-store",
  "Vercel-CDN-Cache-Control": "no-store",
  Pragma: "no-cache",
  Expires: "0",
};
const LIVE_REQUEST_HEADERS = { "Cache-Control": "no-cache, no-store", Pragma: "no-cache" };

function disableCaching(response) {
  for (const [name, value] of Object.entries(LIVE_RESPONSE_HEADERS)) response.setHeader(name, value);
}

function fetchLive(url, timeoutMs) {
  return fetch(url, {
    cache: "no-store",
    headers: LIVE_REQUEST_HEADERS,
    signal: AbortSignal.timeout(timeoutMs),
  });
}

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
  disableCaching(response);
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
    const upstream = await fetchLive(source, 8000);
    if (!upstream.ok) throw new Error(`SVG source returned ${upstream.status}`);
    let svg = await upstream.text();
    if (kind === "stats") {
      try {
        const badge = await fetchLive(
          `https://komarev.com/ghpvc/?username=${encodeURIComponent(PROFILE_USER)}&style=flat-square`, 4000,
        );
        if (badge.ok) svg = injectVisits(svg, parseVisitsFromSvg(await badge.text()), locale);
      } catch (error) {
        console.error("Visit count unavailable; using the last snapshot:", error);
      }
    }
    response.setHeader("Content-Type", "image/svg+xml; charset=utf-8");
    response.setHeader("X-Content-Type-Options", "nosniff");
    // no-cache asks GitHub Camo to revalidate; no-store also bypasses Vercel's CDN cache.
    return response.status(200).send(svg);
  } catch (error) {
    console.error("Card SVG unavailable:", error);
    return response.status(503).send("Card temporarily unavailable");
  }
}
