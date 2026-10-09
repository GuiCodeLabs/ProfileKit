# GitHub Profile Card

[English](README.en.md) · [Licença MIT](LICENSE) · [Abrir o gerador web](https://guicodelabs-profile-card.vercel.app)

Cartões SVG e um gerador web para montar um README de perfil do GitHub. O projeto oferece três cartões próprios — **status, linguagens e ritmo** — em português, inglês e espanhol. O gerador ajuda a configurar o snippet; as métricas reais são coletadas pela Action na cópia de cada usuário. Nenhum token é digitado no site.

Este repositório alimenta o [perfil de Guilherme Beserra](https://github.com/GuiCodeLabs). O visual usa cartões escuros com ícones lineares e números alinhados, inspirados em padrões de leitura rápida comuns em cartões de perfil; o código, os SVGs e os ícones são deste projeto.

<p align="center">
  <img src="profile/stats.svg" width="410" alt="Status do GitHub de GuiCodeLabs" />
  <img src="profile/languages.svg" width="410" alt="Linguagens dos repositórios acessíveis configurados" />
</p>
<p align="center">
  <picture>
    <source media="(max-width: 600px)" srcset="profile/rhythm-mobile.svg" />
    <img src="profile/rhythm.svg" width="840" alt="Ritmo de contribuições" />
  </picture>
</p>

## O que aparece

- **Status do GitHub:** estrelas recebidas, commits no ano, repositórios com commits no ano, PRs, issues, contribuições no ano e visitas ao perfil.
- **Linguagens:** bytes de código dos repositórios próprios públicos; um token granular opcional acrescenta repositórios privados acessíveis selecionados.
- **Ritmo:** contribuições de todo o período, sequência atual, maior sequência e atividade diária nas últimas cinco semanas.
- **Três idiomas e layout responsivo:** cartões lado a lado em telas largas, empilhados em telas estreitas e versão compacta do ritmo para celular.

[Definições e limitações das métricas](docs/METRICS.md) · [Configuração e solução de problemas](docs/CUSTOMIZATION.md) · [Como contribuir](CONTRIBUTING.md)

## Usar no seu perfil

1. Faça uma cópia pública deste repositório. Edite [`profile-card.json`](profile-card.json) com seu login, nome e repositórios a excluir da análise de linguagens.
2. Ative GitHub Actions e permita que o workflow escreva na branch principal. Por padrão, ele calcula o escopo público. Para incluir contagens privadas agregadas, configure `PRIVATE_CONTRIBUTIONS_TOKEN` com um token clássico somente de leitura e escopo `read:user`. Para acrescentar linguagens privadas, configure separadamente `PRIVATE_REPOSITORIES_TOKEN` com um token granular e **Metadata: read** nos repositórios escolhidos. Nenhum deles precisa de acesso de escrita ou conteúdo; veja o [guia de permissões](docs/CUSTOMIZATION.md).
3. Cole o trecho gerado pelo [gerador web](https://guicodelabs-profile-card.vercel.app) no README do seu perfil. Também é possível usar diretamente os caminhos abaixo, substituindo `SEU_USUARIO`:

```html
<p align="center">
  <img src="https://raw.githubusercontent.com/SEU_USUARIO/github-profile-card/main/profile/stats.svg" width="410" alt="Status do GitHub" />
  <img src="https://raw.githubusercontent.com/SEU_USUARIO/github-profile-card/main/profile/languages.svg" width="410" alt="Linguagens dos repositórios" />
</p>
<p align="center">
  <picture>
    <source media="(max-width: 600px)" srcset="https://raw.githubusercontent.com/SEU_USUARIO/github-profile-card/main/profile/rhythm-mobile.svg" />
    <img src="https://raw.githubusercontent.com/SEU_USUARIO/github-profile-card/main/profile/rhythm.svg" width="840" alt="Ritmo de contribuições" />
  </picture>
</p>
```

O primeiro cartão pode usar o [endpoint dinâmico](docs/CUSTOMIZATION.md#visitas-dentro-do-cartão) para buscar visitas quando a imagem for solicitada. A revalidação por reload não é garantida porque o proxy do GitHub pode reaproveitar uma cópia.

## Atualizações, privacidade e autoria

GitHub Actions testa as alterações e atualiza os dados a cada 15 minutos (o agendador pode atrasar). O workflow grava um commit como `github-actions[bot]` somente quando algum SVG ou dado realmente muda; esses commits representam a manutenção automática das imagens. Commits de código e documentação são feitos por pessoas em branches e PRs. O workflow não tenta atribuir atualizações automáticas à conta de uma pessoa.

O endpoint Vercel consulta o contador de visitas quando uma requisição chega à função e pede revalidação ao proxy de imagens Camo. Uma Action não recebe os reloads feitos pelos leitores; por isso, CI não consegue contar cada visualização. A cópia estática é renovada diariamente como fallback.

## Desenvolvimento

Python 3.11+ e Node.js 20+. O gerador usa apenas a biblioteca padrão do Python.

```bash
python3 -m unittest discover -s tests -v
npm test
GITHUB_TOKEN=SEU_TOKEN_DE_LEITURA python3 scripts/generate_card.py
```

Os secrets são opcionais e só são necessários para os dados privados descritos acima. Não inclua tokens em commits. Para gerar uma prévia sem consultar APIs, veja [Prévia local](docs/CUSTOMIZATION.md#prévia-local).
