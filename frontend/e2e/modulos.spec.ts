import { test, expect } from '@playwright/test';

test.describe('Lideranças', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/liderancas');
  });

  test('lista de lideranças políticas carrega', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Lideranças Políticas' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Nome Completo' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Status' })).toBeVisible();
    // Sem lideranças cadastradas no ambiente de teste, a tabela exibe o estado vazio.
    await expect(page.getByText(/lideranças? no total|Nenhuma liderança encontrada/).first()).toBeVisible();
  });

  test('botão de cadastro abre o modal de nova liderança', async ({ page }) => {
    await page.getByRole('button', { name: 'Adicionar Liderança' }).click();
    await expect(page.getByRole('heading', { name: 'Nova Liderança' })).toBeVisible();
    await expect(page.getByPlaceholder('Ex: João da Silva')).toBeVisible();

    await page.getByRole('button', { name: 'Cancelar' }).click();
    await expect(page.getByRole('heading', { name: 'Nova Liderança' })).not.toBeVisible();
  });
});

test.describe('Emendas Orçamentárias', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/emendas');
  });

  test('KPIs e tabela de emendas carregam com filtros', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Emendas Orçamentárias' })).toBeVisible();

    // Cards de KPI (Total de Emendas, Valor Indicado, Valor Empenhado, Valor Pago).
    await expect(page.getByText('Total de Emendas')).toBeVisible();
    await expect(page.getByText('Valor Indicado')).toBeVisible();
    await expect(page.getByText('Valor Empenhado')).toBeVisible();
    await expect(page.getByText('Valor Pago')).toBeVisible();

    // Filtros da tabela: busca textual, ano de exercício e situação.
    await expect(page.getByPlaceholder('Buscar por objeto ou número...')).toBeVisible();
    await expect(page.getByPlaceholder('Ano')).toBeVisible();
    const situacaoSelect = page.locator('select').filter({ hasText: 'Todas as situações' });
    await expect(situacaoSelect).toBeVisible();
    await expect(situacaoSelect.locator('option')).toHaveText([
      'Todas as situações',
      'Indicada',
      'Empenhada',
      'Paga',
      'Cancelada',
    ]);

    await expect(page.getByRole('columnheader', { name: 'Situação' })).toBeVisible();
    await expect(page.getByText(/emendas? no total|Nenhuma emenda encontrada/).first()).toBeVisible();
  });
});

test.describe('Projetos de Lei', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/projetos-lei');
  });

  test('monitoramento legislativo carrega com busca externa e filtros', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Projetos de Lei', exact: true })).toBeVisible();

    // Busca nas fontes oficiais (ALRS, Câmara, Senado).
    await expect(page.getByText('Buscar nas fontes oficiais')).toBeVisible();
    await expect(page.getByPlaceholder('Nome do parlamentar (ex: Delegada Nadine)')).toBeVisible();

    // Listagem e filtro por fonte.
    await expect(page.getByRole('heading', { name: 'Projetos de lei acompanhados' })).toBeVisible();
    const fonteSelect = page.locator('select').filter({ hasText: 'Todas as fontes' });
    await expect(fonteSelect).toBeVisible();
    await expect(fonteSelect.locator('option')).toHaveText([
      'Todas as fontes',
      'Assembleia RS',
      'Câmara dos Deputados',
      'Senado Federal',
    ]);
    await expect(page.getByPlaceholder('Buscar por ementa/autor/número...')).toBeVisible();
  });
});
