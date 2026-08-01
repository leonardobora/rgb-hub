"""Backend fino da skill Alexa 'rgb-hub' (AWS Lambda).

Recebe o JSON da Alexa, valida os slots contra listas validas, mapeia
cor nome->hex, encaminha pro hub via tunel (HUB_URL) e monta a resposta
em fala. Erros viram mensagens amigaveis em portugues.
"""
import os

import httpx

HUB_URL = os.getenv("HUB_URL", "").rstrip("/")

VALID_LIGHTS = {"fita", "quarto"}
VALID_SCENES = {"gaming", "foco", "alerta"}
VALID_MODES = {"screen", "audio"}
COLORS = {
    "vermelho": "FF0000",
    "verde": "00FF00",
    "azul": "0000FF",
    "amarelo": "FFFF00",
    "branco": "FFFFFF",
    "roxo": "8000FF",
    "rosa": "FF00FF",
    "ciano": "00FFFF",
    "laranja": "FF8000",
}


class SlotError(Exception):
    pass


class HubRemoteError(Exception):
    pass


def handler(event, context):
    request = event.get("request", {})
    if request.get("type") == "IntentRequest":
        return _handle_intent(request["intent"])
    return _speech(
        "O hub de luzes esta pronto. Diga uma cena, cor, brilho, "
        "sincronizacao ou espelhamento."
    )


def _handle_intent(intent):
    name = intent["name"]
    slots = intent.get("slots", {})
    try:
        if name == "SceneIntent":
            return _scene(slots)
        if name == "ColorIntent":
            return _color(slots)
        if name == "BrightnessIntent":
            return _brightness(slots)
        if name == "SyncIntent":
            return _sync(slots)
        if name == "ScreenshareIntent":
            _post("/screenshare", {})
            return _speech("Espelhamento iniciado. Clique na TV na janela que abriu.")
        return _speech(
            "Nao entendi. Tente: cena gaming, cor vermelha na fita, "
            "brilho 50 no quarto, sincronizar tela ou espelhar a tela."
        )
    except HubRemoteError:
        return _speech("O hub esta offline. Tente novamente quando o PC estiver ligado.")
    except SlotError as exc:
        return _speech(str(exc))


def _scene(slots):
    scene = _slot(slots, "cena")
    if scene not in VALID_SCENES:
        raise SlotError(f"Escolha uma cena: {', '.join(sorted(VALID_SCENES))}.")
    _post("/scene", {"name": scene})
    return _speech(f"Cena {scene} aplicada.")


def _color(slots):
    light = _slot(slots, "luz")
    color = _slot(slots, "cor")
    if light not in VALID_LIGHTS:
        raise SlotError(f"Escolha uma luz: {', '.join(sorted(VALID_LIGHTS))}.")
    if color not in COLORS:
        raise SlotError(f"Escolha uma cor: {', '.join(sorted(COLORS))}.")
    _post("/color", {"name": light, "hex": COLORS[color]})
    return _speech(f"Cor definida na {light}.")


def _brightness(slots):
    light = _slot(slots, "luz")
    if light not in VALID_LIGHTS:
        raise SlotError(f"Escolha uma luz: {', '.join(sorted(VALID_LIGHTS))}.")
    try:
        pct = int(_slot(slots, "pct"))
    except ValueError as exc:
        raise SlotError("Diga um valor de 0 a 100, por exemplo, brilho 50 na fita.") from exc
    if not 0 <= pct <= 100:
        raise SlotError("O brilho deve ficar entre 0 e 100.")
    _post("/brightness", {"name": light, "pct": pct})
    return _speech(f"Brilho da {light} ajustado para {pct} por cento.")


def _sync(slots):
    mode = _slot(slots, "modo")
    if mode not in VALID_MODES:
        raise SlotError("Escolha tela ou audio.")
    _post("/sync", {"mode": mode})
    return _speech(f"Sincronizacao de {mode} ligada.")


def _slot(slots, name):
    slot = (slots or {}).get(name, {})
    value = slot.get("value") or ""
    return value


def _post(path, payload):
    if not HUB_URL:
        raise HubRemoteError("HUB_URL nao configurado")
    try:
        resp = httpx.post(f"{HUB_URL}{path}", json=payload, timeout=10)
    except httpx.HTTPError as exc:
        raise HubRemoteError("hub offline") from exc
    if resp.status_code >= 400:
        try:
            detail = resp.json().get("error", "erro desconhecido")
        except ValueError:
            detail = "erro desconhecido"
        raise SlotError(f"O hub respondeu: {detail}.")


def _speech(text):
    return {
        "version": "1.0",
        "response": {
            "outputSpeech": {"type": "PlainText", "text": text},
            "shouldEndSession": True,
        },
    }
