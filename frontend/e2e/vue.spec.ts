import { test, expect } from '@playwright/test';

import { Page } from '@playwright/test';

// 设置页面缩放比例的函数
async function setPageZoom(page: Page, zoomPercentage: number) {
  // 设置页面缩放
  await page.addStyleTag({
    content: `
      body {
        transform: scale(${zoomPercentage / 100});
        transform-origin: 0 0;
        width: ${100 / (zoomPercentage / 100)}%;
        height: ${100 / (zoomPercentage / 100)}%;
      }
    `
  });
  
  // 等待缩放生效
  await page.waitForTimeout(500);
}

// 共享前置条件（可选）
test.beforeEach(async ({ page }) => {
  await page.goto('http://localhost:5173/');
  await page.waitForSelector('text=开始使用', { visible: true });
});

// 1. 上传功能测试
test('上传VCF文件功能', async ({ page }) => {
  // 点击上传按钮
  await page.click('text=开始使用');
  await page.waitForSelector('#vcfFile');

  // 上传测试文件
  await page.setInputFiles('#vcfFile', './e2e/fixtures/test.vcf');
  await page.click('button:has-text("提交分析")');
  await page.waitForSelector('.progress-text', { state: 'visible' });

  // 验证成功提示
  await expect(page.getByText('文件上传成功，正在处理...')).toBeVisible();
});
// 2. RSID查询功能测试
test('RSID查询功能', async ({ page }) => {
  await page.click('text=开始使用');
  // 输入有效RSID
  await page.fill('#rsid-input', 'rs1801516');
  await page.click('button:has-text("查询")');

  // 验证结果跳转
  await expect(page.getByText('分析结果')).toBeVisible();
});

// 3. 错误场景测试
test('错误处理验证', async ({ page }) => {
  await page.click('text=开始使用');
  // 上传无效文件
  await page.setInputFiles('#vcfFile', './e2e/fixtures/test.txt');
  await page.click('button:has-text("提交分析")');
  await expect(page.getByText('仅支持 .vcf 文件')).toBeVisible();
  await page.click('button:has-text("重置")');
  await page.click('button:has-text("提交分析")');
  await expect(page.getByText('请选择要上传的VCF文件')).toBeVisible();

  // 查询无效RSID
  await page.click('button:has-text("查询")');
  await expect(page.getByText('请输入有效的RSID')).toBeVisible();
  await page.fill('#rsid-input', 'invalidRSID');
  await page.click('button:has-text("查询")');
  await expect(page.getByText('RSID格式不正确')).toBeVisible();
});


const TEST_VCF_PATH = './e2e/fixtures/test.vcf';
test.describe('结果展示与交互测试', () => {
  test('完整流程测试：上传文件→查看结果→验证数据→下载PDF', async ({ page }) => {
    // 1. 上传VCF文件
    await page.goto('/upload');
    await page.locator('#vcfFile').setInputFiles(TEST_VCF_PATH);
    await page.locator('button[type="submit"]').click();

    // 2. 验证结果页面元素
    await validateResultPage(page);

    // 3. 验证交互功能
    await testInteractions(page);
  });
});
// 结果页面验证函数
async function validateResultPage(page: Page) {
  // 设置页面缩放
  await setPageZoom(page, 20);
  
  // 等待结果页面加载完成
  await page.waitForSelector('.card-header.bg-success', { timeout: 60000 });

  // 1. 验证PRS评分区域
  await expect(page.locator('h4:has-text("乳腺癌PRS评分")')).toBeVisible();
  const prsScore = page.locator('text=乳腺癌PRS评分:').locator('span.text-primary');
  await expect(prsScore).toBeVisible();
  await expect(prsScore).not.toBeEmpty();
  
  const prsRiskBadge = page.locator('text=乳腺癌PRS评分:').locator('span.badge');
  await expect(prsRiskBadge).toBeVisible();
  await expect(prsRiskBadge).not.toBeEmpty();
  
  // 2. 验证PRS区域的变异数量显示
  const prsVariantCount = page.locator('text=乳腺癌PRS评分:').locator('+ p.text-muted');
  await expect(prsVariantCount).toContainText('基于');
  await expect(prsVariantCount).toContainText('个变异计算');
  
  // 3. 验证神经网络预测区域
  await expect(page.locator('h4:has-text("神经网络预测乳腺癌风险")')).toBeVisible();
  const modelScore = page.locator('text=神经网络预测乳腺癌风险:').locator('span.text-primary');
  await expect(modelScore).toBeVisible();
  await expect(modelScore).not.toBeEmpty();
  
  const modelRiskBadge = page.locator('text=神经网络预测乳腺癌风险:').locator('span.badge');
  await expect(modelRiskBadge).toBeVisible();
  await expect(modelRiskBadge).not.toBeEmpty();
  
  // 4. 验证神经网络区域的变异数量显示
  const modelVariantCount = page.locator('text=神经网络预测乳腺癌风险:').locator('+ p.text-muted');
  await expect(modelVariantCount).toContainText('基于');
  await expect(modelVariantCount).toContainText('个变异计算');
  
  // 5. 验证表格标题
  const tableHeaders = [
    '变异ID', '染色体', '位置', '参考序列', '变异序列', 
    '基因型', '模型预测标签', '模型预测得分', '临床意义',
    '相关基因', '疾病名称', 'RegulomeDB分数'
  ];
  
  for (const header of tableHeaders) {
    await expect(page.locator(`th:has-text("${header}")`)).toBeVisible();
  }
  
  // 6. 验证表格数据行
  const tableRows = page.locator('.table.table-striped tbody tr');
  await expect(tableRows).not.toHaveCount(0);
  
  // 检查首行数据是否包含预期内容
  const firstRow = tableRows.first();
  await expect(firstRow.locator('td').nth(0)).not.toBeEmpty(); // 变异ID
  await expect(firstRow.locator('td').nth(1)).toContainText('chr'); // 染色体格式
  await expect(firstRow.locator('td').nth(5)).toContainText('/'); // 基因型格式
  

  // 8. 验证PDF下载按钮
  await expect(page.locator('button:has-text("生成PDF报告")')).toBeVisible();
  await expect(page.locator('button:has-text("生成PDF报告")')).toBeEnabled();

  // 9. 验证排序指示器
  const sortableHeaders = page.locator('.sortable-header');
  await expect(sortableHeaders).not.toHaveCount(0);

  // 10. 验证蛋白质变异区域（如果存在）
  const proteinSection = page.locator('.card-header.bg-info:has-text("蛋白质变异信息")');
  if (await proteinSection.count() > 0) {
    await expect(page.locator('text=蛋白质ID:')).toBeVisible();
  }
}

// 在交互测试中使用 - 同样使用页面缩放
async function testInteractions(page: Page) {
  // 设置页面缩放为33%
  await setPageZoom(page, 40);
  
  // 1. 测试分页
  await page.selectOption('select.form-select', '10');
  await page.waitForTimeout(1000); // 等待分页加载
  await expect(page.locator('.table tbody tr')).toHaveCount(15);

  // 2. 测试排序
  const chromHeader = page.locator('th:has-text("染色体")');
  await chromHeader.click();
  await page.waitForTimeout(1000); // 等待排序完成
}

