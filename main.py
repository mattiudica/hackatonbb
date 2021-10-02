# -*- coding: utf-8 -*-
import inspect
import argparse
import logging
from datetime import datetime
from common import config
# 1) Evito importar todo con importlib.
from importlib import import_module
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    inicio = datetime.now()
    parser = argparse.ArgumentParser()
    # 2) El nombre de la Clase ingresada, debe ser igual en config.yaml -> ott_sites
    new_site_choices = list(config()['ott_sites'].keys())
    # 3) Parser de argumentos de la terminal:
    parser.add_argument('--c', help = 'País para Scrapear', type=str)
    parser.add_argument('--o', help = 'Operación', type=str)
    parser.add_argument('ott_site', help = 'Sitios Para Scrapear', type=str, choices=new_site_choices)

    args = parser.parse_args()

    ott_site_country = args.c
    ott_operation    = args.o
    ott_platforms    = args.ott_site

    # 4) Indico en formato "string", el nombre del módulo a importar.
    module = None
    module = 'platforms.' + ott_platforms.lower()

    # 5) Valido si aún el script pertenece a un "3rd-party".
    # Ej: 'platforms.reelgood_v3'
    tp_sites = list(config()['tp_sites'].items())
    for tp, ott in tp_sites:
        if ott_platforms in ott:
            module = 'platforms.' + tp
            break

    status_code = 0
    # 6) Obtengo el módulo a importar:
    MODULE_NAME = module
    try:
        # 7) Importo el módulo correcto.
        module = import_module(MODULE_NAME)

        # 8) Hago la instancia de la Clase. La clase == ott_platforms
        PlatformClass = getattr(module, ott_platforms)
    except ModuleNotFoundError as exc:
        print(exc)
        print("\n¡¡¡El nombre del archivo y la clase no coinciden!!!\n")
        print(f"Para importar: \"{ott_platforms}\"...")
        print(f"El archivo debe llamarse: \"{ott_platforms.lower()}.py\"")

        ott_operation = 'no operation'
        status_code = 3
    if ott_operation == 'testing':
        _inspected_class = inspect.getfullargspec(PlatformClass)
        args_class = _inspected_class.args
        PlatformClass(ott_platforms, ott_site_country, ott_operation)

    fin = datetime.now()

    print('Tiempo transcurrido:', fin - inicio)
    exit(status_code)