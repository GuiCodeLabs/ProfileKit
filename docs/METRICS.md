# Fonte e escopo das métricas

O projeto consulta a API GraphQL do GitHub e usa datas UTC, como o calendário oficial. Os cartões publicam somente totais agregados; nomes de repositórios privados e código-fonte não são incluídos.

| Indicador | Cálculo | Escopo |
| --- | --- | --- |
| Contribuições do ano | `contributionCalendar.totalContributions` de 1º de janeiro até hoje. | O calendário agrega commits, PRs, issues e revisões. Um token opcional `read:user` pode incluir as contribuições privadas que o GitHub disponibiliza. |
| Commits do ano | `totalCommitContributions` no ano corrente. | Sem o token opcional, o cartão informa que os commits são visíveis/publicamente acessíveis. |
| Repositórios do ano | `totalRepositoriesWithContributedCommits`. | Conta repositórios distintos com commits no ano. Não conta repositórios com apenas issues ou PRs. O escopo privado depende do token `read:user`. |
| Estrelas | Soma de `stargazerCount` dos repositórios próprios consultados. | O token granular permite incluir repositórios privados selecionados. Conta estrelas recebidas, não estrelas dadas. |
| Pull requests e issues | Totais acessíveis pelo GraphQL para a conta. | O GitHub pode limitar itens privados não acessíveis à credencial usada. |
| Linguagens | Bytes de cada linguagem nos repositórios próprios. | Público por padrão. Um token granular opcional acrescenta repositórios privados selecionados. Forks, arquivos arquivados e nomes excluídos são ignorados. Bytes não representam tempo ou experiência. |
| Sequências | Dias consecutivos com `contributionCount > 0`. | A sequência atual considera ontem quando hoje ainda não tem atividade. |
| Mapa recente | Contribuições diárias nos últimos 35 dias, em quadrados de intensidade crescente. | O mapa acompanha o calendário de contribuições do GitHub. |
| Nota anual | Faixa visual própria calculada a partir do total de contribuições no ano. | Não é uma nota ou classificação oficial do GitHub. Os limites ficam listados abaixo. |
| Visitas | Badge Komarev independente, inserido no README. | É um contador de requisições, não de pessoas únicas. O cache de imagens do GitHub pode atrasar a atualização. |

## Faixas da nota anual

| Contribuições no ano | Nota |
| ---: | :--- |
| 0–49 | D |
| 50–99 | C |
| 100–199 | B− |
| 200–399 | B |
| 400–599 | B+ |
| 600–999 | A− |
| 1.000–1.499 | A |
| 1.500–2.499 | A+ |
| 2.500 ou mais | S |

## Dados privados sem expor repositórios

Para incluir contribuições privadas agregadas, configure `PRIVATE_CONTRIBUTIONS_TOKEN` com um token clássico somente de leitura e o escopo `read:user`. Esse escopo permite ler os números de contribuição da conta; não concede escrita nem acesso ao conteúdo dos repositórios. Também habilite **Private contributions** nas configurações do perfil GitHub.

Para incluir linguagens e estrelas de repositórios privados, use `PRIVATE_REPOSITORIES_TOKEN`: um token granular com **Metadata: read** apenas nos repositórios privados que você escolher. A API calcula totais e descarta nomes e identificadores antes de salvar o snapshot.

Contribuições privadas que o GitHub não disponibiliza como dados de repositório permanecem anônimas no calendário. O cartão nunca tenta deduzir commits privados subtraindo outros totais.

## Atualização

Uma GitHub Action consulta as métricas uma vez por dia e atualiza os arquivos na branch `stats-output` quando os dados mudam. Commits dessa rotina são autoria de `github-actions[bot]`; são registros gerados pela automação. A Action não se passa pela pessoa proprietária do perfil.

O badge Komarev conta requisições que chegam ao serviço. Como o GitHub pode servir a imagem por cache, a atualização pode não acontecer em todo acesso ou recarga do perfil. A Action de métricas não recebe eventos de visualização.
