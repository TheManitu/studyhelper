import { test, expect } from '@playwright/test';

const USERS = {
  alice: { user: process.env.TEST_USER || 'alice', pass: process.env.TEST_PASS || 'alice' },
};

test('NiceGUI: login, see dashboard, logout', async ({ page, baseURL }) => {
  // Wait until Keycloak discovery is reachable to avoid flakiness
  for (let i = 0; i < 30; i++) {
    const r = await page.request.get('http://localhost:8080/realms/studyhelper/.well-known/openid-configuration');
    if (r.ok()) break;
    await page.waitForTimeout(1000);
  }

  // Go to NiceGUI root; should redirect to Keycloak login
  await page.goto(baseURL!);

  // On Keycloak login page
  await expect(page.locator('#username')).toBeVisible();
  await expect(page.locator('#password')).toBeVisible();

  await page.locator('#username').fill(USERS.alice.user);
  await page.locator('#password').fill(USERS.alice.pass);
  await page.locator('#kc-login').click();

  // Should be back on app dashboard
  await page.waitForURL(baseURL! + '/', { waitUntil: 'load' });
  await expect(page.getByText('To‑Do Liste').or(page.getByText('To-Do Liste'))).toBeVisible();
  await expect(page.getByText('Pomodoro Timer')).toBeVisible();

  // Click logout and ensure we end up unauthenticated
  await page.getByRole('link', { name: 'Logout' }).click();

  // After IdP logout we should land back and be asked to login again
  for (let i = 0; i < 10; i++) {
    await page.goto(baseURL! + '/');
    if (await page.locator('#username').isVisible().catch(() => false)) break;
    await page.waitForTimeout(500);
  }
  await expect(page.locator('#username')).toBeVisible();
});

test('Keycloak discovery exposes PKCE S256', async ({ page }) => {
  const discovery = await page.request.get('http://localhost:8080/realms/studyhelper/.well-known/openid-configuration');
  expect(discovery.ok()).toBeTruthy();
  const json = await discovery.json();
  expect(json.issuer).toBe('http://localhost:8080/realms/studyhelper');
  expect(json.code_challenge_methods_supported).toContain('S256');
});
