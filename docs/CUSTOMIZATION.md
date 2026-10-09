# Personalização e diagnóstico

## Configurar outra conta

Edite `profile-card.json`:

```json
{
  "username": "SEU_USUARIO",
  "display_name": "Seu Nome",
  "exclude_repositories": ["SEU_USUARIO", "github-profile-card"]
}
```

O filtro `exclude_repositories` afeta **só as linguagens**. O total de contribuições consulta o calendário da conta, inclusive quando os repositórios pertencem a uma organização. As datas do GitHub são UTC, portanto não é preciso configurar fuso horário.

## Incluir contribuições privadas agregadas

O cartão conta commits e repositórios distintos com commits no ano. Para incluir atividade privada agregada, crie um token clássico com **somente** o escopo `read:user`, escolha uma validade curta e salve-o como o secret `PRIVATE_CONTRIBUTIONS_TOKEN` em **Settings → Secrets and variables → Actions**. Esse escopo permite consultar os dados de contribuição da conta, sem permissão para escrever ou acessar o conteúdo dos repositórios. Não acrescente `repo`, `workflow` nem permissões de escrita.

Ative também **Private contributions** nas configurações de perfil do GitHub. Sem o secret, o cartão sinaliza que commits e repositórios refletem apenas os dados públicos acessíveis ao workflow. O cartão publica contagens agregadas e nunca nomes de repositórios privados.

## Incluir linguagens de repositórios privados

Os cards de linguagens e estrelas incluem os repositórios próprios públicos por padrão. Para acrescentar repositórios privados que você possui ou acessa, crie um **fine-grained personal access token** na sua conta GitHub, selecione somente os repositórios privados que quer incluir e conceda apenas a permissão de repositório **Metadata: read**. Não conceda `Contents`, escrita ou acesso a repositórios que não devam entrar no cálculo.

No repositório público do cartão, abra **Settings → Secrets and variables → Actions → New repository secret**. Use o nome `PRIVATE_REPOSITORIES_TOKEN` e cole o token no campo de valor. O workflow usa essa credencial somente para consultar os totais de linguagens. Os SVGs publicados contêm nomes de linguagens e totais de bytes, sem nomes dos repositórios ou conteúdo de arquivos. Se o secret não estiver configurado, o cartão continua calculando apenas os repositórios públicos e informa isso no subtítulo.

O token precisa ter acesso a cada repositório privado que deseja incluir. Se um repositório pertencer a uma organização, a política da organização ou SSO pode exigir aprovação adicional.

## Idioma dos cartões

| Idioma | Estatísticas | Linguagens | Ritmo |
| --- | --- | --- | --- |
| Português | `stats.svg` | `languages.svg` | `rhythm.svg` / `rhythm-mobile.svg` |
| English | `stats-en.svg` | `languages-en.svg` | `rhythm-en.svg` / `rhythm-mobile-en.svg` |
| Español | `stats-es.svg` | `languages-es.svg` | `rhythm-es.svg` / `rhythm-mobile-es.svg` |

Para traduzir outro idioma, acrescente rótulos em `LABELS`, uma extensão em `output_name` e o idioma na lista de `SUPPORTED_LOCALES` em `scripts/generate_card.py`. O GitHub não envia o idioma do visitante para uma imagem SVG inserida no README; a escolha é feita no gerador.

O [gerador web de README](https://guicodelabs-profile-card.vercel.app) detecta o idioma do navegador e permite escolher português, inglês ou espanhol. Ele só gera o snippet: nenhum token é pedido ou enviado pelo navegador.

## Badge de visitas no README

O contador de visitas fica separado dos cartões. Para exibi-lo, coloque um badge Komarev junto aos seus links de contato:

```html
<img src="https://komarev.com/ghpvc/?username=SEU_USUARIO&amp;style=flat-square&amp;label=visitas%20do%20perfil" alt="Visitas do perfil" />
```

O serviço atualiza o contador quando recebe requisições da imagem. O proxy de imagens do GitHub pode guardar uma cópia, então não há garantia de atualização em cada visualização ou recarga.

## Prévia local

Depois que a Action criar `profile/data.json`, gere variantes de teste **sem chamar a API** e abra `preview/stats.svg` no navegador:

```bash
python3 scripts/preview.py
```

Use `--data CAMINHO` para um snapshot de outra conta e `--output-dir CAMINHO` para outra pasta. Os SVGs resultantes podem ser convertidos com Inkscape. Para consultar números reais novamente:

```bash
GITHUB_TOKEN=SEU_TOKEN_DE_LEITURA PRIVATE_REPOSITORIES_TOKEN=TOKEN_OPCIONAL PRIVATE_CONTRIBUTIONS_TOKEN=TOKEN_READ_USER python3 scripts/generate_card.py
```

Os tokens são usados apenas no processo local; jamais grave seus valores no repositório. No workflow, o GitHub fornece um token temporário para os dados públicos.

## Ajustes de aparência

As cores estão em `PALETTE` e `svg_shell`; posições e tamanhos ficam em `render_stats`, `render_languages` e `render_rhythm`. Preserve a altura e a largura do `viewBox` ao alterar dimensões e gere novamente todas as variantes de idioma. A nota anual é uma faixa visual própria, descrita em [definições de métricas](METRICS.md#faixas-da-nota-anual), não uma nota oficial do GitHub.

A disposição no perfil é controlada pelo HTML do README: imagens superiores com `width="410"` cabem juntas em telas largas e quebram de linha em telas estreitas. O `<picture>` alterna para uma versão compacta do cartão inferior até 600 px.

## Quando algo não atualiza

- Se o calendário mostrar zero para uma atividade recente, confira as [regras de contribuições do GitHub](https://docs.github.com/en/account-and-profile/reference/profile-contributions-reference), email de autoria, branch e visibilidade de contribuições privadas.
- Se os números não mudarem, confira a última execução de Actions. Agendamentos podem atrasar e cada atualização depende de um novo commit quando os dados mudam.
- Se a imagem estiver antiga mesmo após um commit, o GitHub pode servir uma cópia em cache. Abra o SVG bruto do repositório para comparar.
- Se o badge de visitas não aumentar, aguarde a atualização do serviço e lembre que o proxy do GitHub pode reutilizar a imagem em cache.
- Se uma linguagem estiver desproporcional, veja quais repositórios e arquivos ocupam mais bytes. Use `exclude_repositories` apenas para omitir repositórios irrelevantes da amostra.
