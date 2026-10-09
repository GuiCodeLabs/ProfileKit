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
    code: null, body: null, headers: {},
    setHeader(key, value) { this.headers[key] = value; return this; },
    status(code) { this.code = code; return this; },
    send(body) { this.body = body; return this; },
  };
  await handler({ method: "GET", url: "/api/card?type=stats&cache_bust=123" }, response);
  assert.equal(response.code, 400);
  assert.equal(response.body, "Invalid card type or locale");
});

test("each origin request bypasses caches and asks GitHub Camo to revalidate the image", async () => {
  const previousFetch = globalThis.fetch;
  const requested = [];
  let badgeCount = 24;
  globalThis.fetch = async (url, options) => {
    requested.push({ url, options });
    return {
      ok: true,
      text: async () => url.includes("komarev.com")
        ? `<svg><text>views</text><text>${++badgeCount}</text></svg>`
        : '<svg data-visits="3"><text id="visits-value">3</text></svg>',
    };
  };
  const makeResponse = () => ({
    code: null, body: null, headers: {},
    setHeader(key, value) { this.headers[key] = value; return this; },
    status(code) { this.code = code; return this; },
    send(body) { this.body = body; return this; },
  });
  try {
    const responses = [];
    for (let visit = 0; visit < 2; visit += 1) {
      const response = makeResponse();
      await handler({ method: "GET", url: "/api/card?type=stats&locale=pt-BR" }, response);
      responses.push(response);
      assert.equal(response.code, 200);
      assert.equal(response.headers["Cache-Control"], "no-cache, no-store, max-age=0, must-revalidate");
      assert.equal(response.headers["CDN-Cache-Control"], "no-store");
      assert.equal(response.headers["Vercel-CDN-Cache-Control"], "no-store");
      assert.equal(response.headers.Pragma, "no-cache");
      assert.equal(response.headers.Expires, "0");
    }
    assert.equal(requested.length, 4);
    for (const request of requested) {
      assert.equal(request.options.cache, "no-store");
      assert.deepEqual(request.options.headers, {
        "Cache-Control": "no-cache, no-store",
        Pragma: "no-cache",
      });
    }
    assert.match(responses[0].body, /id="visits-value">25<\/text>/);
    assert.match(responses[1].body, /id="visits-value">26<\/text>/);
  } finally {
    globalThis.fetch = previousFetch;
  }
});
