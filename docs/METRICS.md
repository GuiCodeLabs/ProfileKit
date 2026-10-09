# De onde vêm os números

O projeto consulta a API GraphQL do GitHub em cada atualização. As datas e o calendário de contribuições usam **UTC**, como o gráfico oficial do GitHub. Todos os cartões usam a mesma coleta, para não misturar períodos nem escopos.

| Indicador | Cálculo | Limite |
| --- | --- | --- |
| Contribuições no card superior | `contributionCalendar.totalContributions` entre 1º de janeiro UTC e agora. | Inclui contribuições públicas e privadas anônimas quando o proprietário habilitou a exibição delas. Reinicia a cada janeiro. |
| Contribuições históricas | Soma de `contributionCalendar.totalContributions` desde a primeira atividade, usada no card inferior. | Não é sinônimo de commits; reúne diferentes tipos de atividade do calendário. |
| Commits visíveis | Soma de `totalCommitContributions` para os mesmos intervalos com o token automático da Action. | Representa commits acessíveis ao token; não tente inferir commits privados subtraindo um total do outro. |
| PRs e issues | Totais da conexão `user.pullRequests` e `user.issues` acessíveis ao token. | Não é um total verificável de PRs/issues privados ocultos. PRs privados podem contribuir ao total do calendário sem aparecer nesta linha. |
| Estrelas | Soma de `stargazerCount` dos repositórios públicos próprios, inclusive forks. | Estrelas recebidas, não estrelas dadas a terceiros. |
| Linguagens | Soma dos bytes das linguagens em repositórios próprios públicos. Com `PRIVATE_REPOSITORIES_TOKEN`, também inclui repositórios próprios privados aos quais o token tem acesso; forks, arquivados e nomes configurados são excluídos. | É uma proporção de bytes, não tempo de trabalho ou experiência. A API retorna somente totais por linguagem; os nomes dos repositórios e o código não são gravados no cartão. |
| Sequências | Dias com `contributionCount > 0` no calendário. A sequência atual inclui ontem quando hoje ainda está vazio. | O calendário inclui tipos diferentes de atividade; a maior sequência cobre o histórico disponível. |
| Visitas | Contagem do serviço Komarev quando a função recebe uma requisição para a imagem. | Não mede pessoas únicas. A resposta pede revalidação com `Cache-Control: no-cache`, mas o proxy Camo do GitHub controla o cache e pode reutilizar uma imagem. |

**Como ler os números:** o total do calendário reúne contribuições públicas e privadas anônimas, se a opção de privacidade estiver habilitada. A linha de commits conta somente os commits acessíveis ao token. Esses indicadores têm escopos diferentes, então não subtraia os valores para estimar “commits privados”.

## Por que meus commits privados não aparecem separadamente?

A opção **Private contributions** no GitHub mostra a quantidade de atividade privada sem revelar o repositório. O calendário consegue incluir esse agregado sem acesso aos repositórios. A distribuição de linguagens é diferente: para calculá-la em repositórios privados, o token opcional precisa de acesso de leitura aos metadados dos repositórios selecionados. Ele não precisa de permissão para alterar repositórios; nenhum nome de repositório nem trecho de código é publicado.

Verifique também as regras do próprio calendário: o email de autoria deve estar associado à conta, o commit precisa estar na branch padrão ou `gh-pages`, e contribuições de organizações com SSO podem exigir uma sessão ativa. Consulte a [documentação oficial do perfil](https://docs.github.com/en/account-and-profile/concepts/contributions-on-your-profile) e a [referência de contribuições](https://docs.github.com/en/account-and-profile/reference/profile-contributions-reference).
