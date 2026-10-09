# Fonte e escopo das métricas

O projeto consulta a API GraphQL do GitHub e usa UTC, o mesmo fuso do calendário oficial. Os SVGs mostram apenas números agregados; nomes de repositórios privados e código-fonte nunca são publicados.

| Indicador | Cálculo | Escopo |
| --- | --- | --- |
| Contribuições do ano | `contributionCalendar.totalContributions` de 1º de janeiro até agora. | O cartão inferior mostra o acumulado histórico. Atividade privada é incluída quando a credencial opcional `PRIVATE_CONTRIBUTIONS_TOKEN` tem o escopo `read:user` e a opção de contribuições privadas está habilitada no GitHub. |
| Commits do ano | `totalCommitContributions` no mesmo intervalo. | Sem a credencial opcional, o rótulo diz “Commits visíveis”. Com `read:user`, o número pode incluir contribuições privadas, mas continua sem revelar os repositórios. |
| Repositórios do ano | `totalRepositoriesWithContributedCommits` no mesmo intervalo. | Conta repositórios distintos com commits, não repositórios com issues/PRs sem commits. O token `read:user` inclui contribuições privadas anonimizadas; sem ele, o cartão identifica o escopo público. |
| Repositórios próprios públicos | Soma de `stargazerCount`. | Conta estrelas recebidas, não estrelas dadas. |
| Pull requests e issues | Totais acessíveis pelo GraphQL para a conta. | O resultado pode não incluir itens privados fora do acesso da credencial. |
| Linguagens | Bytes de cada linguagem em repositórios próprios públicos. | Um token granular opcional acrescenta os repositórios privados selecionados e acessíveis. Forks, arquivos arquivados e repositórios excluídos são ignorados. Bytes não representam tempo ou experiência. |
| Sequência e atividade recente | Dias com `contributionCount > 0` no calendário; barras mostram os últimos 35 dias. | O calendário agrega tipos diferentes de contribuição. A sequência atual conta ontem quando hoje ainda está vazio. |
| Visitas | Serviço Komarev consultado pela função dinâmica quando ela recebe a imagem. | Não mede pessoas únicas. O proxy Camo do GitHub pode servir uma cópia em cache, então uma atualização por reload não é garantida. |

## Dados privados sem expor repositórios

Para incluir contribuições privadas agregadas, configure `PRIVATE_CONTRIBUTIONS_TOKEN` com um token clássico somente de leitura e o escopo `read:user`. Esse escopo permite ler os números de contribuição da conta; não concede escrita nem acesso ao conteúdo dos repositórios. Sem esse token, o cartão usa os dados públicos acessíveis ao `GITHUB_TOKEN`.

Para incluir linguagens de repositórios privados, use separadamente `PRIVATE_REPOSITORIES_TOKEN`: um token granular com **Metadata: read** apenas nos repositórios privados que você escolher. A API calcula totais de bytes; o projeto descarta nomes e identificadores antes de salvar o snapshot.

Contribuições privadas que o GitHub não disponibiliza como dados de repositório permanecem anônimas no calendário. O cartão nunca tenta deduzir commits privados subtraindo outros totais.

## Atualização do contador de visitas

O endpoint dinâmico consulta Komarev em cada requisição que chega à função Vercel. Ele pede revalidação ao Camo do GitHub e desativa o cache da Vercel, mas o proxy do GitHub ainda pode reaproveitar imagens. A Action atualiza a cópia estática uma vez por dia, como fallback. O CI não recebe eventos de reload feitos por leitores.
