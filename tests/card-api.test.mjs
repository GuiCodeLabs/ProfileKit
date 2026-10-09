import assert from "node:assert/strict";
import test from "node:test";
import handler, { injectVisits, parseVisitsFromSvg } from "../api/card.js";

test("badge count parses its last numeric text", () => {
  const badge = '<svg><text>views</text><text>1,234</text><text>1,234</text></svg>';
  assert.equal(parseVisitsFromSvg(badge), 1234);
  assert.equal(parseVisitsFromSvg('<svg><text>offline</text></svg>'), null);
});

test("only the visit field is updated in the card", () => {
  const original = '<svg data-visits="1"><text>141 commits</text><text id="visits-value" x="2">1</text></svg>';
  assert.equal(injectVisits(original, 2345, "pt-BR"),
    '<svg data-visits="2345"><text>141 commits</text><text id="visits-value" x="2">2.345</text></svg>');
});

test("unknown query parameters are rejected before calling external services", async () => {
  const response = {
    code: null, body: null,
    status(code) { this.code = code; return this; },
    send(body) { this.body = body; return this; },
  };
  await handler({ method: "GET", url: "/api/card?type=stats&cache_bust=123" }, response);
  assert.equal(response.code, 400);
  assert.equal(response.body, "Invalid card type or locale");
});
