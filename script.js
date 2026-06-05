const messages = document.querySelector("#messages");
const form = document.querySelector("#chat-form");
const input = document.querySelector("#message-input");
const reflection = document.querySelector("#reflection");
const moodButtons = document.querySelectorAll(".mood-chip");
const authScreen = document.querySelector("#auth-screen");
const appShell = document.querySelector("#app-shell");
const authForm = document.querySelector("#auth-form");
const authUsername = document.querySelector("#auth-username");
const authPassword = document.querySelector("#auth-password");
const authError = document.querySelector("#auth-error");
const currentUser = document.querySelector("#current-user");
const logoutButton = document.querySelector("#logout-button");
const conversationStorageKey = "aurora.conversation";
const sessionStorageKey = "aurora.sessionId";
const authTokenStorageKey = "aurora.authToken";
const authUserStorageKey = "aurora.authUser";
const apiChatUrl = window.location.protocol === "file:"
  ? "http://localhost:5000/api/chat"
  : "/api/chat";
const apiBaseUrl = window.location.protocol === "file:" ? "http://localhost:5000" : "";
const sessionId = getOrCreateSessionId();
let authToken = localStorage.getItem(authTokenStorageKey) || "";
let authUser = JSON.parse(localStorage.getItem(authUserStorageKey) || "null");

const moods = {
  ansiedade: {
    words: ["ansioso", "ansiosa", "ansiedade", "pânico", "medo", "preocupado", "preocupada", "nervoso", "nervosa"],
    reflection: "Parece que seu sistema está tentando te proteger demais agora. Vamos trazer o corpo para o presente."
  },
  tristeza: {
    words: ["triste", "sozinho", "sozinha", "vazio", "vazia", "choro", "chorar", "desanimado", "desanimada"],
    reflection: "Tem um peso aí pedindo cuidado, não julgamento."
  },
  raiva: {
    words: ["raiva", "ódio", "irritado", "irritada", "injustiça", "explodir", "bravo", "brava"],
    reflection: "Raiva muitas vezes aponta para um limite, uma injustiça ou uma necessidade não ouvida."
  },
  cansaço: {
    words: ["cansado", "cansada", "exausto", "exausta", "esgotado", "esgotada", "sem energia", "sono"],
    reflection: "Seu corpo pode estar pedindo menos cobrança e mais recuperação."
  },
  alegria: {
    words: ["feliz", "alegre", "animado", "animada", "grato", "grata", "alívio", "orgulho"],
    reflection: "Tem algo bom aparecendo. Vale deixar isso ocupar espaço também."
  },
  culpa: {
    words: ["culpa", "culpado", "culpada", "errei", "falhei", "devia", "arrependido", "arrependida"],
    reflection: "A culpa precisa ser separada de punição para poder virar reparo."
  },
  vergonha: {
    words: ["vergonha", "envergonhado", "envergonhada", "humilhado", "humilhada", "ridículo", "ridícula", "exposto", "exposta"],
    reflection: "Vergonha tenta te esconder quando você mais precisa de cuidado."
  },
  solidão: {
    words: ["solidão", "sozinho", "sozinha", "isolado", "isolada", "ninguém liga", "sem ninguém", "abandonado", "abandonada"],
    reflection: "Solidão costuma doer mais quando parece que ninguém testemunha o que você vive."
  },
  estresse: {
    words: ["estresse", "estressado", "estressada", "pressão", "correria", "sobrecarregado", "sobrecarregada", "prazo", "cobrança"],
    reflection: "Estresse pede redução de carga antes de pedir produtividade."
  },
  luto: {
    words: ["luto", "morreu", "falecimento", "perda", "perdi alguém", "saudade", "despedida", "velório", "enterro"],
    reflection: "Luto não é algo para vencer rápido; é uma dor que precisa de espaço."
  },
  autoestima: {
    words: ["sou um lixo", "não presto", "me odeio", "feio", "feia", "inútil", "fracasso", "burro", "burra", "não sou suficiente"],
    reflection: "Autoataque costuma parecer verdade quando você está exausto por dentro."
  }
};

const aiState = {
  turns: [],
  conversation: [],
  lastMood: null,
  lastIntensity: 0,
  repeatedMoodCount: 0
};

const emotionLexicon = {
  ansiedade: {
    weight: 2,
    words: ["ansioso", "ansiosa", "ansiedade", "pânico", "panico", "medo", "preocupado", "preocupada", "nervoso", "nervosa", "aperto", "inseguro", "insegura", "e se"]
  },
  tristeza: {
    weight: 2,
    words: ["triste", "sozinho", "sozinha", "vazio", "vazia", "choro", "chorar", "desanimado", "desanimada", "saudade", "perdi", "dor", "abandono"]
  },
  raiva: {
    weight: 2,
    words: ["raiva", "ódio", "odio", "irritado", "irritada", "injustiça", "injustica", "explodir", "bravo", "brava", "absurdo", "limite"]
  },
  cansaço: {
    weight: 2,
    words: ["cansado", "cansada", "exausto", "exausta", "esgotado", "esgotada", "sem energia", "sono", "sobrecarregado", "sobrecarregada", "não dou conta", "nao dou conta"]
  },
  alegria: {
    weight: 1.5,
    words: ["feliz", "alegre", "animado", "animada", "grato", "grata", "alívio", "alivio", "orgulho", "consegui", "bom", "leve"]
  },
  culpa: {
    weight: 1.8,
    words: ["culpa", "culpado", "culpada", "errei", "falhei", "devia", "arrependido", "arrependida"]
  },
  confusão: {
    weight: 1.4,
    words: ["confuso", "confusa", "não sei", "nao sei", "perdido", "perdida", "indeciso", "indecisa", "travado", "travada"]
  },
  vergonha: {
    weight: 1.8,
    words: ["vergonha", "envergonhado", "envergonhada", "humilhado", "humilhada", "ridículo", "ridicula", "exposto", "exposta", "julgado", "julgada"]
  },
  solidão: {
    weight: 2,
    words: ["solidão", "solidao", "sozinho", "sozinha", "isolado", "isolada", "ninguém liga", "ninguem liga", "sem ninguém", "sem ninguem", "abandonado", "abandonada", "invisível", "invisivel"]
  },
  estresse: {
    weight: 1.9,
    words: ["estresse", "estressado", "estressada", "pressão", "pressao", "correria", "sobrecarregado", "sobrecarregada", "prazo", "cobrança", "cobranca", "tensão", "tensao"]
  },
  luto: {
    weight: 2.2,
    words: ["luto", "morreu", "falecimento", "perda", "perdi alguém", "perdi alguem", "saudade", "despedida", "velório", "velorio", "enterro"]
  },
  autoestima: {
    weight: 1.8,
    words: ["sou um lixo", "não presto", "nao presto", "me odeio", "feio", "feia", "inútil", "inutil", "fracasso", "burro", "burra", "não sou suficiente", "nao sou suficiente"]
  },
  ciúme: {
    weight: 1.6,
    words: ["ciúme", "ciume", "ciúmes", "ciumes", "medo de perder", "comparando", "comparação", "comparacao", "traição", "traicao", "trair", "traindo", "traído", "traido", "traída", "traida"]
  },
  esperança: {
    weight: 1.4,
    words: ["esperança", "esperanca", "esperançoso", "esperancoso", "esperançosa", "esperancosa", "melhorando", "vai passar", "confiante", "recomeçar", "recomecar"]
  }
};

const intensityWords = {
  high: ["muito", "demais", "horrível", "horrivel", "insuportável", "insuportavel", "sempre", "nunca", "desespero", "urgente"],
  low: ["um pouco", "talvez", "meio", "leve", "passageiro", "passageira"]
};

const contextSignals = {
  relationship: ["mãe", "mae", "pai", "família", "familia", "namoro", "namorado", "namorada", "amigo", "amiga", "colega"],
  work: ["trabalho", "empresa", "reunião", "reuniao", "prazo", "cliente", "faculdade", "prova", "estudo"],
  body: ["peito", "respirar", "coração", "coracao", "tremendo", "enjoo", "cabeça", "cabeca", "corpo"],
  isolation: ["ninguém", "ninguem", "sozinho", "sozinha", "não tenho com quem", "nao tenho com quem"],
  future: ["futuro", "amanhã", "amanha", "próxima semana", "proxima semana", "e agora", "daqui pra frente"],
  selfImage: ["me odeio", "não presto", "nao presto", "fracasso", "feio", "feia", "inútil", "inutil"]
};

const crisisWords = [
  "suicídio",
  "suicidio",
  "me matar",
  "tirar minha vida",
  "morrer",
  "não aguento mais",
  "nao aguento mais",
  "sumir para sempre",
  "acabar com tudo"
];

const starters = [
  "Estou aqui com você. O que aconteceu hoje?",
  "Pode escrever do jeito que vier. Eu vou acompanhar o fio com calma.",
  "Se tivesse que dar uma nota de 0 a 10 para a intensidade disso agora, qual seria?"
];

const microQuestions = [
  "Qual foi o gatilho mais perto disso?",
  "O que você precisava ter recebido nesse momento?",
  "Onde isso aparece no corpo agora?",
  "Qual seria um próximo passo pequeno o bastante para caber no seu estado atual?",
  "Você quer mais acolhimento, clareza ou um plano de ação?",
  "Qual parte disso você consegue cuidar sem resolver tudo agora?",
  "O que seria um sinal pequeno de alívio nos próximos minutos?"
];

const regulationTools = {
  ansiedade: "Vamos baixar a urgência: solte os ombros, encoste os pés no chão e descreva uma coisa concreta ao seu redor.",
  tristeza: "Por agora, tente não discutir com a tristeza. Só nomeie: 'isso dói porque...'. Uma frase basta.",
  raiva: "Antes de agir, descarregue em texto cru por 60 segundos. Depois a gente separa fato, limite e pedido.",
  cansaço: "Seu próximo passo pode ser fisiológico: água, banho, comida simples, deitar 10 minutos ou desligar uma cobrança.",
  alegria: "Registre esse ponto bom com detalhes. Isso ajuda a mente a reconhecer caminhos que funcionam.",
  culpa: "Vamos separar responsabilidade de punição. O que você faria diferente se pudesse reparar sem se atacar?",
  confusão: "Quando tudo mistura, escolha só duas colunas: o que eu sei e o que eu ainda não sei.",
  vergonha: "Tente falar consigo como falaria com alguém querido: o que aconteceu não define quem você é.",
  solidão: "Escolha uma ponte pequena: mandar uma mensagem simples, ficar perto de alguém ou nomear aqui o que você queria receber.",
  estresse: "Liste três pendências e marque só uma como próximo passo. O resto pode esperar alguns minutos.",
  luto: "Se couber, escolha uma memória concreta. Não para doer menos, mas para dar forma ao amor e à perda.",
  autoestima: "Troque julgamento por evidência: cite uma coisa difícil que você está enfrentando e uma coisa mínima que ainda está tentando fazer.",
  ciúme: "Antes de acusar ou se calar, separe: o que eu vi, o que eu imaginei e o que eu preciso pedir com clareza.",
  esperança: "Anote o que ajudou essa sensação a aparecer. Isso pode virar uma pista de cuidado para os próximos dias."
};

const moodContextLines = {
  vergonha: "Vergonha costuma diminuir quando a experiência pode ser vista com gentileza e proporção.",
  luto: "No luto, lembrar e sofrer podem andar juntos; não precisa apressar esse processo.",
  autoestima: "Quando a dor vira ataque contra si, a mente costuma apagar as evidências de esforço e resistência.",
  solidão: "A sensação de estar sem apoio costuma aumentar o volume de qualquer dor.",
  estresse: "Quando há pressão demais, clareza vem depois de reduzir a carga imediata.",
  ciúme: "Ciúme pede segurança, mas funciona melhor quando vira conversa clara em vez de vigilância.",
  esperança: "Esperança também merece cuidado; ela pode ser pequena e ainda assim real."
};

function addMessage(text, sender = "bot") {
  return addMessageToDom(text, sender, true);
}

function addMessageToDom(text, sender = "bot", persist = true) {
  const bubble = document.createElement("div");
  bubble.className = `message ${sender}`;
  bubble.textContent = text;
  messages.appendChild(bubble);
  messages.scrollTop = messages.scrollHeight;
  if (persist) {
    aiState.conversation.push({ sender, text });
    aiState.conversation = aiState.conversation.slice(-30);
    saveConversation();
  }
  return bubble;
}

function getOrCreateSessionId() {
  const existing = localStorage.getItem(sessionStorageKey);
  if (existing) return existing;

  const id = `aurora-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
  localStorage.setItem(sessionStorageKey, id);
  return id;
}

function saveConversation() {
  localStorage.setItem(getConversationStorageKey(), JSON.stringify(aiState.conversation));
}

function getConversationStorageKey() {
  const username = authUser?.username || "anonymous";
  return `${conversationStorageKey}.${username}`;
}

function restoreConversation() {
  try {
    const stored = JSON.parse(localStorage.getItem(getConversationStorageKey()) || "[]");
    if (!Array.isArray(stored)) return false;

    aiState.conversation = stored
      .filter((item) => item && typeof item.text === "string" && typeof item.sender === "string")
      .slice(-30);

    aiState.conversation.forEach((item) => addMessageToDom(item.text, item.sender, false));
    return aiState.conversation.length > 0;
  } catch {
    return false;
  }
}

async function authRequest(path, body) {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(body)
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.error || "Falha de autenticacao.");
  }
  return data;
}

function setAuthSession(token, user) {
  authToken = token;
  authUser = user;
  localStorage.setItem(authTokenStorageKey, token);
  localStorage.setItem(authUserStorageKey, JSON.stringify(user));
  showApp();
}

function clearAuthSession() {
  authToken = "";
  authUser = null;
  localStorage.removeItem(authTokenStorageKey);
  localStorage.removeItem(authUserStorageKey);
  aiState.conversation = [];
  messages.innerHTML = "";
  showAuth();
}

function showApp() {
  authScreen.classList.add("is-hidden");
  appShell.classList.remove("is-hidden");
  currentUser.textContent = authUser?.username ? `@${authUser.username}` : "IA local";
  messages.innerHTML = "";
  aiState.conversation = [];
  if (!restoreConversation()) {
    addMessage(starters[Math.floor(Math.random() * starters.length)]);
  }
}

function showAuth() {
  appShell.classList.add("is-hidden");
  authScreen.classList.remove("is-hidden");
  currentUser.textContent = "IA local";
}

async function verifyExistingSession() {
  if (!authToken) {
    showAuth();
    return;
  }

  try {
    const response = await fetch(`${apiBaseUrl}/api/me`, {
      headers: {
        Authorization: `Bearer ${authToken}`
      }
    });
    if (!response.ok) throw new Error("Sessao expirada.");
    const data = await response.json();
    authUser = data.user;
    localStorage.setItem(authUserStorageKey, JSON.stringify(authUser));
    showApp();
  } catch {
    clearAuthSession();
  }
}

function normalizeText(text) {
  return text
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}

function countMatches(normalizedText, words) {
  return words.reduce((total, word) => {
    const normalizedWord = normalizeText(word);
    return normalizedText.includes(normalizedWord) ? total + 1 : total;
  }, 0);
}

function analyzeMessage(text, forcedMood) {
  const normalized = normalizeText(text);
  const scores = Object.fromEntries(Object.keys(emotionLexicon).map((key) => [key, 0]));

  Object.entries(emotionLexicon).forEach(([emotion, config]) => {
    scores[emotion] = countMatches(normalized, config.words) * config.weight;
  });

  if (forcedMood && scores[forcedMood] !== undefined) {
    scores[forcedMood] += 4;
  }

  const ranked = Object.entries(scores).sort((a, b) => b[1] - a[1]);
  const primaryMood = ranked[0][1] > 0 ? ranked[0][0] : null;
  const secondaryMood = ranked[1][1] > 0 ? ranked[1][0] : null;
  const highIntensity = countMatches(normalized, intensityWords.high);
  const lowIntensity = countMatches(normalized, intensityWords.low);
  const exclamationBoost = Math.min((text.match(/!/g) || []).length, 3);
  const lengthBoost = text.length > 180 ? 1 : 0;
  const intensity = Math.max(1, Math.min(10, 3 + highIntensity * 2 + exclamationBoost + lengthBoost - lowIntensity));

  const signals = Object.fromEntries(
    Object.entries(contextSignals).map(([signal, words]) => [signal, countMatches(normalized, words) > 0])
  );

  return {
    text,
    normalized,
    primaryMood,
    secondaryMood,
    intensity,
    scores,
    signals,
    asksQuestion: text.includes("?")
  };
}

function rememberAnalysis(analysis) {
  if (analysis.primaryMood && analysis.primaryMood === aiState.lastMood) {
    aiState.repeatedMoodCount += 1;
  } else {
    aiState.repeatedMoodCount = analysis.primaryMood ? 1 : 0;
  }

  aiState.lastMood = analysis.primaryMood || aiState.lastMood;
  aiState.lastIntensity = analysis.intensity;
  aiState.turns.push(analysis);
  aiState.turns = aiState.turns.slice(-6);
}

function hasCrisisSignal(text) {
  const normalized = normalizeText(text);
  return crisisWords.some((word) => normalized.includes(normalizeText(word)));
}

function getDominantPattern() {
  const counts = aiState.turns.reduce((result, turn) => {
    if (turn.primaryMood) result[turn.primaryMood] = (result[turn.primaryMood] || 0) + 1;
    return result;
  }, {});

  return Object.entries(counts).sort((a, b) => b[1] - a[1])[0]?.[0] || null;
}

function buildEmpathy(analysis) {
  if (!analysis.primaryMood) {
    return "Entendi. Tem algo importante aí, mesmo que ainda esteja meio sem nome.";
  }

  const secondary = analysis.secondaryMood ? ` com um pouco de ${analysis.secondaryMood}` : "";
  const intensity = analysis.intensity >= 8 ? "bem intenso" : analysis.intensity >= 6 ? "forte" : "presente";
  return `Estou captando ${analysis.primaryMood}${secondary}, e parece ${intensity} agora.`;
}

function buildContextLine(analysis) {
  if (moodContextLines[analysis.primaryMood]) {
    return moodContextLines[analysis.primaryMood];
  }

  if (analysis.signals.relationship) {
    return "Quando envolve gente próxima, a emoção costuma vir misturada com necessidade de vínculo, limite ou reconhecimento.";
  }

  if (analysis.signals.work) {
    return "Como isso toca trabalho ou desempenho, pode ter uma camada de cobrança junto da emoção principal.";
  }

  if (analysis.signals.body) {
    return "Seu corpo já entrou na conversa; isso é um dado importante, não um detalhe.";
  }

  if (analysis.signals.isolation) {
    return "A sensação de estar sem apoio costuma aumentar o volume de qualquer dor.";
  }

  if (analysis.signals.selfImage) {
    return "Quando a dor vira ataque contra si, a mente costuma apagar as evidências de esforço e resistência.";
  }

  if (analysis.signals.future) {
    return "Quando o futuro fica nebuloso, o melhor ponto de apoio costuma ser o próximo gesto concreto.";
  }

  return "Vou responder pelo que aparece agora, sem tentar fechar diagnóstico sobre você.";
}

function buildNextStep(analysis) {
  const mood = analysis.primaryMood || getDominantPattern();
  const tool = regulationTools[mood] || "Vamos transformar isso em algo observável: fato, sentimento, necessidade e próximo passo.";
  const question = analysis.intensity >= 8
    ? "Antes de continuar: você está seguro agora?"
    : microQuestions[(aiState.turns.length + analysis.text.length) % microQuestions.length];

  if (aiState.repeatedMoodCount >= 3 && mood) {
    return `${tool}\n\nPercebo que ${mood} apareceu algumas vezes. Talvez valha procurar o padrão: o que sempre acontece antes desse sentimento subir?`;
  }

  return `${tool}\n\n${question}`;
}

function composeCrisisReply() {
  reflection.textContent = "Esse tipo de dor merece presença humana agora, não só uma tela.";
  return "Eu sinto muito que esteja nesse ponto. Se houver risco de você se machucar, procure ajuda imediata agora: ligue para a emergência local ou chame alguém de confiança para ficar com você.\n\nNo Brasil, o CVV atende pelo 188. Se você estiver em outro país, procure o serviço de crise da sua região. Enquanto isso, afaste objetos que possam te machucar e me responda só: você está em segurança neste momento?";
}

function updateReflectionForAnalysis(analysis) {
  if (analysis.primaryMood && moods[analysis.primaryMood]) {
    reflection.textContent = moods[analysis.primaryMood].reflection;
  } else if (analysis.primaryMood && regulationTools[analysis.primaryMood]) {
    reflection.textContent = "A emoção apareceu com nuances. Vamos deixar ela mais legível antes de decidir o que fazer.";
  } else {
    reflection.textContent = "Estou tentando entender a textura disso com você.";
  }
}

function composeReply(text, forcedMood, existingAnalysis) {
  if (hasCrisisSignal(text)) {
    return composeCrisisReply();
  }

  const analysis = existingAnalysis || analyzeMessage(text, forcedMood);
  if (!existingAnalysis) {
    rememberAnalysis(analysis);
  }
  updateReflectionForAnalysis(analysis);

  const parts = [
    buildEmpathy(analysis),
    buildContextLine(analysis),
    buildNextStep(analysis)
  ];

  return parts.join("\n\n");
}

async function requestPythonReply(text) {
  const response = await fetch(apiChatUrl, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${authToken}`
    },
    body: JSON.stringify({
      sessionId,
      message: text,
      history: aiState.conversation.slice(0, -2)
    })
  });

  if (!response.ok) {
    if (response.status === 401) {
      clearAuthSession();
      throw new Error("Login necessario.");
    }
    throw new Error("Backend Python indisponivel.");
  }

  const data = await response.json();
  if (!data.reply) {
    throw new Error("Resposta vazia do backend.");
  }

  return data.reply;
}

function sendUserMessage(text, forcedMood) {
  addMessage(text, "user");
  input.value = "";
  input.style.height = "auto";

  const localAnalysis = hasCrisisSignal(text) ? null : analyzeMessage(text, forcedMood);
  if (localAnalysis) {
    rememberAnalysis(localAnalysis);
    updateReflectionForAnalysis(localAnalysis);
  }

  const typingBubble = addMessage("Pensando...", "bot");

  window.setTimeout(async () => {
    try {
      const reply = hasCrisisSignal(text) ? composeCrisisReply() : await requestPythonReply(text);
      typingBubble.textContent = reply;
      aiState.conversation[aiState.conversation.length - 1].text = reply;
      saveConversation();
    } catch {
      const fallbackReply = composeReply(text, forcedMood, localAnalysis);
      typingBubble.textContent = fallbackReply;
      aiState.conversation[aiState.conversation.length - 1].text = fallbackReply;
      saveConversation();
    }
  }, 380);
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const text = input.value.trim();
  if (!text) return;
  sendUserMessage(text);
});

input.addEventListener("input", () => {
  input.style.height = "auto";
  input.style.height = `${input.scrollHeight}px`;
});

input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});

moodButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const mood = button.dataset.mood;
    sendUserMessage(`Estou sentindo ${mood}.`, mood);
  });
});

authForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const submitter = event.submitter;
  const action = submitter?.dataset.authAction || "login";
  authError.textContent = "";

  try {
    const data = await authRequest(`/api/${action}`, {
      username: authUsername.value.trim(),
      password: authPassword.value
    });
    authPassword.value = "";
    setAuthSession(data.token, data.user);
  } catch (error) {
    authError.textContent = error.message;
  }
});

logoutButton.addEventListener("click", async () => {
  if (authToken) {
    await fetch(`${apiBaseUrl}/api/logout`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${authToken}`
      }
    }).catch(() => {});
  }
  clearAuthSession();
});

verifyExistingSession();
