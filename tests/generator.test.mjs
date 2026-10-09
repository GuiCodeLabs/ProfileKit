import test from "node:test";
import assert from "node:assert/strict";
import { buildReadmeSnippet, detectLocale, validateOptions } from "../web/generator.js";

const baseOptions = {
  username: "octocat",
  repository: "github-profile-card",
  locale: "pt-BR",
  format: "html",
  cards: ["stats", "languages", "rhythm"],
  liveViews: false,
  deploymentUrl: "",
};

test("browser languages map to the supported UI locales", () => {
  assert.equal(detectLocale("pt-PT"), "pt-BR");
  assert.equal(detectLocale("en-US"), "en");
  assert.equal(detectLocale("es-MX"), "es");
});

test("HTML output uses the requested localized assets and responsive rhythm card", () => {
  const snippet = buildReadmeSnippet({ ...baseOptions, locale: "en" });
  assert.match(snippet, /profile\/stats-en\.svg/);
  assert.match(snippet, /profile\/languages-en\.svg/);
  assert.match(snippet, /profile\/rhythm-mobile-en\.svg/);
  assert.match(snippet, /media="\(max-width: 600px\)"/);
  assert.equal((snippet.match(/<img /g) || []).length, 3);
});

test("live Vercel image endpoint is escaped as valid HTML", () => {
  const snippet = buildReadmeSnippet({
    ...baseOptions,
    cards: ["stats"],
    liveViews: true,
    deploymentUrl: "https://cards.example.com/ignored/path",
  });
  assert.match(snippet, /https:\/\/cards\.example\.com\/api\/card\?type=stats&amp;locale=pt-BR/);
  assert.doesNotMatch(snippet, /ignored/);
});

test("Markdown emits only selected cards and localized file names", () => {
  const snippet = buildReadmeSnippet({ ...baseOptions, format: "markdown", locale: "es", cards: ["languages"] });
  assert.match(snippet, /profile\/languages-es\.svg/);
  assert.doesNotMatch(snippet, /stats/);
  assert.doesNotMatch(snippet, /rhythm/);
});

test("invalid inputs are rejected before generating an embed", () => {
  assert.equal(validateOptions({ ...baseOptions, username: "not/a/user" }).code, "username");
  assert.equal(validateOptions({ ...baseOptions, repository: "bad repo" }).code, "repository");
  assert.equal(validateOptions({ ...baseOptions, cards: [] }).code, "cards");
  assert.equal(validateOptions({ ...baseOptions, liveViews: true }).code, "deployment");
  assert.throws(() => buildReadmeSnippet({ ...baseOptions, cards: [] }), error => error.code === "cards");
});
