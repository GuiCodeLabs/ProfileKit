import { buildReadmeSnippet, detectLocale, validateOptions } from "./generator.js";

const TRANSLATIONS = {
  "pt-BR": {
    navBuilder: "Gerador", navGuide: "Como usar", navAbout: "Sobre", languageLabel: "Idioma",
    eyebrow: "CARTÕES OPEN SOURCE PARA GITHUB", heroTitle: "Seu trabalho merece<br /><span>um perfil à altura.</span>",
    heroDescription: "Monte um README que mostra sua atividade, suas linguagens e seu ritmo em cartões feitos para o seu perfil.",
    privacyLine: "Sem login e sem tokens no navegador.", dailyLine: "Métricas atualizadas diariamente.", openSource: "Ver no GitHub",
    stepConfigure: "PERSONALIZE", formTitle: "Seu README", usernameLabel: "Usuário do GitHub",
    usernameHint: "Seu nome de usuário, como aparece no GitHub.", repoLabel: "Repositório dos cartões", formatLabel: "Formato",
    htmlOption: "HTML responsivo", markdownOption: "Markdown simples", cardsLegend: "Escolha seus cartões",
    statsOption: "Status do GitHub", statsHint: "Resumo do ano, projetos e conquistas.",
    languagesOption: "Linguagens", languagesHint: "Código dos repositórios acessíveis.",
    rhythmOption: "Ritmo de contribuições", rhythmHint: "Sequência, mapa recente e marcos.",
    setupNote: "Dados privados são opcionais e configurados nas GitHub Actions do seu repositório. Eles nunca passam pelo site.",
    permissionsLink: "Ver guia", generateButton: "Gerar snippet", stepPreview: "PRÉVIA",
    previewTitle: "Uma ideia do resultado", previewSample: "EXEMPLO", previewStats: "Status do GitHub",
    metricStars: "Estrelas", metricCommits: "Commits · ano", metricRepos: "Repositórios · ano",
    metricPulls: "Pull requests", metricIssues: "Issues", metricContributions: "Contribuições · ano", previewLanguages: "Linguagens mais usadas",
    previewLanguageNote: "Amostra de distribuição por bytes de código.", previewRhythm: "Ritmo de contribuições",
    metricDays: "dias", metricCurrent: "Sequência atual", metricBest: "Recorde: 6 dias",
    metricLanguages: "Linguagens", metricYearRepos: "Repos. no ano",
    previewDisclaimer: "Os números são só um exemplo. Depois de configurar sua cópia, a Action usa suas métricas.",
    stepOutput: "COPIE", outputTitle: "Cole no README do perfil", copyButton: "Copiar código",
    errorUsername: "Informe um nome de usuário GitHub válido.", errorRepository: "Informe um nome de repositório válido.",
    errorCards: "Selecione pelo menos um cartão.", copied: "Código copiado para a área de transferência.",
    copyFailed: "Não consegui copiar automaticamente. Selecione e copie o código acima.",
    howEyebrow: "DO REPOSITÓRIO AO PERFIL", howTitle: "Pronto em três passos simples.",
    howForkTitle: "Crie sua cópia", howForkText: "Faça um fork público para gerar seus cartões e controlar sua configuração.",
    forkLink: "Abrir repositório", howConfigureTitle: "Ative a atualização",
    howConfigureText: "A GitHub Action atualiza os cartões diariamente. Tokens privados são opcionais.",
    howPasteTitle: "Adicione ao seu perfil", howPasteText: "Cole o código no README do repositório que tem o mesmo nome da sua conta.",
    profileHelp: "Ajuda do GitHub", aboutEyebrow: "FEITO EM OPEN SOURCE",
    aboutTitle: "Um projeto pessoal,<br /><span>aberto para todo mundo.</span>",
    aboutText: "Criei o ProfileKit para deixar simples montar cartões de perfil claros e personalizáveis. Você pode usar, adaptar e ajudar a melhorar.",
    creatorGithub: "GitHub do criador ↗", creatorLinkedin: "LinkedIn ↗", contributeTitle: "Quer contribuir?",
    contributeText: "Sugestões, correções e novas ideias são bem-vindas.", contributeLink: "Abrir uma issue",
    footerText: "Feito para mostrar o que você constrói.", licenseLink: "Licença MIT",
  },
  en: {
    navBuilder: "Builder", navGuide: "How to use", navAbout: "About", languageLabel: "Language",
    eyebrow: "OPEN SOURCE GITHUB PROFILE CARDS", heroTitle: "Your work deserves<br /><span>a profile to match.</span>",
    heroDescription: "Build a README that shows your activity, languages and rhythm with cards made for your profile.",
    privacyLine: "No sign-in and no browser tokens.", dailyLine: "Metrics refresh daily.", openSource: "View on GitHub",
    stepConfigure: "CUSTOMIZE", formTitle: "Your README", usernameLabel: "GitHub username",
    usernameHint: "Your username as it appears on GitHub.", repoLabel: "Cards repository", formatLabel: "Format",
    htmlOption: "Responsive HTML", markdownOption: "Simple Markdown", cardsLegend: "Choose your cards",
    statsOption: "GitHub status", statsHint: "Year summary, projects and achievements.",
    languagesOption: "Languages", languagesHint: "Code from accessible repositories.",
    rhythmOption: "Contribution rhythm", rhythmHint: "Streak, recent map and milestones.",
    setupNote: "Private data is optional and configured in your repository's GitHub Actions. It never passes through this site.",
    permissionsLink: "Read the guide", generateButton: "Generate snippet", stepPreview: "PREVIEW",
    previewTitle: "A look at the result", previewSample: "SAMPLE", previewStats: "GitHub status",
    metricStars: "Stars", metricCommits: "Commits · year", metricRepos: "Repositories · year",
    metricPulls: "Pull requests", metricIssues: "Issues", metricContributions: "Contributions · year", previewLanguages: "Most used languages",
    previewLanguageNote: "Example distribution by code bytes.", previewRhythm: "Contribution rhythm",
    metricDays: "days", metricCurrent: "Current streak", metricBest: "Record: 6 days",
    metricLanguages: "Languages", metricYearRepos: "Repos · year",
    previewDisclaimer: "These numbers are examples. After setup, your copy's Action uses your metrics.",
    stepOutput: "COPY", outputTitle: "Paste into your profile README", copyButton: "Copy code",
    errorUsername: "Enter a valid GitHub username.", errorRepository: "Enter a valid repository name.",
    errorCards: "Select at least one card.", copied: "Code copied to the clipboard.",
    copyFailed: "Automatic copy failed. Select and copy the code above.",
    howEyebrow: "FROM REPOSITORY TO PROFILE", howTitle: "Ready in three simple steps.",
    howForkTitle: "Create your copy", howForkText: "Fork this public repository to generate your cards and manage your setup.",
    forkLink: "Open repository", howConfigureTitle: "Enable updates",
    howConfigureText: "A GitHub Action refreshes the cards daily. Private tokens are optional.",
    howPasteTitle: "Add it to your profile", howPasteText: "Paste the code into the README in the repository with your GitHub username.",
    profileHelp: "GitHub help", aboutEyebrow: "MADE IN OPEN SOURCE",
    aboutTitle: "A personal project,<br /><span>open for everyone.</span>",
    aboutText: "I created ProfileKit to make clear, customizable profile cards easy to build. Use it, adapt it and help make it better.",
    creatorGithub: "Creator on GitHub ↗", creatorLinkedin: "LinkedIn ↗", contributeTitle: "Want to contribute?",
    contributeText: "Suggestions, fixes and new ideas are welcome.", contributeLink: "Open an issue",
    footerText: "Made to show what you build.", licenseLink: "MIT License",
  },
  es: {
    navBuilder: "Generador", navGuide: "Cómo usar", navAbout: "Acerca de", languageLabel: "Idioma",
    eyebrow: "TARJETAS OPEN SOURCE PARA GITHUB", heroTitle: "Tu trabajo merece<br /><span>un perfil a la altura.</span>",
    heroDescription: "Crea un README que muestre tu actividad, tus lenguajes y tu ritmo con tarjetas hechas para tu perfil.",
    privacyLine: "Sin iniciar sesión y sin tokens en el navegador.", dailyLine: "Métricas actualizadas a diario.", openSource: "Ver en GitHub",
    stepConfigure: "PERSONALIZA", formTitle: "Tu README", usernameLabel: "Usuario de GitHub",
    usernameHint: "Tu nombre de usuario tal como aparece en GitHub.", repoLabel: "Repositorio de tarjetas", formatLabel: "Formato",
    htmlOption: "HTML adaptable", markdownOption: "Markdown simple", cardsLegend: "Elige tus tarjetas",
    statsOption: "Estado de GitHub", statsHint: "Resumen anual, proyectos y logros.",
    languagesOption: "Lenguajes", languagesHint: "Código de los repositorios accesibles.",
    rhythmOption: "Ritmo de contribuciones", rhythmHint: "Racha, mapa reciente y metas.",
    setupNote: "Los datos privados son opcionales y se configuran en GitHub Actions de tu repositorio. Nunca pasan por este sitio.",
    permissionsLink: "Ver guía", generateButton: "Generar snippet", stepPreview: "VISTA PREVIA",
    previewTitle: "Así podría quedar", previewSample: "EJEMPLO", previewStats: "Estado de GitHub",
    metricStars: "Estrellas", metricCommits: "Commits · año", metricRepos: "Repositorios · año",
    metricPulls: "Pull requests", metricIssues: "Incidencias", metricContributions: "Contribuciones · año", previewLanguages: "Lenguajes más usados",
    previewLanguageNote: "Ejemplo de distribución por bytes de código.", previewRhythm: "Ritmo de contribuciones",
    metricDays: "días", metricCurrent: "Racha actual", metricBest: "Récord: 6 días",
    metricLanguages: "Lenguajes", metricYearRepos: "Repos. del año",
    previewDisclaimer: "Son números de ejemplo. Tras configurar tu copia, la Action usará tus métricas.",
    stepOutput: "COPIA", outputTitle: "Pega en el README de tu perfil", copyButton: "Copiar código",
    errorUsername: "Escribe un usuario válido de GitHub.", errorRepository: "Escribe un repositorio válido.",
    errorCards: "Selecciona al menos una tarjeta.", copied: "Código copiado al portapapeles.",
    copyFailed: "No se pudo copiar automáticamente. Selecciona y copia el código de arriba.",
    howEyebrow: "DEL REPOSITORIO AL PERFIL", howTitle: "Listo en tres pasos sencillos.",
    howForkTitle: "Crea tu copia", howForkText: "Haz un fork público para generar tus tarjetas y controlar la configuración.",
    forkLink: "Abrir repositorio", howConfigureTitle: "Activa las actualizaciones",
    howConfigureText: "Una GitHub Action actualiza las tarjetas a diario. Los tokens privados son opcionales.",
    howPasteTitle: "Añádelo a tu perfil", howPasteText: "Pega el código en el README del repositorio con el nombre de tu cuenta.",
    profileHelp: "Ayuda de GitHub", aboutEyebrow: "HECHO EN OPEN SOURCE",
    aboutTitle: "Un proyecto personal,<br /><span>abierto para todos.</span>",
    aboutText: "Creé ProfileKit para facilitar tarjetas de perfil claras y personalizables. Puedes usarlo, adaptarlo y ayudar a mejorarlo.",
    creatorGithub: "Creador en GitHub ↗", creatorLinkedin: "LinkedIn ↗", contributeTitle: "¿Quieres contribuir?",
    contributeText: "Se agradecen sugerencias, correcciones e ideas nuevas.", contributeLink: "Abrir una issue",
    footerText: "Hecho para mostrar lo que construyes.", licenseLink: "Licencia MIT",
  },
};

const $ = selector => document.querySelector(selector);
const localeSelect = $("#locale");
const snippetElement = $("#snippet");
const errorElement = $("#formError");
const copyStatus = $("#copyStatus");
const HTML_TRANSLATIONS = new Set(["heroTitle", "aboutTitle"]);

function readOptions() {
  return {
    username: $("#username").value,
    repository: $("#repository").value,
    locale: localeSelect.value,
    format: $("#format").value,
    cards: [...document.querySelectorAll('input[name="card"]:checked')].map(input => input.value),
  };
}

function translate(key) {
  return TRANSLATIONS[localeSelect.value]?.[key] ?? TRANSLATIONS["pt-BR"][key] ?? key;
}

function applyLocale(locale) {
  const nextLocale = Object.hasOwn(TRANSLATIONS, locale) ? locale : "pt-BR";
  localeSelect.value = nextLocale;
  document.documentElement.lang = nextLocale;
  for (const element of document.querySelectorAll("[data-i18n]")) {
    const value = translate(element.dataset.i18n);
    if (HTML_TRANSLATIONS.has(element.dataset.i18n)) element.innerHTML = value;
    else element.textContent = value;
  }
  renderSnippet();
}

function errorMessage(code) {
  const key = { username: "errorUsername", repository: "errorRepository", cards: "errorCards" }[code];
  return key ? translate(key) : "";
}

function renderSnippet() {
  const options = readOptions();
  const validation = validateOptions(options);
  errorElement.hidden = validation.ok;
  errorElement.textContent = validation.ok ? "" : errorMessage(validation.code);
  snippetElement.textContent = validation.ok ? buildReadmeSnippet(options) : "";
}

function renderPreviewSelection() {
  const selected = new Set(readOptions().cards);
  for (const card of ["stats", "languages", "rhythm"]) {
    const element = $(`[data-card-preview="${card}"]`);
    if (element) element.hidden = !selected.has(card);
  }
  const topCards = [...selected].filter(card => card === "stats" || card === "languages").length;
  $(".cards-preview").classList.toggle("single-top", topCards === 1);
}

async function copySnippet() {
  renderSnippet();
  const content = snippetElement.textContent;
  if (!content) return;
  try {
    await navigator.clipboard.writeText(content);
    copyStatus.textContent = translate("copied");
  } catch {
    const range = document.createRange();
    range.selectNodeContents(snippetElement);
    const selection = window.getSelection();
    selection.removeAllRanges();
    selection.addRange(range);
    copyStatus.textContent = translate("copyFailed");
  }
}

for (const element of document.querySelectorAll("#username, #repository, #format")) {
  element.addEventListener("input", renderSnippet);
  element.addEventListener("change", renderSnippet);
}
for (const input of document.querySelectorAll('input[name="card"]')) {
  input.addEventListener("change", () => {
    renderPreviewSelection();
    renderSnippet();
  });
}
localeSelect.addEventListener("change", () => {
  copyStatus.textContent = "";
  applyLocale(localeSelect.value);
  try { localStorage.setItem("profilekit-locale", localeSelect.value); } catch { /* Storage is optional. */ }
});
$("#generateButton").addEventListener("click", () => {
  renderSnippet();
  if (snippetElement.textContent) $("#outputTitle").scrollIntoView({ behavior: "smooth", block: "center" });
});
$("#copyButton").addEventListener("click", copySnippet);

let initialLocale = detectLocale(navigator.language);
try { initialLocale = localStorage.getItem("profilekit-locale") || initialLocale; } catch { /* Storage is optional. */ }
applyLocale(initialLocale);
renderPreviewSelection();
