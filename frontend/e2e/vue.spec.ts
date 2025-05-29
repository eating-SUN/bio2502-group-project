// e2e/gene-analysis.spec.ts
import { test, expect, Page } from '@playwright/test';

// 测试前准备
test.beforeEach(async ({ page }) => {
  // 访问首页
  await page.goto('http://localhost:5173/')
});

// 测试导航功能
test('导航测试', async ({ page }) => {
  // 检查导航链接
  await expect(page.locator('nav >> text=首页')).toBeVisible({timeout: 10000});
  await expect(page.locator('nav >> text=上传')).toBeVisible({timeout: 10000});
  
  // 导航到上传页面
  await page.click('nav >> text=上传');
  await expect(page).toHaveURL(/upload/);
  await expect(page.locator('div:has-text("上传VCF文件")')).toBeVisible({timeout: 10000});
  
  // 导航到首页
  await page.click('nav >> text=首页');
  await expect(page).toHaveURL(/\//);
});

// 测试VCF文件上传流程
test('VCF文件上传流程', async ({ page }) => {
  // 导航到上传页面
  await page.click('nav >> text=上传');
  
  // 选择测试文件
  const filePath = 'e2e/fixtures/test.vcf';
  await page.setInputFiles('input[type="file"]', filePath);
  
  // 提交文件
  await page.click('button:has-text("提交分析")');
  
  // 检查上传状态
  await expect(page.locator('.progress-container')).toBeVisible({timeout: 10000});
  
  // 等待处理完成并跳转到结果页
  await page.waitForURL(/results/);
  
  // 验证结果页面内容
  await validateResultsPage(page);
});

// 测试RSID查询流程
test('RSID查询流程', async ({ page }) => {
  // 导航到上传页面
  await page.click('nav >> text=上传');
  
  // 输入RSID
  await page.fill('#rsid-input', 'rs123456');
  
  // 提交查询
  await page.click('button:has-text("查询")');
  
  // 检查处理状态
  await expect(page.locator('.progress-container')).toBeVisible();
  
  // 等待处理完成并跳转到结果页
  await page.waitForURL(/results/);
  
  // 验证结果页面内容
  await validateResultsPage(page);
});

// 测试无效文件上传
test('无效文件上传处理', async ({ page }) => {
  // 导航到上传页面
  await page.click('nav >> text=上传');
  
  // 尝试提交空文件
  await page.click('button:has-text("提交分析")');
  
  // 验证错误提示
  await expect(page.locator('.alert-danger:has-text("请选择要上传的VCF文件")')).toBeVisible();
  
  // 上传大文件
  const largeFilePath = 'e2e/fixtures/large.vcf';
  await page.setInputFiles('input[type="file"]', largeFilePath);
  await page.click('button:has-text("提交分析")');
  
  // 验证文件大小错误
  await expect(page.locator('.alert-danger:has-text("文件大小不能超过")')).toBeVisible();
});

// 测试无效RSID查询
test('无效RSID查询处理', async ({ page }) => {
  // 导航到上传页面
  await page.click('nav >> text=上传');
  
  // 尝试提交空RSID
  await page.click('button:has-text("查询")');
  
  // 验证错误提示
  await expect(page.locator('.alert-danger:has-text("请输入有效的RSID")')).toBeVisible();
  
  // 输入无效格式
  await page.fill('#rsid-input', 'invalid_rsid');
  await page.click('button:has-text("查询")');
  
  // 验证格式错误
  await expect(page.locator('.alert-danger:has-text("RSID格式不正确")')).toBeVisible();
});

// 测试结果页面直接访问
test('结果页面直接访问处理', async ({ page }) => {
  // 直接访问结果页
  await page.goto('http://localhost:5173/results');
  
  // 验证错误提示
  await expect(page.locator('.alert alert-danger:has-text("无效的任务ID")')).toBeVisible();
});

// 测试无效任务ID处理
test('无效任务ID处理', async ({ page }) => {
  // 访问带无效ID的结果页
  await page.goto('http://localhost:5173/results?task_id=invalid_id');
  
  // 验证错误提示
  await expect(page.locator('.alert alert-danger:has-text("任务ID无效")')).toBeVisible();
});

// 验证结果页面的辅助函数
async function validateResultsPage(page: Page) {
  // 等待结果加载完成
  await page.waitForSelector('.card-header bg-success text-white:has-text("分析结果")');
  
  // 检查PRS评分和风险等级
  const prsScore = page.locator('h4:has-text("PRS评分:")');
  await expect(prsScore).toBeVisible();
  
  const riskBadge = page.locator('.badge');
  await expect(riskBadge).toHaveClass(/bg-(success|warning|danger|secondary)/);
  
  // 检查变异表格
  const table = page.locator('table.table-striped');
  await expect(table).toBeVisible();
  
  // 检查分页控件
  const pagination = page.locator('.pagination');
  await expect(pagination).toBeVisible();
  
  // 检查图表
  const charts = page.locator('.chart-container');
  await expect(charts).toHaveCount(2);
  
  // 检查PDF下载按钮
  const downloadBtn = page.locator('button:has-text("生成PDF报告")');
  await expect(downloadBtn).toBeVisible();
  
  // 点击下载按钮
  await downloadBtn.click();
  
  // 验证下载功能（模拟）
  await expect(page.locator('text=PDF报告生成功能将在后端实现')).toBeVisible();
}