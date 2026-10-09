import { buildReadmeSnippet, detectLocale, validateOptions } from "./generator.js";

const TRANSLATIONS = {
  "pt-BR": {
    navGuide: "Como funciona", navSource: "Código-fonte", languageLabel: "Idioma",
    eyebrow: "GERADOR OPEN SOURCE · PERFIL GITHUB", heroTitle: "Mostre seu trabalho<br /><span>com clareza.</span>",
    heroDescription: "Escolha os cartões, confira a prévia e gere um snippet pronto para o README do seu perfil.",
    privacyLine: "Sem login. Sem tokens no navegador. Seus dados ficam no GitHub.", openSource: "Código aberto",
    stepConfigure: "CONFIGURE", formTitle: "Seu perfil", usernameLabel: "Usuário do GitHub",
    usernameHint: "O mesmo nome que aparece em github.com/...", repoLabel: "Repositório dos cartões",
    formatLabel: "Formato do snippet", htmlOption: "HTML · responsivo", markdownOption: "Markdown · simples",
    cardsLegend: "Cartões no README", statsOption: "Status do GitHub", statsHint: "Contribuições, commits, estrelas e visitas",
    languagesOption: "Linguagens", languagesHint: "Distribuição de código por linguagem",
    rhythmOption: "Ritmo de contribuições", rhythmHint: "Total histórico e sequências",
    liveLabel: "Contador de visitas via Vercel", liveHint: "Consulta ao receber a imagem; o cache do GitHub ainda pode interferir.",
    deploymentLabel: "URL do seu deploy Vercel", deploymentHint: "O projeto precisa estar conectado ao seu repositório e configurado para seu perfil.",
    generateButton: "Gerar snippet", finePrint: "O gerador cria apenas os links. Os cartões são atualizados pela GitHub Action da sua cópia.",
    stepPreview: "PRÉVIA", previewTitle: "Seu layout", previewLive: "LAYOUT", previewStats: "Status do GitHub",
    metricStars: "Estrelas", metricCommits: "Commits · ano", metricRepos: "Repositórios · ano",
    metricContributions: "Contribuições · ano", metricViews: "Visitas do perfil", previewLanguages: "Linguagens mais usadas",
    previewLanguageNote: "Código dos repositórios configurados", previewRhythm: "Ritmo de contribuições",
    metricAllTime: "Contribuições · todo o período", metricCurrent: "Sequência atual · dias", metricBest: "Maior sequência · dias",
    previewRhythmNote: "Prévia visual · os números serão os seus",
    previewDisclaimer: "Os números acima são ilustrativos. Seus cartões recebem métricas da sua conta após configurar o repositório.",
    stepOutput: "COPIE", outputTitle: "Snippet do README", copyButton: "Copiar código",
    errorUsername: "Informe um nome de usuário GitHub válido.", errorRepository: "Informe um nome de repositório válido.",
    errorCards: "Selecione pelo menos um cartão.", errorDeployment: "Informe uma URL HTTPS válida do seu deploy Vercel.",
    copied: "Código copiado para a área de transferência.", copyFailed: "Não consegui copiar automaticamente. Selecione e copie o código acima.",
    howEyebrow: "DA CÓPIA AO PERFIL", howTitle: "Três passos. Seu perfil atualizado.", howForkTitle: "Faça sua cópia",
    howForkText: "Crie um fork público deste repositório para gerar os cartões com as suas métricas.", forkLink: "Abrir fork no GitHub",
    howConfigureTitle: "Configure a Action", howConfigureText: "Ative o workflow. Secrets opcionais permitem agregar contribuições e linguagens privadas com leitura limitada.",
    permissionsLink: "Ver permissões e guia", howPasteTitle: "Cole no perfil", howPasteText: "Adicione o snippet ao README do repositório que tem o mesmo nome da sua conta GitHub.",
    profileHelp: "Ajuda do GitHub", footerText: "Feito para deixar seus projetos falarem por você.", licenseLink: "Licença MIT",
  },
  en: {
    navGuide: "How it works", navSource: "Source code", languageLabel: "Language",
    eyebrow: "OPEN SOURCE · GITHUB PROFILE BUILDER", heroTitle: "Make your work<br /><span>easy to see.</span>",
    heroDescription: "Choose your cards, preview the layout and create a snippet for your GitHub profile README.",
    privacyLine: "No sign-in. No tokens in your browser. Your data stays on GitHub.", openSource: "Open source",
    stepConfigure: "CONFIGURE", formTitle: "Your profile", usernameLabel: "GitHub username",
    usernameHint: "The name shown at github.com/...", repoLabel: "Cards repository", formatLabel: "Snippet format",
    htmlOption: "HTML · responsive", markdownOption: "Markdown · simple", cardsLegend: "Cards in your README",
    statsOption: "GitHub status", statsHint: "Contributions, commits, stars and views", languagesOption: "Languages",
    languagesHint: "Code distribution by language", rhythmOption: "Contribution rhythm", rhythmHint: "All-time total and streaks",
    liveLabel: "Vercel live view counter", liveHint: "Fetched when the image loads; GitHub caching may still apply.",
    deploymentLabel: "Your Vercel deployment URL", deploymentHint: "The project must be connected to your repository and configured for your profile.",
    generateButton: "Generate snippet", finePrint: "This builder creates embed links only. Your GitHub Action updates the cards in your copy.",
    stepPreview: "PREVIEW", previewTitle: "Your layout", previewLive: "LAYOUT", previewStats: "GitHub status",
    metricStars: "Stars", metricCommits: "Commits · year", metricRepos: "Repositories · year",
    metricContributions: "Contributions · year", metricViews: "Profile views", previewLanguages: "Most used languages",
    previewLanguageNote: "Code from configured repositories", previewRhythm: "Contribution rhythm",
    metricAllTime: "Contributions · all time", metricCurrent: "Current streak · days", metricBest: "Longest streak · days",
    previewRhythmNote: "Visual preview · the numbers will be yours",
    previewDisclaimer: "The numbers above are examples. Your cards use your account metrics after you configure the repository.",
    stepOutput: "COPY", outputTitle: "README snippet", copyButton: "Copy code",
    errorUsername: "Enter a valid GitHub username.", errorRepository: "Enter a valid repository name.", errorCards: "Select at least one card.",
    errorDeployment: "Enter a valid HTTPS URL for your Vercel deployment.", copied: "Code copied to the clipboard.", copyFailed: "Automatic copy failed. Select and copy the code above.",
    howEyebrow: "FROM FORK TO PROFILE", howTitle: "Three steps. Your profile is ready.", howForkTitle: "Create your copy",
    howForkText: "Fork this public repository to generate the cards with your own metrics.", forkLink: "Open fork on GitHub",
    howConfigureTitle: "Configure Actions", howConfigureText: "Enable the workflow. Optional secrets aggregate private contributions and languages with limited read access.",
    permissionsLink: "View permissions and guide", howPasteTitle: "Paste into your profile", howPasteText: "Add the snippet to the README in the repository with the same name as your GitHub account.",
    profileHelp: "GitHub help", footerText: "Made to let your projects speak for you.", licenseLink: "MIT License",
  },
  es: {
    navGuide: "Cómo funciona", navSource: "Código fuente", languageLabel: "Idioma",
    eyebrow: "OPEN SOURCE · GENERADOR DE PERFIL GITHUB", heroTitle: "Haz que tu trabajo<br /><span>se vea claro.</span>",
    heroDescription: "Elige las tarjetas, revisa la vista previa y genera un snippet para el README de tu perfil.",
    privacyLine: "Sin iniciar sesión. Sin tokens en el navegador. Tus datos permanecen en GitHub.", openSource: "Código abierto",
    stepConfigure: "CONFIGURA", formTitle: "Tu perfil", usernameLabel: "Usuario de GitHub",
    usernameHint: "El nombre que aparece en github.com/...", repoLabel: "Repositorio de las tarjetas", formatLabel: "Formato del snippet",
    htmlOption: "HTML · adaptable", markdownOption: "Markdown · simple", cardsLegend: "Tarjetas en tu README",
    statsOption: "Estado de GitHub", statsHint: "Contribuciones, commits, estrellas y visitas", languagesOption: "Lenguajes",
    languagesHint: "Distribución del código por lenguaje", rhythmOption: "Ritmo de contribuciones", rhythmHint: "Total histórico y rachas",
    liveLabel: "Contador de visitas en Vercel", liveHint: "Consulta al recibir la imagen; GitHub todavía puede usar caché.",
    deploymentLabel: "URL de tu despliegue en Vercel", deploymentHint: "El proyecto debe estar conectado a tu repositorio y configurado para tu perfil.",
    generateButton: "Generar snippet", finePrint: "El generador crea solo los enlaces. Tu GitHub Action actualiza las tarjetas de tu copia.",
    stepPreview: "VISTA PREVIA", previewTitle: "Tu diseño", previewLive: "DISEÑO", previewStats: "Estado de GitHub",
    metricStars: "Estrellas", metricCommits: "Commits · año", metricRepos: "Repositorios · año",
    metricContributions: "Contribuciones · año", metricViews: "Visitas del perfil", previewLanguages: "Lenguajes más usados",
    previewLanguageNote: "Código de los repositorios configurados", previewRhythm: "Ritmo de contribuciones",
    metricAllTime: "Contribuciones · todo el período", metricCurrent: "Racha actual · días", metricBest: "Racha máxima · días",
    previewRhythmNote: "Vista visual · los números serán tuyos",
    previewDisclaimer: "Los números de arriba son ejemplos. Tus tarjetas usarán las métricas de tu cuenta tras configurar el repositorio.",
    stepOutput: "COPIA", outputTitle: "Snippet del README", copyButton: "Copiar código",
    errorUsername: "Escribe un usuario válido de GitHub.", errorRepository: "Escribe un nombre de repositorio válido.", errorCards: "Selecciona al menos una tarjeta.",
    errorDeployment: "Escribe una URL HTTPS válida de tu despliegue en Vercel.", copied: "Código copiado al portapapeles.", copyFailed: "No se pudo copiar automáticamente. Selecciona y copia el código de arriba.",
    howEyebrow: "DEL FORK AL PERFIL", howTitle: "Tres pasos. Tu perfil actualizado.", howForkTitle: "Crea tu copia",
    howForkText: "Haz un fork público de este repositorio para generar tarjetas con tus propias métricas.", forkLink: "Abrir fork en GitHub",
    howConfigureTitle: "Configura Actions", howConfigureText: "Activa el workflow. Los secrets opcionales agregan contribuciones y lenguajes privados con acceso de lectura limitado.",
    permissionsLink: "Ver permisos y guía", howPasteTitle: "Pégalo en tu perfil", howPasteText: "Añade el snippet al README del repositorio que tenga el mismo nombre que tu cuenta de GitHub.",
    profileHelp: "Ayuda de GitHub", footerText: "Hecho para que tus proyectos hablen por ti.", licenseLink: "Licencia MIT",
  },
};

const $ = selector => document.querySelector(selector);
const localeSelect = $("#locale");
const snippetElement = $("#snippet");
const errorElement = $("#formError");
const copyStatus = $("#copyStatus");
const liveViews = $("#liveViews");
const deploymentField = $("#deploymentField");

function readOptions() {
  return {
    username: $("#username").value,
    repository: $("#repository").value,
    locale: localeSelect.value,
    format: $("#format").value,
    cards: [...document.querySelectorAll('input[name="card"]:checked')].map(input => input.value),
    liveViews: liveViews.checked,
    deploymentUrl: $("#deploymentUrl").value,
  };
}

function translate(key) {
  return TRANSLATIONS[localeSelect.value]?.[key] ?? TRANSLATIONS["pt-BR"][key] ?? key;
}

function applyLocale(locale) {
  localeSelect.value = locale;
  document.documentElement.lang = locale;
  for (const element of document.querySelectorAll("[data-i18n]")) {
    const value = translate(element.dataset.i18n);
    if (element.dataset.i18n === "heroTitle") element.innerHTML = value;
    else element.textContent = value;
  }
  renderSnippet();
}

function errorMessage(code) {
  const key = { username: "errorUsername", repository: "errorRepository", cards: "errorCards", deployment: "errorDeployment" }[code];
  return key ? translate(key) : "";
}

function renderSnippet() {
  const options = readOptions();
  const validation = validateOptions(options);
  deploymentField.hidden = !liveViews.checked;
  errorElement.hidden = validation.ok;
  errorElement.textContent = validation.ok ? "" : errorMessage(validation.code);
  if (!validation.ok) {
    snippetElement.textContent = "";
    return;
  }
  snippetElement.textContent = buildReadmeSnippet(options);
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

for (const element of document.querySelectorAll("#username, #repository, #format, #deploymentUrl")) {
  element.addEventListener("input", renderSnippet);
  element.addEventListener("change", renderSnippet);
}
for (const input of document.querySelectorAll('input[name="card"]')) {
  input.addEventListener("change", () => {
    renderPreviewSelection();
    renderSnippet();
  });
}
liveViews.addEventListener("change", renderSnippet);
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
