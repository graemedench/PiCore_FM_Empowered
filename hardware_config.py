"""Validated piCorePlayer wiring; BCM numbers, never physical pin numbers."""
import copy
import dataclasses
import json
import re
from pathlib import Path

PATH = Path(__file__).resolve().parents[3] / 'config/hardware.json'
DEFAULTS = {
    'gpiochip': '/dev/gpiochip0',
    'oled': {'enabled': True, 'spi_port': 0, 'spi_device': 0, 'dc': 24, 'rst': 25},
    'rotary': {'enabled': True, 'clk': 13, 'dt': 5, 'sw': 6, 'reverse': True},
    'mcp': {'enabled': True, 'bus': 1, 'addr': 32, 'swap_columns': True, 'led_reverse': True},
    'ir': {'gpio': 4},
    'power': {'gpio': 26},
    'reserved_gpios': [],
}


def validate(config):
    if not re.fullmatch(r'/dev/gpiochip[0-9]+', config['gpiochip']):
        raise ValueError('gpiochip must be /dev/gpiochipN')
    used = {}
    def pin(label, value):
        if type(value) is not int or not 0 <= value <= 27:
            raise ValueError(label + ': use a BCM GPIO from 0 to 27')
        if value in used:
            raise ValueError(f'GPIO{value} conflict: {used[value]} and {label}')
        used[value] = label
    for section in ('oled', 'rotary', 'mcp'):
        if type(config[section]['enabled']) is not bool:
            raise ValueError(section + '.enabled must be true or false')
    for value in config['reserved_gpios']:
        pin('reserved by attached hardware', value)
    if config['oled']['enabled']:
        o = config['oled']
        if o['spi_port'] != 0 or type(o['spi_device']) is not int or o['spi_device'] not in (0, 1):
            raise ValueError('Supported OLED SPI is SPI0, device 0 or 1')
        for label, value in [('SPI MOSI', 10), ('SPI clock', 11), ('SPI chip select', 8 if o['spi_device'] == 0 else 7), ('OLED DC', o['dc']), ('OLED reset', o['rst'])]:
            pin(label, value)
    if config['mcp']['enabled']:
        m = config['mcp']
        if type(m['bus']) is not int or m['bus'] != 1:
            raise ValueError('Supported MCP wiring uses I2C bus 1')
        if type(m['addr']) is not int or not 0x20 <= m['addr'] <= 0x27:
            raise ValueError('MCP address must be 0x20 through 0x27 (32 through 39)')
        pin('I2C SDA', 2)
        pin('I2C SCL', 3)
        for key in ('swap_columns', 'led_reverse'):
            if type(m[key]) is not bool:
                raise ValueError('mcp.' + key + ' must be true or false')
    if config['rotary']['enabled']:
        r = config['rotary']
        if type(r['reverse']) is not bool:
            raise ValueError('rotary.reverse must be true or false')
        for key in ('clk', 'dt', 'sw'):
            if r[key] is not None:
                pin('Encoder ' + key, r[key])
        if r['clk'] is None or r['dt'] is None:
            raise ValueError('Encoder CLK/DT required; disable rotary to omit it')
    for section in ('ir', 'power'):
        if config[section]['gpio'] is not None:
            pin(section, config[section]['gpio'])
    return config


def load(path=PATH, settings_path=None):
    config = copy.deepcopy(DEFAULTS)
    # Keep earlier installations' disabled/remapped shutdown and IR preferences.
    settings_path = Path(settings_path) if settings_path else Path(path).with_name('settings.json')
    try:
        legacy = json.loads(settings_path.read_text())
    except FileNotFoundError:
        legacy = {}
    if 'shutdown_gpio' in legacy.get('power', {}):
        config['power']['gpio'] = legacy['power']['shutdown_gpio']
    if legacy.get('ir', {}).get('enabled') is False:
        config['ir']['gpio'] = None
    try:
        raw = json.loads(Path(path).read_text())
    except FileNotFoundError:
        raw = {}
    return merge(raw, config)


def merge(raw, config=None):
    config = copy.deepcopy(config if config is not None else DEFAULTS)
    if not isinstance(raw, dict):
        raise ValueError('hardware.json must contain an object')
    # Existing Sable hardware.json accepts additional OLED/MCP dataclass fields.
    allowed = {k: set(v) for k, v in DEFAULTS.items() if isinstance(v, dict)}
    allowed['oled'].update(('blank', 'width', 'height'))
    allowed['rotary'].add('long_press_s')
    allowed['mcp'].update(('IODIRA', 'IODIRB', 'GPPUB', 'GPIOA', 'GPIOB', 'OLATA', 'col_settle_s'))
    for key, value in raw.items():
        if key not in config:
            raise ValueError('Unknown hardware setting: ' + key)
        if isinstance(config[key], dict):
            if not isinstance(value, dict) or set(value) - allowed[key]:
                raise ValueError('Unknown or invalid hardware section: ' + key)
            config[key].update(value)
        else:
            config[key] = value
    if not isinstance(config['reserved_gpios'], list):
        raise ValueError('reserved_gpios must be a list of BCM numbers')
    return validate(config)


def mcp_pins(config):
    from ..hardware import Mcp23017
    fields = {f.name for f in dataclasses.fields(Mcp23017)}
    return Mcp23017(**{k: v for k, v in config['mcp'].items() if k in fields})
