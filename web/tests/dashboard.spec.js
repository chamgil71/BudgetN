import { test, expect } from '@playwright/test';

test.describe('KAIB2026 Dashboard Verification', () => {
    test.setTimeout(120000); // 2 minutes
    
    test.beforeEach(async ({ page }) => {
        // Vite dev server URL
        await page.goto('http://localhost:5173/', { waitUntil: 'domcontentloaded' });
        // Close any initial modal/overlay if it exists (like the one mentioned in diagnosis)
        await page.keyboard.press('Escape');
    });

    test('Header statistics are visible', async ({ page }) => {
        const budgetElem = page.locator('#stat-budget');
        await expect(budgetElem).not.toHaveText('-');
        const budget = await page.textContent('#stat-budget');
        console.log('Total Budget in Header:', budget);
        expect(budget).toContain('조');
    });

    test('Navigate through all main tabs', async ({ page }) => {
        const tabs = ['overview', 'department', 'field', 'duplicate', 'projects'];
        for (const tab of tabs) {
            await page.click(`.tab-btn[data-tab="${tab}"]`);
            await expect(page.locator(`.tab-content#tab-${tab}`)).toBeVisible();

            // Check for chart canvases in relevant tabs
            if (tab === 'overview') {
                await expect(page.locator('#chart-dept-donut')).toBeVisible();
            } else if (tab === 'department') {
                await expect(page.locator('#dept-table-container')).toBeVisible();
            } else if (tab === 'field') {
                await expect(page.locator('#treemap-container')).toBeVisible();
                // Check if Treemap contains [object Object] - which we fixed
                const treemapText = await page.textContent('#treemap-container');
                expect(treemapText).not.toContain('[object Object]');
            } else if (tab === 'duplicate') {
                await expect(page.locator('#dup-kpi-grid')).toBeVisible();
                const groupCount = await page.textContent('#dup-kpi-grid .kpi-card .value');
                console.log('Similar Groups found:', groupCount);
                expect(parseInt(groupCount)).toBeGreaterThan(0);
            }
        }
    });

    test('Search functionality in projects tab', async ({ page }) => {
        await page.click('.tab-btn[data-tab="projects"]');
        await page.fill('#project-search', '반도체');
        await page.waitForTimeout(500); // Wait for debounce
        const projectCount = await page.textContent('#project-count');
        console.log('Search "반도체" count:', projectCount);
        expect(projectCount).toContain('총');
    });
});
