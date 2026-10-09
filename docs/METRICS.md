# De onde vêm os números

O projeto consulta a API GraphQL do GitHub em cada atualização. As datas e o calendário de contribuições usam **UTC**, como o gráfico oficial do GitHub. Todos os cartões usam a mesma coleta, para não misturar períodos nem escopos.

| Indicador | Cálculo | Limite |
| --- | --- | --- |
| Total de contribuições | Soma de `contributionCalendar.totalContributions` para cada ano desde a primeira atividade. | Inclui as contagens privadas anônimas quando o proprietário escolheu compartilhá-las; não é sinônimo de commits. |
| Ano atual | Total do calendário entre 1º de janeiro UTC e agora. | Reinicia a cada janeiro. |
| Privadas anônimas | Soma de `restrictedContributionsCount` por ano. | Atividades inacessíveis ao leitor, agregadas. A API não fornece seus tipos nem nomes dos repositórios. |
| Commits visíveis | Soma de `totalCommitContributions` para os mesmos intervalos com o token automático da Action. | Representa commits acessíveis ao token; não tente inferir commits privados subtraindo um total do outro. |
| PRs e issues | Totais da conexão `user.pullRequests` e `user.issues` acessíveis ao token. | Não é um total verificável de PRs/issues privados ocultos. PRs privados podem contribuir ao total do calendário sem aparecer nesta linha. |
| Estrelas | Soma de `stargazerCount` dos repositórios públicos próprios, inclusive forks. | Estrelas recebidas, não estrelas dadas a terceiros. |
| Linguagens | Soma dos bytes das linguagens dos repositórios públicos próprios, excluindo forks, arquivados e nomes configurados. | É uma proporção de bytes, não tempo de trabalho ou experiência. |
| Sequências | Dias com `contributionCount > 0` no calendário. A sequência atual inclui ontem quando hoje ainda está vazio. | O calendário inclui tipos diferentes de atividade; a maior sequência cobre o histórico disponível. |
| Visitas | Contagem do serviço Komarev quando a função recebe uma requisição para a imagem. | Não mede pessoas únicas. A resposta pede revalidação com `Cache-Control: no-cache`, mas o proxy Camo do GitHub controla o cache e pode reutilizar uma imagem. |

**Como ler os números:** o total do calendário reúne diferentes tipos de contribuição; a linha privada é um agregado de atividade sem detalhes; e a linha de commits conta somente os commits acessíveis ao token. Esses indicadores têm escopos diferentes, então não some nem subtraia os valores para estimar “commits privados”.

## Por que meus commits privados não aparecem separadamente?

A opção **Private contributions** no GitHub mostra a quantidade de atividade privada sem revelar o repositório. Ela não transforma as atividades privadas em detalhes públicos da API. Este projeto usa o token automático da Action, restrito ao repositório; não precisa de acesso aos seus outros repositórios. Para contabilizar detalhes de cada repositório privado seria necessário conceder acesso adicional a eles, o que não faz parte desta implementação.

Verifique também as regras do próprio calendário: o email de autoria deve estar associado à conta, o commit precisa estar na branch padrão ou `gh-pages`, e contribuições de organizações com SSO podem exigir uma sessão ativa. Consulte a [documentação oficial do perfil](https://docs.github.com/en/account-and-profile/concepts/contributions-on-your-profile) e a [referência de contribuições](https://docs.github.com/en/account-and-profile/reference/profile-contributions-reference).
