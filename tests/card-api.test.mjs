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

test("each origin request fetches the visit count and sends an uncacheable SVG", async () => {
  const previousFetch = globalThis.fetch;
  const requested = [];
  globalThis.fetch = async url => {
    requested.push(url);
    return {
      ok: true,
      text: async () => url.includes("komarev.com")
        ? '<svg><text>views</text><text>25</text></svg>'
        : '<svg data-visits="3"><text id="visits-value">3</text></svg>',
    };
  };
  const response = {
    code: null, body: null, headers: {},
    setHeader(key, value) { this.headers[key] = value; return this; },
    status(code) { this.code = code; return this; },
    send(body) { this.body = body; return this; },
  };
  try {
    await handler({ method: "GET", url: "/api/card?type=stats&locale=pt-BR" }, response);
    assert.equal(response.code, 200);
    assert.equal(response.headers["Cache-Control"], "no-store, max-age=0");
    assert.equal(response.headers["CDN-Cache-Control"], "no-store");
    assert.equal(requested.length, 2);
    assert.match(response.body, /id="visits-value">25<\/text>/);
  } finally {
    globalThis.fetch = previousFetch;
  }
});
