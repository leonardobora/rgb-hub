# rgb-hub: Integração Alexa + TV LG — Design

Data: 2026-08-01
Status: Aprovado (brainstorming)

## Objetivo

Estender o rgb-hub para ser controlado por voz via Alexa e integrar a
smart TV LG (webOS 4.5+) ao ecossistema. Escopo escolhido: **integração
primeiro** (compras de hardware ficam pra depois).

## Contexto atual

- rgb-hub: controle local (protocolo Tuya) de 2 dispositivos — fita
  Monster (`fita`) e lâmpada Elgin (`quarto`) — via `lights.py`
  (`LightHub`), `cli.py`, `scenes.py` (cenas `gaming`, `foco`,
  `alerta`), `reactive.py`, `tray.py`.
- Nomes de voz reutilizam os aliases de `aliases.json` (`fita`,
  `quarto`).
- Hardware: Echo Dot, TV LG webOS 4.5+, PC com Windows rodando o hub.
- **Restrição chave**: o PC desliga com frequência e não existe outro
  dispositivo sempre ligado. Nada que dependa do hub funciona com o PC
  desligado.

## Abordagem escolhida (C)

Oficiais primeiro, skill custom por último:

1. **Luzes por voz** — skill oficial **Smart Life** na Alexa (nuvem
   Tuya, funciona sem o PC).
2. **TV por voz** — skill oficial **LG ThinQ** na Alexa (nuvem LG,
   funciona sem o PC). Cobre on/off/volume/input.
3. **Skill custom** (este projeto) — para o que as oficiais não cobrem:
   cenas do hub, cor/brilho por voz, disparar sync, disparar
   screenshare. Backend = hub local exposto por túnel.
4. **Screenshare** — script Windows para espelhar a tela do PC na TV.

## Arquitetura

```
Alexa (Echo Dot)
├── skill Smart Life (oficial) ──→ luzes via nuvem Tuya   [sem PC]
├── skill LG ThinQ (oficial) ────→ TV via nuvem LG        [sem PC]
└── skill custom "rgb-hub" ──→ Lambda (fino) ──→ túnel cloudflared ──→ server.py no PC
         ├── cenas (gaming/foco/alerta)
         ├── cor/brilho por luz
         ├── disparar sync screen/audio
         └── disparar screenshare
```

### Componentes novos no rgb-hub

1. **`server.py`** — API HTTP local (FastAPI) que expõe o `LightHub`:
   - `POST /scene` `{name}`
   - `POST /color` `{name, hex}`
   - `POST /brightness` `{name, pct}`
   - `POST /sync` `{mode: screen|audio}`
   - `POST /screenshare`
    - `POST /tv` `{action: on|off|volume, value?}` (controle local
      webOS via `aiowebostv`)
   - Erros: JSON `{error: "<mensagem amigável>"}` com status adequado.
2. **Skill custom** no Alexa Developer Console (ASK):
   - `SceneIntent` (slot `cena`) → `POST /scene`
   - `ColorIntent` (slot `luz`, `cor`) → `POST /color`
   - `BrightnessIntent` (slot `luz`, `pct`) → `POST /brightness`
   - `SyncIntent` (slot `modo`) → `POST /sync`
   - `ScreenshareIntent` → `POST /screenshare`
   - Backend fino (Lambda): valida slots, mapeia cor nome→hex,
     encaminha pro túnel, traduz resposta/erro em fala.
   - Slots fora da lista válida (luz inexistente, cena inexistente) →
     a skill responde com as opções válidas.
3. **Túnel** — `cloudflared` (uso pessoal) expondo a porta do
   `server.py` como HTTPS estável pra Alexa.
4. **`screenshare.py`** — dispara o espelhamento de tela do PC → TV LG
   via Miracast (`ms-settings:connecteddevices` / API Miracast), ligando
   a TV e ajustando o input antes, quando necessário.

## Fluxo de uma fala

```
"Alexa, cena gaming"
  → Alexa → skill rgb-hub (Lambda) → HTTPS → cloudflared → server.py no PC
  → server.py chama apply_scene("gaming") → luzes mudam
  → resposta de volta: "Cena gaming aplicada."
```

## Automações PC ↔ TV

- `POST /tv` controla on/off/volume/input da TV via `aiowebostv`
  (controle local, independente da nuvem).
- Screenshare espelha o monitor primário na TV (ex: jogar no sofá).
- Cenas do hub não controlam a TV nesta versão (fica para evolução).

## Tratamento de erros

- **PC desligado**: Alexa responde "dispositivo indisponível" (mecanismo
  padrão). Aceito.
- **Luz/TV fora de alcance**: JSON de erro com mensagem amigável → Alexa
  lê a mensagem.
- **Túnel caiu**: Lambda devolve erro 502 → skill diz "O hub está
  offline, tente novamente quando o PC estiver ligado".
- **Validação de slots**: valores fora da lista → skill enumera opções.

## Testes

- **Unit**: endpoints do `server.py` com `LightHub` mock; validação de
  slots; mapeamento de cores nome→hex.
- **Integração real**: manual, com as luzes de verdade (padrão do
  projeto — protocolo Tuya não é simulável sem local_key real).

## Configuração manual (não é código deste projeto)

1. Habilitar skill **Smart Life** no app Alexa.
2. Habilitar skill **LG ThinQ** no app Alexa e vincular a conta LG.

## Fora de escopo (futuro)

- Compras de hardware / novas lâmpadas e itens IoT.
- Skill com intents além das listadas (ex: TV nas cenas, rotinas
  complexas, perguntas/respostas).
- Home Assistant como central.
- Substituição do firmware Tuya (tuya-cloudcutter / Tasmota).
