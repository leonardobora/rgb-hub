"""Dispara o espelhamento da tela do PC na TV LG.

O Windows nao expoe API publica pra iniciar uma conexao Miracast de
verdade -- abrir o painel 'ms-settings:connecteddevices' e o usuario
clicar na TV e a forma honesta de fazer. Antes disso a gente acorda a
TV (WoL) pra ela aparecer na lista."""
import os


class ScreenshareError(Exception):
    pass


async def start_screenshare(tv, launcher=None):
    if launcher is None:
        launcher = _open_connected_devices
    if tv is not None:
        await tv.set_power(True)
    launcher()
    return {"status": "ok"}


def _open_connected_devices():
    try:
        os.startfile("ms-settings:connecteddevices")
    except (OSError, AttributeError) as exc:
        raise ScreenshareError(
            "Nao consegui abrir o painel de espelhamento do Windows. "
            "Abra em Configuracoes -> Bluetooth e dispositivos -> Adicionar dispositivo."
        ) from exc
