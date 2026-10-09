# Cartão de estatísticas do GuiCodeLabs

Gerador aberto do [cartão do perfil de Guilherme Beserra](https://github.com/GuiCodeLabs). Um único SVG reúne estrelas, commits públicos de todo o período e do ano atual, pull requests, issues e visitas.

![Cartão de estatísticas](profile/stats.svg)

## Como funciona

- O workflow `.github/workflows/update-card.yml` atualiza o SVG diariamente e também pode ser executado manualmente.
- O script consulta a API GraphQL do GitHub com o `GITHUB_TOKEN` automático e limitado a este repositório. Ele soma os commits públicos de cada ano em que houve contribuições e separa o ano atual.
- A contagem de visitas vem do [GitHub Profile Views Counter](https://github.com/antonkomarev/github-profile-views-counter). O perfil inclui o pixel desse serviço para que as visitas continuem sendo registradas; o SVG apresenta o último valor coletado pelo workflow.
- O cartão **não** acessa repositórios privados nem pede um personal access token. Contribuições privadas podem aparecer anonimamente no calendário nativo do GitHub, mas não são somadas aos números de commits do cartão.

Para usar no README de um perfil GitHub:

```html
<img src="https://raw.githubusercontent.com/GuiCodeLabs/github-profile-card/main/profile/stats.svg" alt="Estatísticas do GitHub de Guilherme Beserra" />
```

## Desenvolvimento

Requer Python 3.11 ou posterior; só usa a biblioteca padrão.

```bash
python3 -m unittest discover -s tests
GITHUB_TOKEN=... python3 scripts/generate_card.py
```

Para executar localmente, use um token temporário somente com acesso de leitura a dados públicos. O workflow usa apenas `${{ github.token }}` e não precisa de segredo adicional.

Licença: [MIT](LICENSE).
