# GitHub Profile Card

Cartões SVG originais para mostrar atividade, linguagens e sequência de contribuições de um perfil GitHub. Este repositório gera os cartões do [GuiCodeLabs](https://github.com/GuiCodeLabs) e pode ser adaptado para qualquer usuário.

<p align="center"><img src="profile/stats.svg" width="520" alt="Atividade no GitHub de Guilherme Beserra" /></p>
<p align="center"><img src="profile/languages.svg" width="520" alt="Linguagens dos repositórios públicos" /></p>

## O que os números significam

| Métrica | Fonte e escopo |
| --- | --- |
| Contribuições | Soma dos calendários anuais do GitHub. Inclui commits reconhecidos pelo calendário, PRs, issues e outras contribuições. Quando o usuário permite exibir atividades privadas, o calendário também pode mostrar suas **contagens anônimas**. |
| Commits públicos | `totalCommitContributions` por ano, visíveis para o token automático deste repositório. Não revela commits de repositórios privados. |
| Estrelas | Estrelas recebidas pelos repositórios **públicos próprios**, inclusive forks. |
| PRs e issues | Totais visíveis no perfil pela API do GitHub. |
| Linguagens | Bytes de código por linguagem informados pela API do GitHub nos repositórios públicos próprios; exclui forks, arquivados e os nomes em `exclude_repositories`. Não é uma medida de proficiência. |
| Sequências | Dias consecutivos com contribuições no calendário. A sequência atual admite hoje ainda vazio quando ontem teve atividade. |
| Visitas | Solicitações que chegam ao contador Komarev, não visitantes únicos. O GitHub usa um proxy/cache de imagens, por isso um reload não necessariamente gera outra solicitação. |

**Exemplo:** 413 contribuições e 141 commits públicos podem estar ambos corretos. Contribuições têm mais tipos de atividade e podem incluir contagens privadas anônimas. A diferença não indica 272 commits privados.

Os intervalos anuais usam o fuso em `profile-card.json`. Os cartões são SVGs próprios, sem reaproveitar arte ou código dos serviços de estatísticas anteriores.

## Usar no seu perfil

1. Crie sua cópia deste repositório, publique-a e edite `profile-card.json` com seu usuário, nome e fuso. Os repositórios listados em `exclude_repositories` saem **apenas** do cartão de linguagens.
2. Ative o GitHub Actions na cópia e permita que o workflow escreva os SVGs na branch padrão. O workflow usa o `GITHUB_TOKEN` automático e não pede PAT.
3. No README do perfil, use as imagens da **sua cópia**. Elas estão em `profile/stats.svg`, `profile/languages.svg` e `profile/rhythm.svg`.

```html
<p align="center">
  <img src="https://raw.githubusercontent.com/SEU_USUARIO/github-profile-card/main/profile/stats.svg" width="520" alt="Atividade no GitHub" />
  <img src="https://raw.githubusercontent.com/SEU_USUARIO/github-profile-card/main/profile/languages.svg" width="520" alt="Linguagens dos repositórios" />
  <img src="https://raw.githubusercontent.com/SEU_USUARIO/github-profile-card/main/profile/rhythm.svg" width="520" alt="Sequência de contribuições" />
</p>
```

Cada cartão ocupa sua própria linha no README; a largura máxima de 520 px permite leitura tanto no computador quanto no aplicativo móvel.

### Idioma

O README do GitHub não oferece ao SVG o idioma da pessoa que está vendo a página. Escolha o idioma alterando o nome do arquivo no Markdown:

| Idioma | Arquivos estáticos | Endpoint dinâmico |
| --- | --- | --- |
| Português | `stats.svg`, `languages.svg`, `rhythm.svg` | `locale=pt-BR` |
| English | `stats-en.svg`, `languages-en.svg`, `rhythm-en.svg` | `locale=en` |
| Español | `stats-es.svg`, `languages-es.svg`, `rhythm-es.svg` | `locale=es` |

O gerador detecta automaticamente **as linguagens de programação do usuário configurado**. O idioma da interface é uma escolha explícita do README.

## Atualizações e visitas

O workflow atualiza as métricas a cada 15 minutos, sujeito ao agendamento do GitHub. Só cria um commit quando os dados mudam. Uma execução diária consulta o contador de visitas e atualiza a cópia estática; essa consulta também é contada como acesso pelo serviço.

O arquivo `api/card.js` fornece a opção de **cartão dinâmico** para hospedar no Vercel. Ele usa o SVG público gerado pelo workflow, busca o número de visitas ao receber uma solicitação e envia `Cache-Control` de 60 segundos. Configure `PROFILE_REPOSITORY` como `SEU_USUARIO/github-profile-card` e `PROFILE_USER` como seu usuário no deploy. O SVG dinâmico pode ser usado assim:

```html
<img src="https://SEU-DEPLOY.vercel.app/api/card?type=stats&amp;locale=pt-BR" width="520" alt="Atividade no GitHub" />
```

O cache de imagens do GitHub pode segurar a atualização por mais tempo; **não é garantido um incremento por reload**. Para não inflar a contagem, remova qualquer pixel ou badge antigo do mesmo contador ao usar o endpoint dinâmico.

## Desenvolvimento

Python 3.11+ e Node.js 20+. Sem dependências externas ou serviços pagos para gerar os cartões estáticos.

```bash
python3 -m unittest discover -s tests -v
npm test
GITHUB_TOKEN=SEU_TOKEN_DE_LEITURA python3 scripts/generate_card.py --config profile-card.json
```

O comando local precisa de um token de leitura para a API GraphQL. Não inclua o token no repositório; no GitHub Actions ele é fornecido automaticamente. Use `--refresh-visits` somente se quiser consultar e incrementar o contador. Para prévia sem consultas à API, importe as funções de renderização com dados de exemplo.

## Ideias para contribuições

- Temas claro e escuro com cores configuráveis em `profile-card.json`.
- Testes visuais de acessibilidade e de leitura em telas pequenas.
- Exportação opcional para PNG e integração com outros perfis públicos.

Contribuições são bem-vindas. Veja a [licença MIT](LICENSE).
