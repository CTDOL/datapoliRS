---
name: diagnostico-ambiente
description: Diagnosticar o ambiente real onde um sistema roda ou vai rodar — servidor, VPS, container — antes de propor qualquer mudança de infraestrutura, deploy, ou correção de produção. Use sempre que o pedido envolver investigar um servidor desconhecido ou pouco documentado, descobrir "o que está rodando nesse VPS", entender por que um serviço em produção está com problema, preparar um deploy novo num ambiente existente, revisar segurança básica de servidor, ou mapear certificados/domínios/cron antes de mexer neles. Também use quando o usuário mencionar acessar um servidor por SSH pela primeira vez, auditar infraestrutura, ou perguntar "o que tem instalado nesse servidor". Não é para configurar CI/CD do zero (isso é repo-bootstrap) nem para desenhar a arquitetura do código em si (isso é arquitetura-hexagonal) — é o passo anterior a ambos: entender o terreno antes de decidir o que fazer nele.
---

# Diagnóstico de ambiente de implantação

## Por que isso existe

`detect-stack.sh` (em `arquitetura-hexagonal`) responde "que código é esse". Esta skill responde uma pergunta diferente e anterior quando o alvo é um servidor: **"o que está de pé nesse ambiente, e o que depende disso continuar de pé".**

Servidor de produção que ninguém documentou é uma cena de investigação, não uma tela em branco. Cada serviço rodando, cada porta aberta, cada linha de cron existe porque alguém precisou dela — mesmo que ninguém mais lembre por quê. Antes de desligar, atualizar ou reconfigurar qualquer coisa, o objetivo é saber o que vai quebrar se você mexer.

## Postura

Você está lendo um sistema em produção, possivelmente antigo, possivelmente sem dono claro. Três coisas seguem disso:

- **Só leitura, sempre.** Nenhum comando desta skill altera o servidor. Se o usuário pedir para já corrigir algo durante o diagnóstico, termine o inventário primeiro — corrigir sem saber o que depende daquilo é como remover uma peça de um motor rodando sem saber o que ela segura.
- **Marque confiança, não afirme certeza.** Um script não sabe se uma porta aberta é intencional ou um esquecimento de 2019. Reporte o fato (porta 8080 aberta, rodando X) e deixe a pergunta "isso devia estar assim?" para o usuário, que conhece o histórico.
- **O ferramental de leitura não é neutro.** Comando de leitura não pesa nada, mas a infraestrutura que você traz para executá-lo pode pesar muito: servidor remoto de IDE, instalação de CLI, language server indexando o filesystem. Num servidor com pouca RAM, isso derruba a máquina — e aí a auditoria virou o incidente. Antes de acoplar qualquer ferramenta ao servidor, olhe a RAM disponível; abaixo de ~4GB, prefira SSH simples e comandos avulsos. E **nunca abra `/` como pasta de trabalho numa IDE remota**: o indexador tenta ler o servidor inteiro, incluindo backups e diretórios de usuários, e um processo só pode passar de 2GB. Abra sempre a pasta do projeto.

## Passo 0 — Preparar o terreno antes de tocar em qualquer coisa

**Primeiro, garanta um caminho alternativo de acesso.** Se o SSH travar no meio do trabalho — e num servidor sobrecarregado ele trava —, você precisa de outra porta de entrada: painel do provedor, terminal web do WHM/cPanel, console VNC, acesso serial. Descubra qual existe e **deixe aberto numa aba** antes de começar. Descobrir que não tem plano B no momento em que você já está trancado do lado de fora é uma das piores sensações da profissão, e é totalmente evitável.

**Segundo, pergunte se já existe documentação.** Nem todo servidor "sem dono claro" está de fato sem registro — às vezes o registro existe, só não está no próprio servidor. Pergunte: **existe alguma nota, matriz de portas, ADR, guia de deploy ou post-mortem de incidente sobre esse ambiente**, guardada em outro lugar (um cofre de notas, um repositório de documentação, um Notion)? Se existir, leia antes de interpretar os achados do script.

Isso importa porque esse tipo de documento costuma responder de cara o que o inventário só consegue marcar como "confiança média, confirmar" — por exemplo, uma matriz de portas já diz qual serviço é dono de qual porta e qual é o escopo de bind pretendido (loopback ou público), o que transforma "porta X aberta, não sei se é intencional" em "porta X deveria estar em 127.0.0.1 segundo a documentação, e está em 0.0.0.0 — isso é desvio confirmado, não suposição". Um post-mortem de incidente antigo também costuma revelar fragilidades operacionais (o que já derrubou esse ambiente antes) que o script não tem como enxergar sozinho.

Se não existir documentação, siga direto para o Passo 1 — só não invente a existência dela.

## Passo 1 — Rodar o inventário

```bash
scripts/audit-servidor.sh
```

Rode **dentro do servidor** (via SSH), não de fora. Ele é somente-leitura e cobre, nesta ordem: sistema e atualizações pendentes, serviços systemd ativos, containers Docker, portas escutando, firewall, servidor web e vhosts, certificados SSL e validade, cron/timers, usuários e configuração SSH.

Partes que exigem privilégio (firewall, algumas leituras de systemd) avisam quando não conseguem ler em vez de travar o script inteiro — rode com `sudo` se quiser o quadro completo, mas rode primeiro sem, para ver o que já é visível com o usuário atual (é o que um invasor ou um dev júnior também veria).

Se o servidor usa cPanel/WHM (comum em hospedagem compartilhada), o script pode não achar vhosts nem certificados nos caminhos padrão de Nginx/Apache/Let's Encrypt — cPanel guarda isso por conta, em outro lugar. Não trate "não encontrado" como "não existe": trate como "esses caminhos padrão não se aplicam aqui, confirme via painel WHM/AutoSSL quantos domínios e certificados realmente existem".

## Passo 2 — Ler o resultado como uma investigação, não como uma lista

Depois do script, olhe para quatro perguntas, na ordem:

1. **O que está exposto para fora que não devia estar?** Cruze "portas escutando em 0.0.0.0/::" com "firewall" e, se existir documentação do Passo 0, com o escopo de bind que ela declara para cada serviço. Um container ou app que deveria escutar só em `127.0.0.1` e aparece em `0.0.0.0` é o padrão de desvio mais comum em ambientes com proxy reverso (Apache/Nginx na frente, apps atrás) — e, quando há uma regra documentada dizendo isso, é achado de confiança alta, não "confirmar com o responsável".
2. **O que vai parar de funcionar sozinho, e quando?** Certificado vencendo em poucos dias, cron apontando para um script que não existe mais, timer systemd falhando — essas são bombas-relógio silenciosas, o script te entrega a data, mas cabe a você calcular a urgência.
3. **Quem consegue entrar, e como?** Login root por senha, chaves de gente que já saiu do projeto, sudo sem necessidade aparente — e não esqueça quem *além de humanos* tem acesso: agente de IA, automação de deploy, CI/CD com chave própria contam, e ficam de fora de uma auditoria que só pensa em "funcionários". Duas armadilhas específicas aqui:

   - **`authorized_keys` não é o único caminho.** Se o `sshd_config` tiver `TrustedUserCAKeys`, existe autenticação por certificado: quem tiver um certificado assinado por aquela CA entra sem constar em lugar nenhum do `authorized_keys`. Você pode limpar o arquivo inteiro e o acesso continuar aberto. Cheque `grep -riE "TrustedUserCAKeys|AuthorizedPrincipalsFile" /etc/ssh/sshd_config /etc/ssh/sshd_config.d/` e, se houver, veja de quem é a CA (`ssh-keygen -lf` no arquivo apontado) e quem está autorizado (`/etc/ssh/auth_principals/`).
   - **Chave listada não é chave usada.** O OpenSSH registra o fingerprint em cada login bem-sucedido, então o log responde o que a lista não responde: `grep -h "Accepted publickey" /var/log/secure* | awk '{print $NF}' | sort | uniq -c | sort -rn` (em Debian/Ubuntu, `/var/log/auth.log*`). Isso separa a chave que faz centenas de logins da que nunca foi usada. Cuidado com a conclusão: "sem uso" vale só para a janela de retenção do log — confirme até onde ele vai antes de afirmar qualquer coisa.

   Ao mexer em acesso, **desative antes de apagar**: comentar a linha com `#` no `authorized_keys` neutraliza a chave, mantém o registro do que foi feito, e reverter é apagar um caractere. Faça backup do arquivo, mantenha o canal alternativo do Passo 0 aberto, e teste uma conexão nova **antes** de fechar a sessão atual.
4. **Esse ambiente já foi derrubado por uma operação pesada antes?** Build de imagem, compilação de dependência nativa, migração grande, indexação — essas coisas competem por CPU/RAM com tudo que já está rodando, e em servidor sem recursos dedicados isso já matou serviço via OOM-killer em casos reais. Se houver post-mortem documentado (Passo 0), ele geralmente já virou regra ("nunca compilar no host", "sempre imagem pré-compilada") — leve essa regra para qualquer recomendação de deploy daqui pra frente.

   Quando a pergunta for "por que caiu", **o servidor guarda a resposta e quase ninguém procura**. Dois lugares:

   ```bash
   dmesg -T | grep -iE 'oom|killed process' | tail -20    # o kernel matou algo? qual processo, que tamanho
   sar -q -f /var/log/sa/sa$(date +%d)                     # carga minuto a minuto
   sar -r -f /var/log/sa/sa$(date +%d)                     # memória e swap ao longo do dia
   ```

   O `dmesg` diz **o que** morreu e com quanta memória. O `sar` (pacote `sysstat`, presente na maioria dos servidores) reconstrói **quando** a pressão começou e como evoluiu — permite cruzar o pico com o que estava sendo feito naquele minuto. Duas leituras que valem mais que qualquer suposição: `%commit` acima de 100% significa que o sistema prometeu mais memória do que RAM+swap comportam, e uma amostra do `sar` fora do horário regular indica que nem o coletor conseguiu rodar, ou seja, a máquina estava travada de verdade.

## Passo 3 — Perguntar o que o servidor não conta

O inventário mostra o que existe, não por quê. Nunca preencha essas lacunas com suposição — pergunte:

- Esse serviço rodando em produção, alguém ainda usa? (às vezes a resposta é "não sei", e isso já é informação)
- Essa porta aberta é intencional (API interna, painel de admin) ou sobrou de um teste?
- Existe outro servidor ou provedor cuidando de parte disso (CDN, balanceador, backup gerenciado) que este inventário não alcança porque roda fora da máquina?
- Há uma janela de manutenção, ou qualquer mudança aqui pode ser feita a qualquer hora?

A última pergunta decide o ritmo do resto do trabalho — sistema sem janela de manutenção definida pede mudança incremental e reversível, nunca um passo grande de uma vez.

## Passo 4 — Registrar o achado, não só relatar

O valor real deste diagnóstico não é a saída do script (isso qualquer um roda de novo). É a lista curta e legível do que importa, no mesmo espírito da Fase 2 de `analise-legado`:

```
ACHADOS DO AMBIENTE

A1. Nginx serve 3 domínios; certificado de app.exemplo.com vence em 9 dias.
    Confiança: alta — data lida direto do certificado.
    Ação: renovar antes do vencimento, confirmar se o renew automático
    do certbot está de fato agendado (ver cron/timers).

A2. Container do serviço X escutando em 0.0.0.0:8081, mas a matriz de
    portas documentada define bind estrito em 127.0.0.1 para todo
    container atrás do proxy reverso.
    Confiança: alta — não é suposição, é desvio confirmado contra
    regra escrita (ver Passo 0).
    Ação: corrigir o bind no docker-compose.yml para 127.0.0.1:8081:PORTA
    e validar que o proxy reverso (Apache/.htaccess) continua servindo
    o domínio normalmente antes de considerar resolvido.

A3. PermitRootLogin=yes no sshd_config.
    Confiança: alta — risco conhecido, sem ambiguidade.
    Ação: propor troca para acesso só por chave, senão vazio.
```

Assim como em `analise-legado`, separe **o que é risco real, já confirmado** (A2 e A3, porque há documentação ou config explícita sem ambiguidade) de **o que ainda precisa de confirmação humana** — normalmente qualquer achado sem documentação de apoio e sem certeza sobre quem usa aquilo. Não corrija o confirmado sem, mesmo assim, avisar antes: mudar bind de porta em produção sem janela de manutenção definida (ver Passo 3) ainda merece passo pequeno e reversível, não um "conserta e sobe".

## O que fazer com o resultado

- Se o próximo passo for corrigir algo: siga a ordem de risco crescente de `analise-legado` (segurança primeiro, depois o resto) — um servidor de produção pune erro de ordem mais rápido que um repositório de código.
- Se o próximo passo for propor infraestrutura nova (CI/CD, deploy automatizado) sobre esse ambiente: use `repo-bootstrap` a partir daqui, já sabendo o que existe, em vez de assumir um servidor limpo.
- Se aparecer regra de negócio embutida em algum script de deploy ou cron (não incomum): isso vira trabalho de `analise-legado`, não desta skill.

## Quando NÃO aplicar

- **Ambiente local de desenvolvimento.** Isto é para servidor real — de produção, homologação, ou qualquer máquina que hospeda algo que outras pessoas usam. Para "por que meu projeto não sobe aqui na minha máquina", o problema é outro (dependência, variável de ambiente, versão de runtime) e não precisa deste roteiro.
- **Servidor você mesmo provisionou há 5 minutos e documentou.** Se você já sabe o que está rodando porque acabou de configurar, rodar o inventário completo é redundante — só vale como registro de ponto de partida, se quiser um.
