const { chromium } = require("playwright");
const path = require("node:path");
const fs = require("node:fs");
const os = require("node:os");
const { execFileSync } = require("node:child_process");
(async () => {
  const root = path.resolve(__dirname, "../..");
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), "skillspine-browser-"));
  execFileSync(process.env.PYTHON || "python", [
    "-m",
    "skillspine",
    path.join(root, "examples/collection"),
    "--changed",
    "shared/rubric.md",
    "--format",
    "html",
    "--output",
    path.join(temp, "report.html"),
    "--fail-on",
    "never",
  ]);
  const browser = await chromium.launch({
    channel: process.env.SKILLSPINE_BROWSER_CHANNEL || undefined,
    headless: true,
  });
  try {
    const page = await browser.newPage({
      viewport: { width: 1440, height: 1100 },
      deviceScaleFactor: 1,
    });
    const errors = [];
    page.on("pageerror", (e) => errors.push(e.message));
    const network = [];
    page.on("request", (r) => {
      if (/^https?:/.test(r.url())) network.push(r.url());
    });

    await page.goto(
      require("node:url").pathToFileURL(path.join(temp, "report.html")).href,
    );
    const assert = (v, m) => {
      if (!v) throw Error(m);
    };
    assert(
      (await page.locator(".skill:visible").count()) === 3,
      "three skills",
    );
    assert(
      (await page.locator(".warn:visible").count()) === 2,
      "two isolated failures",
    );

    await page.selectOption("#layout", "collection");
    assert(
      (await page.locator(".warn:visible").count()) === 0,
      "collection should be clean",
    );
    await page.check("#affected");
    assert(
      (await page.locator(".skill:visible").count()) === 2,
      "two affected skills",
    );
    await page.fill("#search", "skills/review");
    assert(
      (await page.locator(".skill:visible").count()) === 1,
      "search narrows to review",
    );
    await page.fill("#search", "not-a-path");
    assert(await page.locator("#empty").isVisible(), "empty state");
    await page.fill("#search", "");
    await page.uncheck("#affected");
    const downloadPromise = page.waitForEvent("download");
    await page.click("#download");
    const download = await downloadPromise;
    await download.saveAs(path.join(temp, "download.json"));
    const data = JSON.parse(
      require("node:fs").readFileSync(path.join(temp, "download.json"), "utf8"),
    );
    assert(
      data.schema_version === 1 && data.skills.length === 3,
      "JSON export",
    );
    await page.setViewportSize({ width: 390, height: 844 });
    await page.selectOption("#layout", "isolated");
    assert(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
      "mobile overflow",
    );

    assert(errors.length === 0, "JS errors: " + errors.join());
    assert(network.length === 0, "network requests");
    console.log(
      "PASS: desktop, mobile, layout toggle, impact filter, search, empty state, JSON download, no script errors, zero HTTP requests",
    );
  } finally {
    await browser.close();
    fs.rmSync(temp, { recursive: true, force: true });
  }
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
