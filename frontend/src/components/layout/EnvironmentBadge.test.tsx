import { afterEach, describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { EnvironmentBadge } from './EnvironmentBadge';

describe('EnvironmentBadge', () => {
  afterEach(() => {
    delete process.env.NEXT_PUBLIC_ENV_LABEL;
  });

  it('mostra o rótulo de protótipo quando o build recebe PROTOTIPO', () => {
    process.env.NEXT_PUBLIC_ENV_LABEL = 'PROTOTIPO';

    render(<EnvironmentBadge />);

    expect(screen.getByRole('status').textContent).toContain('PROTÓTIPO');
    expect(screen.getByRole('status').textContent).toContain('Regra 7.4.1');
  });

  it('não renderiza nada quando o build não define rótulo', () => {
    const { container } = render(<EnvironmentBadge />);

    expect(container.firstChild).toBeNull();
  });
});
