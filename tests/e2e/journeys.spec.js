const { test, expect } = require("@playwright/test");
const { spawn } = require("child_process");
const fs = require("fs");
const path = require("path");

const ARTIFACT_DIR = path.join(__dirname, "..", "..", "artifacts", "journeys");
const PORT = process.env.PORT || "8000";
const PYTHON = process.env.PYTHON || "python3";
let server;

test.describe.configure({ mode: "serial" });

async function waitForServer(port, attempts = 10) {
  for (let i = 0; i < attempts; i += 1) {
    try {
      const response = await fetch(`http://localhost:${port}`);
      if (response.ok) return;
    } catch (err) {
      // retry
    }
    await new Promise((resolve) => setTimeout(resolve, 300));
  }
  throw new Error(`Server did not start on port ${port}`);
}

test.beforeAll(async () => {
  fs.mkdirSync(ARTIFACT_DIR, { recursive: true });
  const docsDir = path.join(__dirname, "..", "..", "docs");
  server = spawn(PYTHON, ["-m", "http.server", PORT, "--directory", docsDir], {
    stdio: "inherit",
  });
  await waitForServer(PORT);
});

test.afterAll(() => {
  if (server && !server.killed) server.kill();
});

test.beforeEach(async ({ page }) => {
  await page.goto(`http://localhost:${PORT}`);
  await page.evaluate(() => localStorage.clear());
  await page.reload();
  await page.waitForSelector('[data-hs-ready="1"]');
});

test("explore renders clusters, dense rows, and real event data", async ({ page }) => {
  await expect(page.locator("#tab-bar [data-view='explore']")).toHaveAttribute("aria-current", "page");
  await expect(page.locator(".cluster-card")).not.toHaveCount(0);
  await expect(page.locator(".cluster-card .why-blurb").first()).toContainText("Why this works");
  await expect(page.locator(".preference-chip")).toHaveCount(6);
  await expect(page.locator(".item-row")).not.toHaveCount(0);
  await expect(page.locator("body")).toContainText("Chicago at Proctors");
  await expect(page.locator("body")).not.toContainText("undefined");

  const rowInfo = await page.evaluate(() => {
    const root = document.querySelector("#view-root").getBoundingClientRect();
    const rows = [...document.querySelectorAll(".item-row")].map((row) => row.getBoundingClientRect());
    return {
      firstRowHeight: Math.round(rows[0].height),
      visibleRows: rows.filter((rect) => rect.top >= root.top && rect.bottom <= root.bottom).length,
    };
  });
  expect(rowInfo.firstRowHeight).toBeLessThanOrEqual(72);
  expect(rowInfo.visibleRows).toBeGreaterThanOrEqual(3);

  await page.screenshot({ path: path.join(ARTIFACT_DIR, "01-explore.png"), fullPage: false });
});

test("pwa metadata and service worker are available", async ({ page }) => {
  await expect(page.locator('link[rel="manifest"]')).toHaveAttribute("href", "manifest.webmanifest");
  await expect(page.locator('link[rel="apple-touch-icon"]')).toHaveAttribute("href", "apple-touch-icon.png");
  const manifest = await page.evaluate(async () => {
    const response = await fetch("manifest.webmanifest");
    return response.json();
  });
  expect(manifest.display).toBe("standalone");
  expect(manifest.name).toContain("Happenstance");
  expect(manifest.icons.some((icon) => icon.src === "icon-192.png" && icon.type === "image/png")).toBe(true);

  const registered = await page.evaluate(async () => {
    if (!("serviceWorker" in navigator)) return false;
    await navigator.serviceWorker.ready;
    return Boolean(await navigator.serviceWorker.getRegistration());
  });
  expect(registered).toBe(true);
});

test("preference chips rerank results, highlight matches, and persist", async ({ page }) => {
  await page.getByRole("button", { name: "Art & Culture", exact: true }).click();

  await expect(page.locator(".preference-chip.active")).toContainText("Art & Culture");
  await expect(page.locator(".preference-badges").first()).toContainText("Art & Culture");
  await expect(page.locator(".item-row").first()).toContainText("Art & Culture");

  const stored = await page.evaluate(() => localStorage.getItem("happenstance_prefs"));
  expect(JSON.parse(stored)).toContain("art-culture");

  await page.reload();
  await page.waitForSelector('[data-hs-ready="1"]');
  await expect(page.locator(".preference-chip.active")).toContainText("Art & Culture");

  await page.setViewportSize({ width: 390, height: 844 });
  await page.reload();
  await page.waitForSelector('[data-hs-ready="1"]');
  const chipsFit = await page.evaluate(() => {
    const chipRow = document.querySelector(".preference-chips");
    return chipRow && chipRow.scrollWidth <= chipRow.clientWidth + 1;
  });
  expect(chipsFit).toBe(true);

  await page.click("#filter-toggle");
  await page.getByRole("button", { name: "⭐ 4+", exact: true }).click();
  await expect(page.locator(".item-row").first()).toContainText("⭐");

  await page.screenshot({ path: path.join(ARTIFACT_DIR, "01b-preferences-mobile.png"), fullPage: false });
});

test("target ZIP sorts by miles and surfaces Saratoga clusters", async ({ page }) => {
  await page.click("#filter-toggle");
  await page.fill('[data-action="target-input"]', "12866");
  await page.click('[data-action="apply-target"]');

  await expect(page.locator('[data-action="sort"]')).toHaveValue("distance");
  await expect(page.locator(".cluster-card").first()).toContainText("Saratoga Springs");
  await expect(page.locator(".distance").first()).toContainText("mi");
  await expect(page.locator(".distance").first()).not.toContainText("km");

  await page.screenshot({ path: path.join(ARTIFACT_DIR, "02-saratoga-target.png"), fullPage: false });
});

test("bottom sheet shows pairings for tapped rows", async ({ page }) => {
  await page.locator(".item-row").first().click();
  await page.waitForSelector("body.sheet-open");

  await expect(page.locator(".bottom-sheet")).toContainText("Pairings");
  await expect(page.locator(".bottom-sheet")).toContainText("Tickets");
  await expect(page.locator(".bottom-sheet")).toContainText("Event details");
  await expect(page.locator(".pairing-list .pairing-card")).not.toHaveCount(0);
  await expect(page.locator(".bottom-sheet")).toContainText("Why this works");
  const longBlurbs = await page.evaluate(() => {
    return [...document.querySelectorAll(".bottom-sheet .why-blurb p")]
      .map((node) => node.textContent.trim().split(/\s+/).filter(Boolean).length)
      .filter((count) => count > 40);
  });
  expect(longBlurbs).toHaveLength(0);

  await page.getByLabel("Close").click();
  await expect(page.locator("body")).not.toHaveClass(/sheet-open/);
  await page.screenshot({ path: path.join(ARTIFACT_DIR, "03-sheet-pairings.png"), fullPage: false });
});

test("timeline, saved, and plan views work from bottom tabs", async ({ page }) => {
  await page.click("#tab-bar [data-view='timeline']");
  await expect(page.locator("#tab-bar [data-view='timeline']")).toHaveAttribute("aria-current", "page");
  await expect(page.locator(".timeline-day")).toHaveCount(7);
  await expect(page.locator(".timeline-slot")).not.toHaveCount(0);

  await page.click("#tab-bar [data-view='saved']");
  await expect(page.locator("#tab-bar [data-view='saved']")).toHaveAttribute("aria-current", "page");
  await expect(page.locator(".empty")).toContainText("Nothing saved yet");

  await page.click("#tab-bar [data-view='plan']");
  await expect(page.locator("#tab-bar [data-view='plan']")).toHaveAttribute("aria-current", "page");
  await expect(page.locator(".empty")).toContainText("Your plan is empty");

  await page.screenshot({ path: path.join(ARTIFACT_DIR, "04-tabs.png"), fullPage: false });
});

test("cluster plan button creates a restaurant plus event plan", async ({ page }) => {
  await page.click("#filter-toggle");
  await page.fill('[data-action="target-input"]', "12866");
  await page.click('[data-action="apply-target"]');
  await page.locator(".cluster-card .cluster-link").first().click();
  await page.waitForSelector("body.sheet-open");
  await expect(page.locator(".bottom-sheet")).toContainText("Address");
  await expect(page.locator(".bottom-sheet")).toContainText("Menu");
  await page.getByLabel("Close").click();
  await expect(page.locator("body")).not.toHaveClass(/sheet-open/);

  await page.locator(".cluster-card [data-action='add-cluster-plan']").first().click();

  await expect(page.locator("#tab-bar [data-view='plan']")).toHaveAttribute("aria-current", "page");
  await expect(page.locator(".plan-card")).toHaveCount(2);
  await expect(page.locator(".plan-summary")).toContainText("2 items");

  await page.screenshot({ path: path.join(ARTIFACT_DIR, "05-cluster-plan.png"), fullPage: false });
});
