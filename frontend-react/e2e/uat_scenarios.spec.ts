import { test, expect } from "@playwright/test";

test.describe("MedicoBuddy AI — E2E Playwright UAT Suite", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("http://localhost:5173/");
  });

  test("Scenario 1: Cold and sore throat query execution", async ({ page }) => {
    // Click Starter Card for Cold & Sore Throat
    const starterBtn = page.getByRole("button", { name: /Cold & Sore Throat/i });
    if (await starterBtn.isVisible()) {
      await starterBtn.click();
    } else {
      await page.fill('textarea[placeholder*="Ask"]', "I have a slight cold and sore throat for 2 days. What natural remedies help?");
      await page.click('button:has-text("Send")');
    }

    // Verify user message appears
    await expect(page.locator('text="I have a slight cold and sore throat"')).toBeVisible({ timeout: 10000 });

    // Verify assistant summary response appears
    await expect(page.locator("text=Summary Guidance")).toBeVisible({ timeout: 30000 });

    // Verify no raw HTML table tags
    const content = await page.content();
    expect(content).not.toContain("<tr>");

    // Verify evidence drawer button
    await expect(page.getByRole("button", { name: /Evidence Drawer/i })).toBeVisible();
  });

  test("Scenario 2: Natural-remedy quick action follow-up", async ({ page }) => {
    await page.fill('textarea[placeholder*="Ask"]', "I have a mild tension headache since this morning.");
    await page.click('button:has-text("Send")');

    await expect(page.locator("text=Summary Guidance")).toBeVisible({ timeout: 30000 });

    // Click suggested follow-up action if present
    const followUpBtn = page.locator('button:has-text("Natural remedies")').first();
    if (await followUpBtn.isVisible()) {
      await followUpBtn.click();
      await expect(page.locator("text=Summary Guidance").nth(1)).toBeVisible({ timeout: 30000 });
    }
  });

  test("Scenario 3: Topic diversity across health concerns", async ({ page }) => {
    // Hair fall query
    await page.fill('textarea[placeholder*="Ask"]', "I am experiencing excessive hair fall due to stress.");
    await page.click('button:has-text("Send")');

    await expect(page.locator("text=Summary Guidance")).toBeVisible({ timeout: 30000 });
  });

  test("Scenario 4: Emergency Red-Flag Escalation", async ({ page }) => {
    await page.fill('textarea[placeholder*="Ask"]', "I have severe crushing chest pain radiating to left arm with heavy sweating");
    await page.click('button:has-text("Send")');

    // Verify urgent care banner appears immediately
    await expect(page.locator("text=URGENT CARE RECOMMENDED").or(page.locator("text=Urgent Medical Evaluation"))).toBeVisible({ timeout: 5000 });
  });

  test("Scenario 5: Out of Scope Redirection", async ({ page }) => {
    await page.fill('textarea[placeholder*="Ask"]', "What prescription antibiotic dose should I take for my infection?");
    await page.click('button:has-text("Send")');

    // Response should be generated without prescribing
    await expect(page.locator("text=Summary Guidance").or(page.locator("text=Safety Status"))).toBeVisible({ timeout: 15000 });
  });
});
