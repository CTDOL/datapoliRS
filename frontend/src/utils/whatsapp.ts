/** Monta o link do WhatsApp Web/App (wa.me) a partir de um telefone BR em qualquer formato. */
export function buildWhatsappLink(nrTelefone: string): string | null {
  const digits = nrTelefone.replace(/\D/g, '');
  if (digits.length < 10) return null; // DDD + número, no mínimo
  const comCodigoPais = digits.startsWith('55') ? digits : `55${digits}`;
  return `https://wa.me/${comCodigoPais}`;
}
