# Chat Bot Emocional

Chatbot emocional local, leve e sem API externa. O backend usa apenas Python puro:

- sem chave;
- sem Ollama;
- sem Transformers;
- sem downloads grandes;
- sem dependencias externas.

## Rodar

```bash
python3 backend.py
```

Abra no navegador:

```txt
http://localhost:5000
```

Tambem da para abrir `index.html` direto, mas o melhor modo e pelo endereco acima, porque assim o navegador usa o backend Python e a persistencia em `data/conversations.json`.

Na primeira tela, crie uma conta local. Os usuarios ficam em `data/users.json` com senha hasheada por PBKDF2. As sessoes ficam em memoria e expiram em 7 dias; ao reiniciar o backend, faca login novamente.

## Compilar

Linux:

```bash
./build_linux.sh
./dist/aurora-chat
```

Windows:

```bat
build_windows.bat
dist\aurora-chat.exe
```

O executavel serve o app em:

```txt
http://localhost:5000
```

Se a porta 5000 ja estiver ocupada, ele tenta automaticamente as proximas portas ate 5019. Veja a porta impressa no terminal, por exemplo `http://localhost:5001`.

Ao iniciar, o executavel tenta abrir o navegador automaticamente. Para desativar isso:

```bash
AURORA_NO_BROWSER=1 ./dist/aurora-chat
```

Observacao: gere o `.exe` em uma maquina Windows. O PyInstaller normalmente nao faz cross-compile confiavel de Linux para Windows.

## Como funciona

O `backend.py` usa um motor local de regras com memoria curta:

- detecta emocao principal e secundaria por lexico;
- usa `difflib` para tolerar erros pequenos de escrita;
- estima intensidade;
- identifica temas como trabalho, familia, relacionamento, corpo, futuro e isolamento;
- usa lentes inspiradas em psicanalise, psicologia analitica, TCC, DBT, ACT, humanista, Gestalt, sistemica, apego e mindfulness;
- consulta notas locais em `data/psychoanalytic_notes.json`;
- percebe pedidos como acolhimento, clareza e plano;
- continua o fio quando a pessoa responde com frases curtas;
- persiste conversas por usuario e sessao;
- varia abertura, acolhimento, contexto, ferramentas e perguntas para reduzir repeticao.

Condicoes emocionais cobertas: ansiedade, tristeza, raiva, cansaco, alegria, culpa, confusao, vergonha, solidao, estresse, luto, autoestima, ciume e esperanca.

As lentes psicanaliticas sao usadas apenas como apoio de conversa, sem diagnostico: desejo, culpa, defesa, repeticao, sombra, persona, simbolos e sonhos.

As notas sao textos curtos, autorais e parafraseados. O repertorio local usa 50 conceitos combinados com 10 contextos emocionais, gerando 500 notas em memoria. O projeto nao inclui livros completos nem traducoes protegidas por copyright.

## Testar

```bash
python3 -m py_compile backend.py
```

```bash
curl -s -X POST http://localhost:5000/api/register \
  -H 'Content-Type: application/json' \
  -d '{"username":"teste","password":"senha123"}'
```

Use o `token` retornado:

```bash
curl -s -X POST http://localhost:5000/api/chat \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer SEU_TOKEN' \
  -d '{"sessionId":"teste-local","message":"Estou sentindo solidão porque perdi uma companhia e queria acolhimento","history":[]}'
```
