import { test, expect } from '@playwright/test';

const PDF_MINIMO = Buffer.from('%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n');

test.describe('Balcão Inteligente — Jornada E2E Completa (BAL-11)', () => {
  test('portal público -> comutador IA/Regex -> triagem/efetivação -> descarte -> timeline -> resolução -> grafo', async ({
    page,
    browser,
  }) => {
    const errosConsole: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') errosConsole.push(msg.text());
    });
    page.on('pageerror', (err) => {
      errosConsole.push(String(err));
    });

    await page.goto('/balcao');
    await expect(page.getByRole('button', { name: 'Caixa de Entrada' })).toBeVisible();

    // 1. Aba Portais Públicos: comutar IA <-> Regex e gerar portal
    await page.getByRole('button', { name: 'Portais Públicos' }).click();
    await expect(page.getByLabel('Motor de extração')).toBeVisible();

    await page.getByLabel('Motor de extração').selectOption('ollama');
    await page.getByLabel('Modelo de IA').fill('llama3.2');
    await page.getByRole('button', { name: 'Aplicar Motor' }).click();
    await expect(page.getByText(/Motor de extração atualizado para "ollama"/i)).toBeVisible();

    await page.getByLabel('Motor de extração').selectOption('regex');
    await page.getByLabel('Modelo de IA').fill('');
    await page.getByRole('button', { name: 'Aplicar Motor' }).click();
    await expect(page.getByText(/Motor de extração atualizado para "regex"/i)).toBeVisible();

    await page.getByRole('button', { name: 'Gerar Novo Portal' }).click();
    const codigoLink = page.locator('code').filter({ hasText: '/portal/' });
    await expect(codigoLink).toBeVisible();
    const linkTexto = (await codigoLink.textContent()) ?? '';
    const tokenMatch = linkTexto.match(/\/portal\/([^\s]+)/);
    expect(tokenMatch?.[1]).toBeTruthy();
    const rotaPortal = `/portal/${tokenMatch![1]}`;

    // 2. Contexto público isolado (sem cookies de sessão): enviar 2 entradas
    const publicContext = await browser.newContext();
    const publicPage = await publicContext.newPage();
    publicPage.on('console', (msg) => {
      if (msg.type() === 'error') errosConsole.push(`[portal] ${msg.text()}`);
    });
    publicPage.on('pageerror', (err) => {
      errosConsole.push(`[portal] ${String(err)}`);
    });

    const marcadorEfetivar = `E2E-Efetivar-${Date.now()}`;
    const marcadorDescartar = `E2E-Descartar-${Date.now()}`;

    await publicPage.goto(rotaPortal);
    await publicPage.locator('textarea').fill(
      `Sou Maria Silva (${marcadorEfetivar}), fone (51) 99999-1234, preciso de atendimento em Porto Alegre.`
    );
    await publicPage.locator('input[type="file"]').setInputFiles({
      name: 'documento.pdf',
      mimeType: 'application/pdf',
      buffer: PDF_MINIMO,
    });
    await publicPage.getByRole('button', { name: /Enviar/i }).click();
    await expect(publicPage.getByRole('status').filter({ hasNotText: 'AMBIENTE DE' })).toBeVisible();

    // Segunda entrada para testar descarte
    await publicPage.goto(rotaPortal);
    await publicPage.locator('textarea').fill(`Entrada de teste para descarte (${marcadorDescartar}).`);
    await publicPage.getByRole('button', { name: /Enviar/i }).click();
    await expect(publicPage.getByRole('status').filter({ hasNotText: 'AMBIENTE DE' })).toBeVisible();
    await publicContext.close();

    // 3. Voltar para Caixa de Entrada, atualizar lista via filtro, efetivar e resolver com evidência
    await page.getByRole('button', { name: 'Caixa de Entrada' }).click();
    await page.getByRole('button', { name: 'Todas' }).click();
    await page.getByRole('button', { name: 'Pendentes' }).click();

    const itemEfetivar = page.getByText(marcadorEfetivar).first();
    await expect(itemEfetivar).toBeVisible({ timeout: 15_000 });
    await itemEfetivar.click();

    await page.locator('#triagem-nome').fill('Maria Silva E2E');
    await page.locator('#triagem-resumo').fill(`Atendimento E2E ${marcadorEfetivar}`);
    await page.getByRole('button', { name: 'Efetivar Entrada' }).click();

    await expect(page.getByText(/BAL-\d{4}-\d+/).first()).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText('Timeline do Atendido (Append-Only)')).toBeVisible();

    // Resolver com evidência
    await page.locator('#resolucao-despacho').fill('Demanda encaminhada e concluída no teste E2E.');
    await page.locator('#resolucao-evidencia').setInputFiles({
      name: 'evidencia.pdf',
      mimeType: 'application/pdf',
      buffer: PDF_MINIMO,
    });
    await expect(page.getByText('Evidência anexada')).toBeVisible();
    await page.getByRole('button', { name: 'Resolver Atendimento' }).click();
    await expect(page.getByText('Atendimento resolvido com sucesso.')).toBeVisible();

    // 4. Descartar segunda entrada
    const itemDescartar = page.getByText(marcadorDescartar).first();
    await expect(itemDescartar).toBeVisible({ timeout: 10_000 });
    await itemDescartar.click();
    await page.getByLabel('Motivo do descarte').fill('Solicitação duplicada em teste E2E');
    await page.getByRole('button', { name: 'Descartar', exact: true }).click();
    await expect(page.getByText('DESCARTADA').first()).toBeVisible({ timeout: 10_000 });

    // 5. Visualizar Grafo de Correlações
    await page.getByRole('button', { name: 'Grafo de Correlações' }).click();
    await expect(page.getByText(/Maria Silva E2E|Grafo de Correlações/i).first()).toBeVisible();

    expect(errosConsole, `Erros no console do navegador: ${errosConsole.join(' | ')}`).toEqual([]);
  });
});
