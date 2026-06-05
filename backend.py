from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from difflib import SequenceMatcher
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import secrets
import sys
import time
import unicodedata
import webbrowser


PORT = 5000
IS_FROZEN = getattr(sys, "frozen", False)
RESOURCE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
APP_DIR = Path(sys.executable).resolve().parent if IS_FROZEN else Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "data"
CONVERSATIONS_FILE = DATA_DIR / "conversations.json"
USERS_FILE = DATA_DIR / "users.json"
PSYCHOANALYTIC_NOTES_FILE = RESOURCE_DIR / "data" / "psychoanalytic_notes.json"
_PSYCHOANALYTIC_NOTES = None
SESSIONS = {}

EMOTION_LEXICON = {
    "ansiedade": {
        "weight": 2,
        "words": [
            "ansioso",
            "ansiosa",
            "ansiedade",
            "panico",
            "medo",
            "preocupado",
            "preocupada",
            "nervoso",
            "nervosa",
            "aperto",
            "inseguro",
            "insegura",
            "e se",
        ],
        "reflection": "Parece que seu sistema esta tentando te proteger demais agora.",
        "tool": "Vamos baixar a urgencia: solte os ombros, encoste os pes no chao e descreva uma coisa concreta ao seu redor.",
    },
    "tristeza": {
        "weight": 2,
        "words": [
            "triste",
            "sozinho",
            "sozinha",
            "vazio",
            "vazia",
            "choro",
            "chorar",
            "desanimado",
            "desanimada",
            "saudade",
            "perdi",
            "perdi uma companhia",
            "perdi uma copanhia",
            "companhia",
            "copanhia",
            "dor",
            "abandono",
        ],
        "reflection": "Tem um peso ai pedindo cuidado, nao julgamento.",
        "tool": "Por agora, tente nao discutir com a tristeza. So nomeie: 'isso doi porque...'. Uma frase basta.",
    },
    "raiva": {
        "weight": 2,
        "words": [
            "raiva",
            "odio",
            "irritado",
            "irritada",
            "frustrante",
            "frustrado",
            "frustrada",
            "frustracao",
            "injustica",
            "explodir",
            "bravo",
            "brava",
            "absurdo",
            "limite",
        ],
        "reflection": "Raiva muitas vezes aponta para um limite ou uma necessidade nao ouvida.",
        "tool": "Antes de agir, descarregue em texto cru por 60 segundos. Depois separe fato, limite e pedido.",
    },
    "cansaco": {
        "weight": 2,
        "words": [
            "cansado",
            "cansada",
            "exausto",
            "exausta",
            "esgotado",
            "esgotada",
            "sem energia",
            "sono",
            "sobrecarregado",
            "sobrecarregada",
            "nao dou conta",
        ],
        "reflection": "Seu corpo pode estar pedindo menos cobranca e mais recuperacao.",
        "tool": "Seu proximo passo pode ser fisiologico: agua, banho, comida simples, deitar 10 minutos ou desligar uma cobranca.",
    },
    "alegria": {
        "weight": 1.5,
        "words": [
            "feliz",
            "alegre",
            "animado",
            "animada",
            "grato",
            "grata",
            "alivio",
            "orgulho",
            "consegui",
            "bom",
            "leve",
        ],
        "reflection": "Tem algo bom aparecendo. Vale deixar isso ocupar espaco tambem.",
        "tool": "Registre esse ponto bom com detalhes. Isso ajuda a mente a reconhecer caminhos que funcionam.",
    },
    "culpa": {
        "weight": 1.8,
        "words": [
            "culpa",
            "culpado",
            "culpada",
            "errei",
            "falhei",
            "devia",
            "arrependido",
            "arrependida",
        ],
        "reflection": "A culpa precisa ser separada de punicao para virar reparo.",
        "tool": "Vamos separar responsabilidade de ataque pessoal. O que voce faria diferente se pudesse reparar sem se destruir?",
    },
    "confusao": {
        "weight": 1.4,
        "words": [
            "confuso",
            "confusa",
            "nao sei",
            "perdido",
            "perdida",
            "indeciso",
            "indecisa",
            "travado",
            "travada",
        ],
        "reflection": "Quando tudo mistura, clareza pequena ja ajuda.",
        "tool": "Escolha so duas colunas: o que eu sei e o que eu ainda nao sei.",
    },
    "vergonha": {
        "weight": 1.8,
        "words": [
            "vergonha",
            "envergonhado",
            "envergonhada",
            "humilhado",
            "humilhada",
            "ridiculo",
            "ridicula",
            "exposto",
            "exposta",
            "julgado",
            "julgada",
        ],
        "reflection": "Vergonha tenta te esconder quando voce mais precisa de cuidado.",
        "tool": "Tente falar consigo como falaria com alguem querido: o que aconteceu nao define quem voce e.",
    },
    "solidao": {
        "weight": 2,
        "words": [
            "solidao",
            "sozinho",
            "sozinha",
            "isolado",
            "isolada",
            "ninguem liga",
            "sem ninguem",
            "sem companhia",
            "perdi uma companhia",
            "perdi uma copanhia",
            "abandonado",
            "abandonada",
            "invisivel",
        ],
        "reflection": "Solidao costuma doer mais quando parece que ninguem testemunha o que voce vive.",
        "tool": "Escolha uma ponte pequena: mandar uma mensagem simples, ficar perto de alguem ou nomear aqui o que voce queria receber.",
    },
    "estresse": {
        "weight": 1.9,
        "words": [
            "estresse",
            "estressado",
            "estressada",
            "pressao",
            "correria",
            "sobrecarregado",
            "sobrecarregada",
            "prazo",
            "cobranca",
            "tensao",
        ],
        "reflection": "Estresse pede reducao de carga antes de pedir produtividade.",
        "tool": "Liste tres pendencias e marque so uma como proximo passo. O resto pode esperar alguns minutos.",
    },
    "luto": {
        "weight": 2.2,
        "words": [
            "luto",
            "morreu",
            "falecimento",
            "perda",
            "perdi alguem",
            "perdi uma companhia",
            "perdi uma copanhia",
            "saudade",
            "despedida",
            "velorio",
            "enterro",
        ],
        "reflection": "Luto nao e algo para vencer rapido; e uma dor que precisa de espaco.",
        "tool": "Se couber, escolha uma memoria concreta dessa pessoa ou situacao. Nao para doer menos, mas para dar forma ao amor e a perda.",
    },
    "autoestima": {
        "weight": 1.8,
        "words": [
            "sou um lixo",
            "nao presto",
            "me odeio",
            "feio",
            "feia",
            "inutil",
            "fracasso",
            "burro",
            "burra",
            "nao sou suficiente",
        ],
        "reflection": "Autoataque costuma parecer verdade quando voce esta exausto por dentro.",
        "tool": "Troque julgamento por evidencia: cite uma coisa dificil que voce esta enfrentando e uma coisa minima que ainda esta tentando fazer.",
    },
    "ciume": {
        "weight": 1.6,
        "words": [
            "ciume",
            "ciumes",
            "inseguranca no relacionamento",
            "medo de perder",
            "comparando",
            "comparacao",
            "traicao",
            "trair",
            "traindo",
            "traido",
            "traida",
        ],
        "reflection": "Ciume mistura medo, apego e necessidade de seguranca.",
        "tool": "Antes de acusar ou se calar, separe: o que eu vi, o que eu imaginei e o que eu preciso pedir com clareza.",
    },
    "esperanca": {
        "weight": 1.4,
        "words": [
            "esperanca",
            "esperancoso",
            "esperancosa",
            "melhorando",
            "vai passar",
            "confiante",
            "recomecar",
            "recomeçar",
        ],
        "reflection": "Quando aparece uma fresta de esperanca, vale proteger esse sinal.",
        "tool": "Anote o que ajudou essa sensacao a aparecer. Isso pode virar uma pista de cuidado para os proximos dias.",
    },
}

INTENSITY_HIGH = [
    "muito",
    "demais",
    "horrivel",
    "insuportavel",
    "sempre",
    "nunca",
    "desespero",
    "urgente",
]
INTENSITY_LOW = ["um pouco", "talvez", "meio", "leve", "passageiro", "passageira"]

CONTEXT_SIGNALS = {
    "relationship": [
        "mae",
        "pai",
        "familia",
        "namoro",
        "namorado",
        "namorada",
        "amigo",
        "amiga",
        "colega",
    ],
    "work": ["trabalho", "empresa", "reuniao", "prazo", "cliente", "faculdade", "prova", "estudo"],
    "body": ["peito", "respirar", "coracao", "tremendo", "enjoo", "cabeca", "corpo"],
    "isolation": ["ninguem", "sozinho", "sozinha", "nao tenho com quem"],
    "future": ["futuro", "amanha", "proxima semana", "e agora", "daqui pra frente"],
    "self_image": ["me odeio", "nao presto", "fracasso", "feio", "feia", "inutil"],
}

TOPIC_LEXICON = {
    "trabalho": ["trabalho", "empresa", "chefe", "colega", "cliente", "prazo", "reuniao", "projeto", "demissao"],
    "estudo": ["faculdade", "escola", "prova", "nota", "estudar", "curso", "tcc", "professor", "aula"],
    "familia": ["mae", "pai", "irmao", "irma", "familia", "casa", "filho", "filha", "parente"],
    "relacionamento": ["namoro", "namorado", "namorada", "marido", "esposa", "ex", "relacionamento", "termino", "trai"],
    "amizade": ["amigo", "amiga", "amizade", "grupo", "colega", "convite"],
    "corpo": ["peito", "respirar", "coracao", "tremendo", "enjoo", "cabeca", "insônia", "insonia", "sono"],
    "dinheiro": ["dinheiro", "conta", "divida", "boleto", "salario", "aluguel", "comprar", "pagar"],
    "futuro": ["futuro", "amanha", "semana", "plano", "decisao", "escolha", "daqui pra frente"],
}

INTENT_LEXICON = {
    "desabafo": ["preciso desabafar", "desabafar", "so queria falar", "so quero falar"],
    "conselho": ["o que eu faço", "o que eu faco", "me ajuda", "algum conselho", "como lidar"],
    "decisao": ["decidir", "decisao", "escolher", "nao sei se", "devo"],
    "conflito": ["briguei", "discuti", "me xingou", "falei demais", "conflito"],
    "ruminacao": ["nao paro de pensar", "fico pensando", "e se", "minha cabeça nao para", "minha cabeca nao para"],
    "acolhimento": ["acolhimento", "me acolhe", "so acolhe", "quero acolhimento"],
    "clareza": ["clareza", "quero clareza", "me ajuda a entender"],
    "plano": ["plano", "acao", "ação", "passo a passo", "o que fazer"],
}

SUPPORT_MODE_WORDS = {
    "acolhimento": ["acolhimento", "me acolhe", "so acolhe", "quero acolhimento"],
    "clareza": ["clareza", "quero clareza", "me ajuda a entender"],
    "plano": ["plano", "acao", "ação", "passo a passo"],
}

STOPWORDS = {
    "acho",
    "agora",
    "ainda",
    "algo",
    "alguem",
    "aqui",
    "bem",
    "cada",
    "como",
    "comigo",
    "demais",
    "disso",
    "esse",
    "essa",
    "estou",
    "ficar",
    "hoje",
    "isso",
    "mais",
    "mesmo",
    "muito",
    "nao",
    "para",
    "porque",
    "quando",
    "quero",
    "sobre",
    "tambem",
    "tenho",
    "tudo",
    "voce",
}

CRISIS_WORDS = [
    "suicidio",
    "me matar",
    "tirar minha vida",
    "morrer",
    "nao aguento mais",
    "sumir para sempre",
    "acabar com tudo",
]

MICRO_QUESTIONS = [
    "Qual foi o gatilho mais perto disso?",
    "O que voce precisava ter recebido nesse momento?",
    "Onde isso aparece no corpo agora?",
    "Qual seria um proximo passo pequeno o bastante para caber no seu estado atual?",
    "Voce quer mais acolhimento, clareza ou um plano de acao?",
    "Qual parte disso voce consegue cuidar sem resolver tudo agora?",
    "O que seria um sinal pequeno de alivio nos proximos minutos?",
]

MOOD_CONTEXT_LINES = {
    "vergonha": [
        "Vergonha costuma diminuir quando a experiencia pode ser vista com gentileza e proporcao.",
        "Quando a vergonha aparece, ela tenta te colocar sozinho com algo que talvez precise de testemunha segura.",
        "A vergonha geralmente fala alto, mas nem sempre fala com justica sobre quem voce e.",
    ],
    "luto": [
        "No luto, lembrar e sofrer podem andar juntos; nao precisa apressar esse processo.",
        "Perda mexe com rotina, identidade e presenca; nao e so uma ideia triste passando.",
        "Quando algo ou alguem falta, a mente tenta entender um vazio que o corpo sente antes das palavras.",
    ],
    "autoestima": [
        "Quando a dor vira ataque contra si, a mente costuma apagar as evidencias de esforco e resistencia.",
        "Autoataque parece explicacao, mas muitas vezes e so dor procurando um alvo perto.",
        "Talvez a pergunta agora nao seja se voce vale algo, mas o que te fez esquecer disso por alguns minutos.",
    ],
    "solidao": [
        "A sensacao de estar sem apoio costuma aumentar o volume de qualquer dor.",
        "Solidao nao e so falta de gente; as vezes e falta de sentir que alguem realmente percebe voce.",
        "Quando a solidao aperta, ate dores pequenas ficam com eco maior.",
    ],
    "estresse": [
        "Quando ha pressao demais, clareza vem depois de reduzir a carga imediata.",
        "Estresse costuma transformar tudo em urgencia, mesmo quando nem tudo precisa ser resolvido agora.",
        "Talvez seu sistema esteja pedindo menos demanda antes de pedir mais resposta.",
    ],
    "ciume": [
        "Ciume pede seguranca, mas funciona melhor quando vira conversa clara em vez de vigilancia.",
        "Quando o medo de perder entra, a mente pode misturar fato, fantasia e necessidade de garantia.",
        "Ciume costuma apontar para um pedido de seguranca que ainda nao achou uma forma boa de sair.",
    ],
    "esperanca": [
        "Esperanca tambem merece cuidado; ela pode ser pequena e ainda assim real.",
        "Quando uma fresta boa aparece, vale observar o que ajudou ela a existir.",
        "Esperanca nao precisa virar certeza para ser util; as vezes basta ser uma direcao pequena.",
    ],
}

OPENING_VARIANTS = [
    "Estou acompanhando o fio.",
    "Entendi melhor por esse pedaco.",
    "Isso da mais contorno ao que voce esta vivendo.",
    "Faz sentido esse ponto ter ficado sensivel.",
    "Peguei uma nuance importante aqui.",
    "Tem um sinal emocional bem vivo nessa frase.",
    "Vou pegar isso com cuidado.",
    "Essa parte merece um pouco mais de espaco.",
]

CONTINUATION_VARIANTS = [
    "Vou manter o contexto anterior aqui.",
    "Isso parece continuar a mesma dor, so por outro angulo.",
    "Nao vou tratar essa frase como assunto novo; ela parece parte do mesmo fio.",
    "Esse detalhe conversa com o que voce vinha trazendo.",
    "Isso parece uma continuacao, nao um ponto solto.",
    "Vou ligar essa frase ao que ja apareceu antes.",
    "Esse pedaco ajuda a enxergar melhor o mesmo nucleo.",
]

EMPATHY_VARIANTS = {
    "unknown": [
        "Entendi. Tem algo importante ai, mesmo que ainda esteja meio sem nome.",
        "Ainda nao esta totalmente claro, mas parece haver uma coisa pedindo atencao.",
        "Pode nao estar organizado ainda, e tudo bem; ja da para escutar um sinal ai.",
        "Nao vou forcar uma etiqueta. Vou ficar perto do que apareceu.",
    ],
    "mood": [
        "Estou captando {primary}{secondary}, e parece {intensity} agora.",
        "O que aparece com mais forca e {primary}{secondary}; a intensidade parece {intensity}.",
        "Pelo jeito que voce escreveu, {primary}{secondary} esta bem presente nesse momento.",
        "A leitura que chega aqui e {primary}{secondary}, com um peso {intensity}.",
    ],
}

TOOL_VARIANTS = {
    "ansiedade": [
        "Vamos baixar a urgencia: solte os ombros, encoste os pes no chao e descreva uma coisa concreta ao seu redor.",
        "Antes de resolver, tente voltar para o corpo: respire mais lento e procure cinco detalhes no ambiente.",
        "Se a mente acelerou, escolha uma ancora pequena: pes no chao, ar entrando, ar saindo.",
    ],
    "tristeza": [
        "Por agora, tente nao discutir com a tristeza. So nomeie: 'isso doi porque...'. Uma frase basta.",
        "Talvez o primeiro cuidado seja admitir a dor sem tentar convencer ela a ir embora.",
        "Tente dar uma frase simples para essa tristeza, sem corrigir nem enfeitar.",
    ],
    "raiva": [
        "Antes de agir, descarregue em texto cru por 60 segundos. Depois separe fato, limite e pedido.",
        "A raiva pode virar informacao: o que foi ultrapassado, negado ou injusto aqui?",
        "Segure a acao por um instante e procure o limite que essa raiva esta tentando proteger.",
    ],
    "cansaco": [
        "Seu proximo passo pode ser fisiologico: agua, banho, comida simples, deitar 10 minutos ou desligar uma cobranca.",
        "Quando o corpo esta sem margem, cuidado basico nao e pouco: e base.",
        "Tente reduzir uma demanda pequena antes de exigir clareza de si mesmo.",
    ],
    "culpa": [
        "Vamos separar responsabilidade de ataque pessoal. O que voce faria diferente se pudesse reparar sem se destruir?",
        "Culpa fica menos cruel quando vira pergunta de reparo, nao sentenca contra voce.",
        "Procure a parte reparavel disso e deixe de lado, por um momento, a parte que so te pune.",
    ],
    "solidao": [
        "Escolha uma ponte pequena: mandar uma mensagem simples, ficar perto de alguem ou nomear aqui o que voce queria receber.",
        "Talvez a ponte de agora seja minima: dizer a alguem 'nao estou bem' ja conta.",
        "Se contato real estiver dificil, comece nomeando exatamente que tipo de presenca esta faltando.",
    ],
    "luto": [
        "Se couber, escolha uma memoria concreta dessa pessoa ou situacao. Nao para doer menos, mas para dar forma ao amor e a perda.",
        "No luto, uma memoria pequena pode organizar a dor melhor do que uma explicacao grande.",
        "Deixe a perda ter contorno: o que exatamente esta fazendo falta hoje?",
    ],
    "default": [
        "Vamos transformar isso em algo observavel: fato, sentimento, necessidade e proximo passo.",
        "Vamos diminuir o tamanho do problema: uma coisa que aconteceu, uma emocao, uma necessidade.",
        "Tente separar o que e fato do que e interpretacao; dai a proxima escolha fica menos nebulosa.",
    ],
}

INTENT_CONTEXT_VARIANTS = {
    "conselho": [
        "Vou te dar um caminho pratico, mas mantendo espaco para o que voce esta sentindo.",
        "Da para pensar em acao, mas sem apagar a emocao que trouxe voce ate aqui.",
        "Vamos procurar um passo concreto sem fingir que o sentimento nao importa.",
    ],
    "desabafo": [
        "Vou ficar mais no acolhimento do que em tentar resolver rapido.",
        "Se isso e desabafo, nao precisa virar conclusao agora.",
        "Vou priorizar escuta aqui, porque talvez a primeira coisa seja tirar isso de dentro.",
    ],
    "decisao": [
        "Quando tem decisao no meio da emocao, ajuda separar urgencia, medo e fatos.",
        "Decidir sob carga emocional costuma embaralhar risco real com medo antecipado.",
        "Talvez a decisao precise esperar alguns minutos de clareza, nao de pressa.",
    ],
    "conflito": [
        "Conflito costuma pedir duas leituras: o que aconteceu fora e o que isso tocou dentro.",
        "Quando ha conflito, vale separar a cena externa da ferida que ela ativou.",
        "Aqui parece importante distinguir limite, pedido e reacao.",
    ],
    "ruminacao": [
        "Pensamento em looping geralmente precisa de limite gentil, nao de mais debate interno.",
        "Quando a mente repete a cena, talvez ela esteja buscando seguranca, nao uma resposta perfeita.",
        "Loop mental costuma pedir aterramento antes de analise.",
    ],
}

TOPIC_CONTEXT_VARIANTS = {
    "trabalho": [
        "No trabalho, isso pode misturar cobranca, medo de consequencia e necessidade de limite.",
        "Quando o assunto e trabalho, a emocao pode vir junto com desempenho, hierarquia e pressao.",
        "Talvez exista uma camada de obrigacao ai que esta deixando tudo mais pesado.",
    ],
    "relacionamento": [
        "Em relacionamento, vale separar fato, interpretacao e pedido antes de responder no impulso.",
        "Quando envolve vinculo, o medo de perder ou de nao ser visto pode amplificar tudo.",
        "Talvez a pergunta seja o que aconteceu de fato e que necessidade ficou sem resposta.",
    ],
    "familia": [
        "Com familia, a emocao costuma carregar historia antiga junto do problema de hoje.",
        "Familia as vezes toca camadas antigas, mesmo quando a situacao parece atual.",
        "Quando familia entra, pode haver mais passado na sala do que parece.",
    ],
    "corpo": [
        "Como o corpo apareceu, primeiro vale regular o ritmo antes de tirar conclusoes.",
        "Se o corpo ja entrou na conversa, ele precisa ser ouvido antes da mente decidir tudo.",
        "Sintoma corporal costuma ser um pedido de pausa, nao uma falha sua.",
    ],
}

QUESTION_VARIANTS = {
    "acolhimento": [
        "O que voce mais queria receber agora: presenca, escuta, colo simbolico ou silencio acompanhado?",
        "Se eu ficasse so do seu lado nessa dor, qual parte voce gostaria que eu testemunhasse?",
        "Qual pedaco disso esta mais sozinho dentro de voce?",
    ],
    "perda": [
        "O que voce mais sente falta nessa companhia: presenca, conversa, costume, cuidado ou simplesmente nao estar sozinho?",
        "Que momento pequeno com essa companhia voltou mais forte agora?",
        "O vazio esta mais na rotina, na saudade, ou na sensacao de nao ter para quem voltar?",
    ],
    "frustracao": [
        "Fica comigo nesse ponto: o que exatamente torna isso frustrante agora?",
        "A frustracao vem mais da perda em si, da impotencia, ou de nao conseguir mudar nada?",
        "Se essa frustracao pudesse reclamar de uma coisa, qual seria?",
    ],
}

PSYCHOANALYTIC_LENSES = {
    "freudiana": {
        "words": [
            "infancia",
            "crianca",
            "mae",
            "pai",
            "culpa",
            "desejo",
            "repetindo",
            "repeticao",
            "recalque",
            "defesa",
            "inconsciente",
            "medo de perder",
            "abandono",
        ],
        "line": "Por uma lente freudiana, vale olhar se isso toca desejo, culpa, defesa ou alguma repeticao afetiva antiga.",
        "questions": [
            "Isso parece uma dor de agora ou tambem lembra algo antigo?",
            "Que desejo fica dificil admitir quando essa emocao aparece?",
            "Quando isso acontece, voce tende a se defender atacando, sumindo, agradando ou se culpando?",
        ],
    },
    "junguiana": {
        "words": [
            "sonho",
            "sonhei",
            "simbolo",
            "sombra",
            "persona",
            "mascara",
            "arquétipo",
            "arquetipo",
            "intuição",
            "intuicao",
            "imagem",
            "mito",
            "sentido",
        ],
        "line": "Por uma lente junguiana, isso pode ser visto como imagem psiquica: algo pedindo simbolo, integracao ou menos mascara.",
        "questions": [
            "Se essa emocao fosse uma imagem, que forma ela teria?",
            "Que parte sua voce costuma esconder para conseguir ser aceito?",
            "O que essa situacao mostra sobre a diferenca entre quem voce e e quem precisa parecer ser?",
        ],
    },
}

class EmotionalChatHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(RESOURCE_DIR), **kwargs)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_cors_headers()
        self.end_headers()

    def do_POST(self):
        if self.path == "/api/register":
            self.handle_register()
            return
        if self.path == "/api/login":
            self.handle_login()
            return
        if self.path == "/api/logout":
            self.handle_logout()
            return
        if self.path != "/api/chat":
            self.send_json(404, {"error": "Rota nao encontrada."})
            return

        try:
            user = self.require_user()
            if not user:
                return

            payload = self.read_json()
            message = str(payload.get("message", "")).strip()
            session_id = build_user_session_id(user["username"], str(payload.get("sessionId", "default")))
            saved_history = load_conversation(session_id)
            browser_history = payload.get("history", [])
            history = browser_history if isinstance(browser_history, list) and browser_history else saved_history

            if not message:
                self.send_json(400, {"error": "Mensagem vazia."})
                return

            reply, analysis = compose_reply(message, history if isinstance(history, list) else [])
            updated_history = [*history[-30:], {"sender": "user", "text": message}, {"sender": "bot", "text": reply}]
            save_conversation(session_id, updated_history)
            self.send_json(200, {"reply": reply, "analysis": analysis, "history": updated_history[-30:]})
        except json.JSONDecodeError:
            self.send_json(400, {"error": "JSON invalido."})
        except Exception as error:
            print(error)
            self.send_json(500, {"error": "Erro interno no backend."})

    def do_GET(self):
        if self.path != "/api/me":
            return super().do_GET()

        user = self.get_authenticated_user()
        if not user:
            self.send_json(401, {"authenticated": False})
            return
        self.send_json(200, {"authenticated": True, "user": {"username": user["username"]}})

    def handle_register(self):
        try:
            payload = self.read_json()
            username = normalize_username(str(payload.get("username", "")))
            password = str(payload.get("password", ""))
            if not is_valid_username(username):
                self.send_json(400, {"error": "Usuario deve ter 3 a 30 caracteres: letras, numeros, ponto, _ ou -."})
                return
            if len(password) < 6:
                self.send_json(400, {"error": "Senha deve ter pelo menos 6 caracteres."})
                return

            users = load_users()
            if username in users:
                self.send_json(409, {"error": "Usuario ja existe."})
                return

            users[username] = create_password_record(password)
            save_users(users)
            token = create_session(username)
            self.send_json(201, {"token": token, "user": {"username": username}})
        except json.JSONDecodeError:
            self.send_json(400, {"error": "JSON invalido."})
        except Exception as error:
            print(error)
            self.send_json(500, {"error": "Erro interno no backend."})

    def handle_login(self):
        try:
            payload = self.read_json()
            username = normalize_username(str(payload.get("username", "")))
            password = str(payload.get("password", ""))
            users = load_users()
            record = users.get(username)
            if not record or not verify_password(password, record):
                self.send_json(401, {"error": "Usuario ou senha invalidos."})
                return

            token = create_session(username)
            self.send_json(200, {"token": token, "user": {"username": username}})
        except json.JSONDecodeError:
            self.send_json(400, {"error": "JSON invalido."})
        except Exception as error:
            print(error)
            self.send_json(500, {"error": "Erro interno no backend."})

    def handle_logout(self):
        token = self.get_bearer_token()
        if token:
            SESSIONS.pop(token, None)
        self.send_json(200, {"ok": True})

    def require_user(self):
        user = self.get_authenticated_user()
        if user:
            return user
        self.send_json(401, {"error": "Login necessario."})
        return None

    def get_authenticated_user(self):
        token = self.get_bearer_token()
        if not token:
            return None
        session = SESSIONS.get(token)
        if not session:
            return None
        if session["expiresAt"] < time.time():
            SESSIONS.pop(token, None)
            return None
        users = load_users()
        if session["username"] not in users:
            SESSIONS.pop(token, None)
            return None
        return {"username": session["username"]}

    def get_bearer_token(self):
        authorization = self.headers.get("Authorization", "")
        prefix = "Bearer "
        if not authorization.startswith(prefix):
            return ""
        return authorization[len(prefix):].strip()

    def read_json(self):
        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(min(content_length, 20_000))
        return json.loads(raw_body.decode("utf-8") or "{}")

    def send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")


def normalize_text(text):
    normalized = unicodedata.normalize("NFD", text.lower())
    return "".join(char for char in normalized if unicodedata.category(char) != "Mn")


def sanitize_session_id(value):
    return re.sub(r"[^a-zA-Z0-9_-]", "", value)[:80] or "default"


def normalize_username(value):
    return re.sub(r"\s+", "", normalize_text(value)).lower()


def is_valid_username(username):
    return bool(re.fullmatch(r"[a-z0-9._-]{3,30}", username))


def build_user_session_id(username, session_id):
    return f"{username}:{sanitize_session_id(session_id)}"


def load_users():
    if not USERS_FILE.exists():
        return {}
    try:
        users = json.loads(USERS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return users if isinstance(users, dict) else {}


def save_users(users):
    DATA_DIR.mkdir(exist_ok=True)
    USERS_FILE.write_text(json.dumps(users, ensure_ascii=False, indent=2), encoding="utf-8")


def create_password_record(password):
    salt = secrets.token_hex(16)
    iterations = 180_000
    digest = hash_password(password, salt, iterations)
    return {
        "salt": salt,
        "iterations": iterations,
        "hash": digest,
        "createdAt": int(time.time()),
    }


def hash_password(password, salt, iterations):
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        iterations,
    )
    return digest.hex()


def verify_password(password, record):
    try:
        salt = str(record["salt"])
        iterations = int(record["iterations"])
        expected = str(record["hash"])
    except (KeyError, TypeError, ValueError):
        return False
    actual = hash_password(password, salt, iterations)
    return hmac.compare_digest(actual, expected)


def create_session(username):
    token = secrets.token_urlsafe(32)
    SESSIONS[token] = {
        "username": username,
        "expiresAt": time.time() + 60 * 60 * 24 * 7,
    }
    return token


def load_all_conversations():
    if not CONVERSATIONS_FILE.exists():
        return {}
    try:
        return json.loads(CONVERSATIONS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def load_conversation(session_id):
    conversations = load_all_conversations()
    history = conversations.get(session_id, [])
    return history if isinstance(history, list) else []


def load_psychoanalytic_notes():
    global _PSYCHOANALYTIC_NOTES

    if _PSYCHOANALYTIC_NOTES is not None:
        return _PSYCHOANALYTIC_NOTES

    try:
        notes = json.loads(PSYCHOANALYTIC_NOTES_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        notes = []

    if isinstance(notes, dict):
        _PSYCHOANALYTIC_NOTES = expand_note_library(notes)
    else:
        _PSYCHOANALYTIC_NOTES = notes if isinstance(notes, list) else []
    return _PSYCHOANALYTIC_NOTES


def expand_note_library(library):
    concepts = library.get("concepts", [])
    contexts = library.get("contexts", [])
    if not isinstance(concepts, list) or not isinstance(contexts, list):
        return []

    expanded = []
    for concept in concepts:
        if not isinstance(concept, dict):
            continue
        for context in contexts:
            if not isinstance(context, dict):
                continue
            expanded.append(build_expanded_note(concept, context))
    return expanded


def build_expanded_note(concept, context):
    approach = str(concept.get("approach", "")).strip()
    author = str(concept.get("author", approach or "Psicologia")).strip()
    concept_name = str(concept.get("concept", "")).strip()
    context_name = str(context.get("name", "")).strip()
    concept_note = str(concept.get("note", "")).strip()
    context_note = str(context.get("note", "")).strip()
    concept_question = str(concept.get("question", "")).strip()
    context_question = str(context.get("question", "")).strip()
    keywords = []
    concept_keywords = concept.get("keywords", [])
    context_keywords = context.get("keywords", [])
    for source in (concept_keywords, context_keywords):
        if isinstance(source, list):
            keywords.extend(str(item) for item in source)

    return {
        "author": author,
        "approach": approach,
        "concept": f"{concept_name} / {context_name}".strip(" /"),
        "keywords": keywords,
        "conceptKeywords": concept_keywords if isinstance(concept_keywords, list) else [],
        "contextKeywords": context_keywords if isinstance(context_keywords, list) else [],
        "note": f"{concept_note} Neste contexto, {context_note}".strip(),
        "question": f"{concept_question} {context_question}".strip(),
    }


def save_conversation(session_id, history):
    DATA_DIR.mkdir(exist_ok=True)
    conversations = load_all_conversations()
    conversations[session_id] = history[-40:]
    CONVERSATIONS_FILE.write_text(json.dumps(conversations, ensure_ascii=False, indent=2), encoding="utf-8")


def round_probabilities(probas):
    return {str(key): round(float(value), 3) for key, value in probas.items()}


def tokenize(text):
    return re.findall(r"\b[a-z0-9]{3,}\b", normalize_text(text))


def similarity(left, right):
    return SequenceMatcher(None, left, right).ratio()


def fuzzy_word_match(token, target):
    if abs(len(token) - len(target)) > 3:
        return False

    if len(target) <= 4:
        threshold = 0.94
    elif len(target) <= 6:
        threshold = 0.88
    else:
        threshold = 0.84
    return similarity(token, target) >= threshold


def fuzzy_phrase_match(text, phrase):
    phrase_tokens = tokenize(phrase)
    if not phrase_tokens:
        return False

    text_tokens = tokenize(text)
    phrase_size = len(phrase_tokens)
    if phrase_size == 1:
        target = phrase_tokens[0]
        return any(fuzzy_word_match(token, target) for token in text_tokens)

    for index in range(0, len(text_tokens) - phrase_size + 1):
        window = " ".join(text_tokens[index:index + phrase_size])
        target = " ".join(phrase_tokens)
        if similarity(window, target) >= 0.84:
            return True

    return False


def count_matches(text, words):
    total = 0
    for word in words:
        normalized_word = normalize_text(word)
        if normalized_word in text:
            total += 1
            continue
        if fuzzy_phrase_match(text, normalized_word):
            total += 1
    return total


def has_crisis_signal(text):
    normalized = normalize_text(text)
    return any(word in normalized for word in CRISIS_WORDS)


def analyze_message(message):
    normalized = normalize_text(message)
    scores = {
        emotion: round(count_matches(normalized, config["words"]) * config["weight"], 2)
        for emotion, config in EMOTION_LEXICON.items()
    }
    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    primary = ranked[0][0] if ranked and ranked[0][1] > 0 else None
    secondary = ranked[1][0] if len(ranked) > 1 and ranked[1][1] > 0 else None

    high = count_matches(normalized, INTENSITY_HIGH)
    low = count_matches(normalized, INTENSITY_LOW)
    exclamations = min(message.count("!"), 3)
    length_boost = 1 if len(message) > 180 else 0
    intensity = max(1, min(10, 3 + high * 2 + exclamations + length_boost - low))

    signals = {
        signal: count_matches(normalized, words) > 0
        for signal, words in CONTEXT_SIGNALS.items()
    }
    topics = detect_topics(normalized)
    intent = detect_intent(normalized)
    key_phrase = extract_key_phrase(message)
    psychoanalytic = detect_psychoanalytic_lenses(normalized, topics, primary, secondary)
    psychoanalytic_note = find_psychoanalytic_note(normalized, psychoanalytic)

    return {
        "primaryMood": primary,
        "secondaryMood": secondary,
        "intensity": intensity,
        "signals": signals,
        "scores": scores,
        "topics": topics,
        "intent": intent,
        "keyPhrase": key_phrase,
        "psychoanalytic": psychoanalytic,
        "psychoanalyticNote": psychoanalytic_note,
        "isShort": len(normalized.split()) <= 4,
        "provider": "local",
    }


def compose_reply(message, history):
    if has_crisis_signal(message):
        return (
            "Eu sinto muito que esteja nesse ponto. Se houver risco de voce se machucar, procure ajuda imediata agora: ligue para a emergencia local ou chame alguem de confianca para ficar com voce.\n\n"
            "No Brasil, o CVV atende pelo 188. Enquanto isso, afaste objetos que possam te machucar e me responda so: voce esta em seguranca neste momento?",
            {"crisis": True},
        )

    analysis = analyze_message(message)
    analysis["provider"] = "local"
    dominant_history_mood = get_dominant_history_mood(history)
    support_mode = detect_support_mode(normalize_text(message))
    previous_context = get_previous_context(history)

    if support_mode:
        reply = compose_support_mode_reply(support_mode, previous_context, analysis)
        analysis["supportMode"] = support_mode
        return reply, analysis

    if should_continue_previous_thread(analysis, dominant_history_mood, previous_context):
        analysis["primaryMood"] = analysis["primaryMood"] or dominant_history_mood
        analysis["secondaryMood"] = analysis["secondaryMood"] or previous_context.get("secondaryMood")
        analysis["topics"] = analysis["topics"] or previous_context.get("topics", [])
        analysis["continuedThread"] = True

    mood = analysis["primaryMood"] or dominant_history_mood

    parts = [build_specific_opening(message, analysis)]
    context_line = build_context_line(analysis)
    if context_line:
        parts.append(context_line)
    psychoanalytic_line = build_psychoanalytic_line(analysis)
    if psychoanalytic_line:
        parts.append(psychoanalytic_line)
    parts.append(build_next_step(analysis, mood, history))

    return "\n\n".join(parts), analysis


def detect_topics(normalized):
    topics = [
        topic
        for topic, words in TOPIC_LEXICON.items()
        if count_matches(normalized, words) > 0
    ]
    return topics[:3]


def detect_intent(normalized):
    for intent, words in INTENT_LEXICON.items():
        if count_matches(normalized, words) > 0:
            return intent
    return "perceber"


def detect_support_mode(normalized):
    for mode, words in SUPPORT_MODE_WORDS.items():
        if count_matches(normalized, words) > 0:
            return mode
    return None


def detect_psychoanalytic_lenses(normalized, topics, primary, secondary):
    scores = {
        name: count_matches(normalized, config["words"])
        for name, config in PSYCHOANALYTIC_LENSES.items()
    }

    if "familia" in topics or primary in ("culpa", "vergonha") or secondary in ("culpa", "vergonha"):
        scores["freudiana"] += 1
    if primary in ("autoestima", "ciume", "solidao") or secondary in ("autoestima", "ciume", "solidao"):
        scores["freudiana"] += 1
    if primary in ("confusao", "vergonha") or secondary in ("confusao", "vergonha"):
        scores["junguiana"] += 1
    if count_matches(normalized, ["pareco", "finjo", "mascara", "nao sou eu", "quem eu sou"]) > 0:
        scores["junguiana"] += 1

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    active = [
        {
            "lens": name,
            "score": score,
            "question": choose_variant(PSYCHOANALYTIC_LENSES[name]["questions"], normalized),
        }
        for name, score in ranked
        if score > 0
    ]
    return active[:2]


def find_psychoanalytic_note(normalized, lenses):
    notes = load_psychoanalytic_notes()
    if not notes:
        return None

    active_lenses = {item["lens"] for item in lenses}
    ranked = []
    for note in notes:
        author = normalize_text(str(note.get("author", "")))
        concept = normalize_text(str(note.get("concept", "")))
        concept_keywords = note.get("conceptKeywords", note.get("keywords", []))
        context_keywords = note.get("contextKeywords", [])
        if not isinstance(concept_keywords, list):
            concept_keywords = []
        if not isinstance(context_keywords, list):
            context_keywords = []

        score = count_matches(normalized, concept_keywords) * 3
        score += count_matches(normalized, context_keywords)
        if author == "freud" and "freudiana" in active_lenses:
            score += 1
        if author == "jung" and "junguiana" in active_lenses:
            score += 1
        if concept and concept in normalized:
            score += 1

        if score > 0:
            ranked.append((score, note))

    if not ranked:
        return None

    selected = sorted(ranked, key=lambda item: item[0], reverse=True)[0][1]
    return {
        "author": selected.get("author"),
        "approach": selected.get("approach"),
        "concept": selected.get("concept"),
        "note": selected.get("note"),
        "question": selected.get("question"),
    }


def build_psychoanalytic_line(analysis):
    note = analysis.get("psychoanalyticNote")
    if note and note.get("note"):
        return str(note["note"])

    lenses = analysis.get("psychoanalytic", [])
    if not lenses:
        return ""

    lens_name = lenses[0]["lens"]
    return PSYCHOANALYTIC_LENSES[lens_name]["line"]


def extract_key_phrase(message):
    cleaned = " ".join(message.replace("\n", " ").split())
    clauses = re.split(r"[.!?;]|, mas |, porque | porque | e eu | que eu ", cleaned, flags=re.IGNORECASE)
    candidates = [clause.strip(" ,") for clause in clauses if len(clause.strip()) >= 12]
    if not candidates:
        return cleaned[:90].strip()

    def score(clause):
        normalized = normalize_text(clause)
        words = [word for word in re.findall(r"\b[\wÀ-ÿ]{3,}\b", normalized) if word not in STOPWORDS]
        emotion_hits = sum(count_matches(normalized, config["words"]) for config in EMOTION_LEXICON.values())
        topic_hits = sum(count_matches(normalized, words) for words in TOPIC_LEXICON.values())
        return len(words) + emotion_hits * 3 + topic_hits * 2

    phrase = max(candidates, key=score)
    return phrase[:110].strip()


def get_previous_context(history):
    for item in reversed(history[-10:]):
        if item.get("sender") != "user":
            continue

        text = str(item.get("text", "")).strip()
        if not text:
            continue

        analysis = analyze_message(text)
        if analysis["primaryMood"] or analysis["topics"] or len(text.split()) > 3:
            return {
                "text": text,
                "primaryMood": analysis["primaryMood"],
                "secondaryMood": analysis["secondaryMood"],
                "topics": analysis["topics"],
                "keyPhrase": analysis["keyPhrase"],
            }

    return {}


def should_continue_previous_thread(analysis, dominant_history_mood, previous_context):
    if not previous_context or not analysis["isShort"]:
        return False
    if analysis["primaryMood"] or dominant_history_mood:
        return True
    return bool(previous_context.get("primaryMood") or previous_context.get("topics"))


def compose_support_mode_reply(mode, previous_context, analysis):
    mood = previous_context.get("primaryMood") or analysis["primaryMood"] or "isso"
    phrase = previous_context.get("keyPhrase") or previous_context.get("text")

    if mode == "acolhimento":
        question_key = "perda" if phrase and "companh" in normalize_text(phrase) else "acolhimento"
        if phrase:
            if question_key == "perda":
                bridge = choose_variant(
                    [
                        f"faz sentido que {mood} pese: perder uma companhia mexe com rotina, presenca e pertencimento.",
                        f"quando uma companhia falta, {mood} pode aparecer como saudade, vazio e desorientacao ao mesmo tempo.",
                        f"essa falta nao e pequena; companhia tambem organiza dias, gestos e sensacao de mundo.",
                    ],
                    phrase,
                )
            else:
                bridge = choose_variant(
                    [
                        f"faz sentido que {mood} pese. Eu nao vou tentar reduzir isso a uma solucao rapida.",
                        f"da para ficar um pouco com {mood} sem transformar tudo em tarefa.",
                        f"talvez o mais honesto agora seja acolher {mood} antes de procurar explicacao.",
                    ],
                    phrase,
                )
            return (
                f"{choose_variant(['Ta. Vou ficar no acolhimento, sem correr para resolver.', 'Certo. Vou diminuir o ritmo e ficar mais perto da dor.', 'Vamos deixar a solucao esperar um pouco.'], phrase)} "
                f"Quando voce fala de \"{phrase}\", "
                f"{bridge}\n\n"
                f"{choose_variant(['Por enquanto, voce nao precisa transformar isso em plano. Pode so deixar a dor ter nome aqui.', 'Agora nao precisa fechar conclusao. Basta deixar esse ponto existir com algum cuidado.', 'Nao vou puxar voce para desempenho emocional; vamos so dar lugar para o que apareceu.'], phrase)}\n\n"
                f"{choose_variant(QUESTION_VARIANTS[question_key], phrase)}"
            )

        return (
            f"{choose_variant(['Ta. Vou ficar no acolhimento, sem tentar resolver rapido.', 'Certo. Vou responder mais como presenca do que como plano.', 'Vamos com calma; nao precisa organizar tudo agora.'], mood)}\n\n"
            f"{choose_variant(['O que voce esta sentindo nao precisa estar organizado perfeitamente para ser valido.', 'Mesmo meio confuso, isso ja merece cuidado.', 'Voce nao precisa formular bonito para ser levado a serio aqui.'], mood)}\n\n"
            f"{choose_variant(QUESTION_VARIANTS['acolhimento'], mood)}"
        )

    if mode == "clareza":
        return (
            f"{choose_variant(['Vamos por clareza: uma parte e o fato, outra e o sentimento, outra e a necessidade.', 'Vamos separar em camadas para isso parar de virar um bloco so.', 'Clareza aqui pode ser pequena: nomear fato, emocao e necessidade.'], mood)}\n\n"
            f"{choose_variant([f'Pelo fio da conversa, o sentimento mais forte parece {mood}.', f'O centro emocional parece estar em {mood}.', f'A palavra que mais aparece como eixo e {mood}.'], mood)} "
            f"{choose_variant(['A necessidade talvez seja presenca, seguranca ou reconhecimento.', 'Talvez exista um pedido por presenca, seguranca ou limite.', 'Pode haver uma necessidade simples escondida dentro de uma emocao grande.'], mood)}\n\n"
            f"{choose_variant(['Qual dessas tres palavras chega mais perto: presenca, seguranca ou reconhecimento?', 'Se voce tivesse que escolher uma necessidade agora, seria apoio, seguranca ou espaco?', 'O que parece mais verdadeiro: quero ser visto, quero me sentir seguro, ou quero parar de carregar isso sozinho?'], mood)}"
        )

    return (
        f"{choose_variant(['Vamos fazer um plano pequeno, sem fingir que isso resolve tudo.', 'Vamos montar algo bem menor que o problema inteiro.', 'Da para agir em escala pequena, sem prometer milagre.'], mood)}\n\n"
        f"{choose_variant(['Primeiro: cuidar do corpo por alguns minutos. Segundo: nomear exatamente o que doeu. Terceiro: escolher uma pessoa, lugar ou gesto que reduza 1% da sensacao de estar sozinho.', 'Um roteiro possivel: regular o corpo, escrever a frase central, escolher uma ponte minima com o mundo.', 'Pense em tres gestos: respirar, nomear, aproximar. Pequenos mesmo.'], mood)}\n\n"
        f"{choose_variant(['Qual desses tres passos cabe agora?', 'Qual gesto parece pequeno o bastante para comecar?', 'Se fosse para reduzir so 1% disso, por onde voce comecaria?'], mood)}"
    )


def get_dominant_history_mood(history):
    counts = {}
    for item in history[-8:]:
        text = str(item.get("text", ""))
        if item.get("sender") == "user" and text:
            mood = analyze_message(text)["primaryMood"]
            if mood:
                counts[mood] = counts.get(mood, 0) + 1

    if not counts:
        return None

    return sorted(counts.items(), key=lambda item: item[1], reverse=True)[0][0]


def build_empathy(analysis):
    primary = analysis["primaryMood"]
    secondary = analysis["secondaryMood"]

    if not primary:
        return choose_variant(EMPATHY_VARIANTS["unknown"], analysis.get("keyPhrase", ""))

    secondary_text = f" com um pouco de {secondary}" if secondary else ""
    if analysis["intensity"] >= 8:
        intensity = "bem intenso"
    elif analysis["intensity"] >= 6:
        intensity = "forte"
    else:
        intensity = "presente"

    return choose_variant(
        EMPATHY_VARIANTS["mood"],
        f"{primary}:{secondary}:{analysis.get('keyPhrase', '')}",
    ).format(primary=primary, secondary=secondary_text, intensity=intensity)


def build_specific_opening(message, analysis):
    empathy = build_empathy(analysis)
    key_phrase = analysis.get("keyPhrase")
    topics = analysis.get("topics", [])

    if analysis.get("continuedThread"):
        return f"{choose_variant(CONTINUATION_VARIANTS, message)} {empathy}"

    if key_phrase and len(key_phrase) >= 12:
        connector = choose_variant(
            [
                f"Voce trouxe \"{key_phrase}\".",
                f"A frase que fica em destaque e \"{key_phrase}\".",
                f"O ponto mais vivo parece ser \"{key_phrase}\".",
                f"Vou partir dessa parte: \"{key_phrase}\".",
            ],
            key_phrase,
        )
        return f"{choose_variant(OPENING_VARIANTS, key_phrase)} {connector} {empathy}"

    if topics:
        topic_text = join_words(topics)
        return f"Pelo que voce trouxe, o centro parece ser {topic_text}. {empathy}"

    return empathy


def build_context_line(analysis):
    primary = analysis["primaryMood"]
    topics = analysis.get("topics", [])
    intent = analysis.get("intent")

    if analysis.get("continuedThread"):
        return choose_variant(
            [
                "Como voce esta respondendo em partes curtas, vou manter o contexto anterior em vez de tratar cada frase como um assunto novo.",
                "Vou considerar isso como continuacao do mesmo fio, porque frases curtas tambem carregam contexto.",
                "Nao vou isolar essa resposta; ela parece ligada ao que veio antes.",
            ],
            analysis.get("keyPhrase", ""),
        )

    if intent in INTENT_CONTEXT_VARIANTS:
        return choose_variant(INTENT_CONTEXT_VARIANTS[intent], analysis.get("keyPhrase", ""))

    for topic in ("trabalho", "relacionamento", "familia", "corpo"):
        if topic in topics:
            return choose_variant(TOPIC_CONTEXT_VARIANTS[topic], analysis.get("keyPhrase", ""))

    if primary in MOOD_CONTEXT_LINES:
        return choose_variant(MOOD_CONTEXT_LINES[primary], analysis.get("keyPhrase", ""))

    signals = analysis["signals"]
    if signals["relationship"]:
        return choose_variant(
            [
                "Quando envolve gente proxima, a emocao costuma vir misturada com necessidade de vinculo, limite ou reconhecimento.",
                "Com pessoas importantes, a dor raramente e so sobre o fato; tambem toca pertencimento.",
                "Vinculos proximos mexem com limite, cuidado e medo de nao ser considerado.",
            ],
            analysis.get("keyPhrase", ""),
        )
    if signals["work"]:
        return choose_variant(TOPIC_CONTEXT_VARIANTS["trabalho"], analysis.get("keyPhrase", ""))
    if signals["body"]:
        return choose_variant(TOPIC_CONTEXT_VARIANTS["corpo"], analysis.get("keyPhrase", ""))
    if signals["isolation"]:
        return choose_variant(MOOD_CONTEXT_LINES["solidao"], analysis.get("keyPhrase", ""))
    if signals["self_image"]:
        return choose_variant(MOOD_CONTEXT_LINES["autoestima"], analysis.get("keyPhrase", ""))
    if signals["future"]:
        return choose_variant(
            [
                "Quando o futuro fica nebuloso, o melhor ponto de apoio costuma ser o proximo gesto concreto.",
                "Se o futuro ficou grande demais, talvez o foco precise voltar para a proxima hora.",
                "Futuro incerto pede um passo pequeno, nao uma previsao perfeita.",
            ],
            analysis.get("keyPhrase", ""),
        )

    return choose_variant(
        [
            "Vou responder pelo que aparece agora, sem tentar fechar diagnostico sobre voce.",
            "Vou ficar no que da para perceber daqui, sem forcar uma conclusao sobre voce.",
            "A leitura ainda e parcial, entao vou tratar isso como pista, nao como rotulo.",
        ],
        analysis.get("keyPhrase", ""),
    )


def build_next_step(analysis, mood, history):
    tool = get_tool_text(mood, analysis)
    key_phrase = normalize_text(analysis.get("keyPhrase", ""))

    if "companh" in key_phrase or "copanh" in key_phrase:
        question = choose_variant(QUESTION_VARIANTS["perda"], key_phrase)
        return f"{tool}\n\n{question}"

    if analysis.get("continuedThread") and ("frustr" in key_phrase or mood == "raiva"):
        question = choose_variant(QUESTION_VARIANTS["frustracao"], key_phrase)
        return f"{tool}\n\n{question}"

    if analysis.get("continuedThread") and mood in ("tristeza", "solidao", "luto"):
        question = choose_variant(QUESTION_VARIANTS["acolhimento"], key_phrase)
        return f"{tool}\n\n{question}"

    repeated_mood = repeated_user_mood_count(history, mood) >= 2
    if repeated_mood and mood:
        if analysis.get("continuedThread"):
            question = choose_variant(QUESTION_VARIANTS["frustracao"], analysis.get("keyPhrase", ""))
            return f"{tool}\n\n{question}"
        return f"{tool}\n\nPercebo que {mood} apareceu algumas vezes. O que costuma acontecer logo antes desse sentimento subir?"

    psychoanalytic_lenses = analysis.get("psychoanalytic", [])
    psychoanalytic_note = analysis.get("psychoanalyticNote")
    if psychoanalytic_note and psychoanalytic_note.get("question"):
        question = psychoanalytic_note["question"]
        return f"{tool}\n\n{question}"
    if psychoanalytic_lenses:
        question = psychoanalytic_lenses[0]["question"]
        return f"{tool}\n\n{question}"

    intent = analysis.get("intent")
    topics = analysis.get("topics", [])

    if analysis["intensity"] >= 8:
        question = "Antes de continuar: voce esta seguro agora?"
    elif intent == "conselho":
        question = "Se voce quiser agir hoje, qual acao teria menos risco e mais clareza?"
    elif intent == "decisao":
        question = "Quais sao as duas opcoes reais, e qual delas voce escolheria se o medo baixasse 20%?"
    elif intent == "conflito":
        question = "Qual frase voce gostaria de dizer sem atacar e sem engolir o que sente?"
    elif intent == "ruminacao":
        question = "Qual pensamento esta repetindo mais: uma previsao, uma culpa ou uma cena?"
    elif "trabalho" in topics:
        question = "O que e responsabilidade sua aqui, e o que pertence ao ambiente ou a outra pessoa?"
    elif "relacionamento" in topics:
        question = "O que voce sabe de fato, e o que sua mente esta tentando completar sozinha?"
    elif "familia" in topics:
        question = "Isso parece uma dor de agora, uma dor antiga, ou as duas coisas juntas?"
    elif "corpo" in topics:
        question = "De 0 a 10, quanto seu corpo esta ativado neste momento?"
    else:
        question = choose_variant(
            MICRO_QUESTIONS,
            f"{analysis.get('keyPhrase', '')}:{len(history)}:{analysis['intensity']}",
        )

    return f"{tool}\n\n{question}"


def get_tool_text(mood, analysis):
    options = TOOL_VARIANTS.get(mood)
    if not options and mood in EMOTION_LEXICON:
        options = [EMOTION_LEXICON[mood]["tool"]]
    if not options:
        options = TOOL_VARIANTS["default"]
    return choose_variant(options, f"{mood}:{analysis.get('keyPhrase', '')}")


def join_words(words):
    if len(words) == 1:
        return words[0]
    if len(words) == 2:
        return f"{words[0]} e {words[1]}"
    return f"{', '.join(words[:-1])} e {words[-1]}"


def choose_variant(options, seed_text):
    if not options:
        return ""
    return options[rotating_index(options, seed_text)]


def rotating_index(options, seed_text, window_seconds=2):
    text_seed = sum(ord(char) for char in str(seed_text))
    time_seed = int(time.time() / window_seconds)
    return (text_seed + time_seed) % len(options)


def repeated_user_mood_count(history, mood):
    if not mood:
        return 0

    count = 0
    for item in history[-6:]:
        if item.get("sender") != "user":
            continue
        if analyze_message(str(item.get("text", "")))["primaryMood"] == mood:
            count += 1

    return count


def is_port_unavailable_error(error):
    return error.errno in (13, 98) or getattr(error, "winerror", None) == 10013


def open_browser(url):
    if os.getenv("AURORA_NO_BROWSER", "0") == "1":
        return
    try:
        webbrowser.open(url)
    except Exception as error:
        print(f"Nao foi possivel abrir o navegador automaticamente: {error}")


if __name__ == "__main__":
    server = None
    selected_port = PORT
    for candidate_port in range(PORT, PORT + 20):
        try:
            server = ThreadingHTTPServer(("localhost", candidate_port), EmotionalChatHandler)
            selected_port = candidate_port
            break
        except OSError as error:
            if not is_port_unavailable_error(error):
                raise
    if server is None:
        raise OSError(f"Nenhuma porta livre encontrada entre {PORT} e {PORT + 19}.")

    url = f"http://localhost:{selected_port}"
    print(f"Aurora Python rodando em {url}")
    open_browser(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nAurora encerrado.")
    finally:
        server.server_close()
