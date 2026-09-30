import parse
from packages.core.config.device_schema import *
import re


def strip_format_width(fmt, value):
    """Форматирует значение, убирая принудительную ширину из формата"""
    stripped_fmt = re.sub(r'^(\d+)', '', fmt)
    return format(value, stripped_fmt)


def ascii_coder(cmd_prefix='', cmd_suffix='', cmd_separator='', enc='ascii', frame_terminator='\r\n',
                address={'value': 1, 'fmt': '02X', 'prefix': '', 'suffix': ''},
                command={'value': 'READ', 'fmt': 's', 'prefix': '', 'suffix': ''},
                params=[{'name': 'A', 'value': 0, 'param_prefix': '', 'param_fmt': '', 'param_space': 5,
                         'param_alignment': 'right', 'param_suffix': '', 'fill_symbol': ' '}]):
    params_parts = []
    for param in params:
        if param['param_space'] != 0:
            if param['param_fmt'] == '':
                param_value_str = str(param['value'])
            else:
                param_value_str = strip_format_width(param['param_fmt'], param['value'])

            fill = param.get('fill_symbol', ' ')

            if param['param_space'] != -1:
                if len(param_value_str) > param['param_space']:
                    if param['param_alignment'] == 'right':
                        param_value_str = param_value_str[-param['param_space']:]
                    elif param['param_alignment'] == 'left':
                        param_value_str = param_value_str[:param['param_space']]
                    else:
                        return {'error': True, 'result': f'Неизвестный вид выравнивания {param["param_alignment"]}'}

                if fill == '': fill = ' '
                if len(param_value_str) < param['param_space']:
                    space = param['param_space'] - len(param_value_str)
                    fill_text = ((space // len(fill) + 1) * fill)[:space]
                    if param['param_alignment'] == 'left':
                        param_value_str = fill_text + param_value_str
                    elif param['param_alignment'] == 'right':
                        param_value_str = param_value_str + fill_text
                    else:
                        return {'error': True, 'result': f'Неизвестный вид выравнивания {param["param_alignment"]}'}
            else:
                pass

            params_parts.append(param['param_prefix'] + param_value_str + param['param_suffix'])

    params_text = cmd_separator.join(params_parts) if cmd_separator else ''.join(params_parts)

    address_text = address['prefix'] + format(address['value'], address['fmt']) + address['suffix']
    command_text = command['prefix'] + format(command['value'], command['fmt']) + command['suffix']

    command = cmd_prefix + address_text + command_text + params_text + cmd_suffix + frame_terminator
    return {'error': False, 'result': command.encode(enc, errors="replace")}


def ascii_decoder(cmd, cmd_prefix='', cmd_suffix='', cmd_separator='', enc='ascii', frame_terminator='\r\n',
                  address={'value': 1, 'fmt': '02X', 'prefix': '', 'suffix': ''},
                  command={'value': 'READ', 'fmt': 's', 'prefix': '', 'suffix': ''},
                  params=[{'name': 'A', 'value': 0, 'param_prefix': '', 'param_fmt': '', 'param_space': 5,
                           'param_alignment': 'right', 'param_suffix': '', 'fill_symbol': ' '}]):
    # Декодируем bytes в строку если нужно
    if isinstance(cmd, bytes):
        cmd = cmd.decode(enc, errors="replace")

    # Убираем terminator
    if frame_terminator and cmd.endswith(frame_terminator):
        cmd = cmd[:-len(frame_terminator)]

    # Убираем prefix и suffix
    if cmd_prefix and cmd.startswith(cmd_prefix):
        cmd = cmd[len(cmd_prefix):]
    if cmd_suffix and cmd.endswith(cmd_suffix):
        cmd = cmd[:-len(cmd_suffix)]

    # Формируем address и command части как в кодере
    try:
        address_text = address['prefix'] + format(address['value'], address['fmt']) + address['suffix']
    except (ValueError, KeyError):
        address_text = address.get('prefix', '') + str(address.get('value', '')) + address.get('suffix', '')

    try:
        command_text = command['prefix'] + format(command['value'], command['fmt']) + command['suffix']
    except (ValueError, KeyError):
        command_text = command.get('prefix', '') + str(command.get('value', '')) + command.get('suffix', '')

    header = address_text + command_text

    # Проверяем, начинается ли cmd с header
    if not cmd.startswith(header):
        return {'error': True, 'result': f'Команда не соответствует ожидаемому формату. Ожидался header: {header}',
                'raw': cmd}

    # Извлекаем часть с параметрами
    params_text = cmd[len(header):]

    # Если нет параметров, возвращаем пустой результат
    if not params:
        return {'error': False, 'result': {}, 'raw': cmd}

    parsed = {}
    remaining = params_text

    for i, param in enumerate(params):
        # Пропускаем param_prefix
        if param.get('param_prefix') and remaining.startswith(param['param_prefix']):
            remaining = remaining[len(param['param_prefix']):]

        param_space = param.get('param_space', 0)

        if param_space > 0:
            # Извлекаем значение фиксированной длины
            if len(remaining) < param_space:
                val = remaining
                remaining = ''
            else:
                val = remaining[:param_space]
                remaining = remaining[param_space:]

            # Убираем param_suffix
            if param.get('param_suffix') and remaining.startswith(param['param_suffix']):
                remaining = remaining[len(param['param_suffix']):]

            # Убираем разделитель между параметрами
            if cmd_separator and i < len(params) - 1 and remaining.startswith(cmd_separator):
                remaining = remaining[len(cmd_separator):]

            # Очищаем значение от fill_symbol
            fill_symbol = param.get('fill_symbol', ' ')
            val = val.strip(fill_symbol)

            # Пробуем конвертировать в число
            try:
                if '.' in val:
                    parsed[param['name']] = float(val)
                elif val:
                    parsed[param['name']] = int(val)
                else:
                    parsed[param['name']] = val
            except ValueError:
                parsed[param['name']] = val
        else:
            # Если param_space == 0, параметр не имеет фиксированной длины
            # Ищем следующий разделитель или конец строки
            if cmd_separator and i < len(params) - 1:
                sep_pos = remaining.find(cmd_separator)
                if sep_pos != -1:
                    val = remaining[:sep_pos]
                    remaining = remaining[sep_pos + len(cmd_separator):]
                else:
                    val = remaining
                    remaining = ''
            else:
                # Последний параметр или нет разделителя - берем всё до param_suffix
                if param.get('param_suffix'):
                    suffix_pos = remaining.find(param['param_suffix'])
                    if suffix_pos != -1:
                        val = remaining[:suffix_pos]
                        remaining = remaining[suffix_pos + len(param['param_suffix']):]
                    else:
                        val = remaining
                        remaining = ''
                else:
                    val = remaining
                    remaining = ''

            # Пробуем конвертировать в число
            try:
                if '.' in val:
                    parsed[param['name']] = float(val)
                elif val:
                    parsed[param['name']] = int(val)
                else:
                    parsed[param['name']] = val
            except ValueError:
                parsed[param['name']] = val

    result = {
        Block.ADDRESS: address_text,
        Block.COMMAND_CODE: command_text,
        "params": parsed,
    }

    return {'error': False, 'result': result, 'raw': cmd}


crc_algorithms = {
    ChecksumAlgorithm.XOR: 1,
    ChecksumAlgorithm.SUM: 1,
    ChecksumAlgorithm.LRC: 1,
    ChecksumAlgorithm.CRC8: 1,
    ChecksumAlgorithm.CRC16_MODBUS: 2,
    ChecksumAlgorithm.CRC16_CCITT: 2,
    ChecksumAlgorithm.CRC16_X25: 2,
    ChecksumAlgorithm.CRC32: 4,
    ChecksumAlgorithm.CRC32_MPEG2: 4
}

sources = {
    Source.DATA_ONLY: 'Только данные',
    Source.COMMAND_AND_DATA: 'Команда и данные',
    Source.ADDRESS_COMMAND_DATA: 'Адрес, команда и данные',
    Source.FROM_COMMAND: 'От команды',
    Source.FROM_ADDRESS: 'От адреса',
    Source.FROM_LENGTH: 'От длины',
    Source.ALL: 'Всё сообщение'
}

bin_blocks = {
    Block.START_BYTE: {'ru': 'Стартовое слово', 'en': Block.START_BYTE},
    Block.ADDRESS: {'ru': 'Адрес', 'en': Block.ADDRESS},
    Block.COMMAND_CODE: {'ru': 'Команда', 'en': 'command_code'},
    Block.DATA: {'ru': 'Данные', 'en': Block.DATA},
    Block.END_BYTE: {'ru': 'Конечное слово', 'en': Block.END_BYTE},
    Block.LENGTH_FIELD: {'ru': 'Поле длинны', 'en': Block.LENGTH_FIELD},
    Block.CHECKSUM: {'ru': 'Контрольная сумма', 'en': Block.CHECKSUM},
}

def crc_calc(algo=ChecksumAlgorithm.CRC16_MODBUS, data=bytes):
    if algo == ChecksumAlgorithm.XOR:
        crc = 0
        for b in data:
            crc ^= b
        crc &= 0xFF
    elif algo == ChecksumAlgorithm.SUM:
        crc = sum(data) & 0xFF
    elif algo == ChecksumAlgorithm.LRC:
        crc = (-sum(data)) & 0xFF
    elif algo == ChecksumAlgorithm.CRC8:
        crc = 0
        for b in data:
            crc ^= b
            for _ in range(8):
                if crc & 1:
                    crc = (crc >> 1) ^ 0x8C
                else:
                    crc >>= 1
    elif algo == ChecksumAlgorithm.CRC16_MODBUS:
        crc = 0xFFFF
        for b in data:
            crc ^= b
            for _ in range(8):
                if crc & 1:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1
    elif algo == ChecksumAlgorithm.CRC16_CCITT:
        crc = 0xFFFF
        for b in data:
            crc ^= b << 8
            for _ in range(8):
                if crc & 0x8000:
                    crc = (crc << 1) ^ 0x1021
                else:
                    crc <<= 1
            crc &= 0xFFFF
    elif algo == ChecksumAlgorithm.CRC16_X25:
        crc = 0xFFFF
        for b in data:
            crc ^= b
            for _ in range(8):
                if crc & 1:
                    crc = (crc >> 1) ^ 0x8408
                else:
                    crc >>= 1
        crc ^= 0xFFFF
    elif algo == ChecksumAlgorithm.CRC3:
        import zlib
        crc = zlib.crc32(data) & 0xFFFFFFFF
    elif algo == ChecksumAlgorithm.CRC32_MPEG2:
        crc = 0xFFFFFFFF
        for b in data:
            crc ^= b << 24
            for _ in range(8):
                if crc & 0x80000000:
                    crc = (crc << 1) ^ 0x04C11DB7
                else:
                    crc <<= 1
            crc &= 0xFFFFFFFF
    else:
        return {'error': True, 'result': f"Неизвестный алгоритм: {algo}"}

    return crc


def bin_coder(start_byte={'use': False, 'length': 1, 'value': 0xFF},
              address={'use': False, 'length': 1, 'value': 0x01},
              command_code={'use': False, 'length': 1, 'value': 0xaf},
              length_field={'use': False, 'length': 1, 'include': Source.DATA_ONLY},
              byteorder='little',
              checksum={'use': False, 'length': 2, 'algorithm': ChecksumAlgorithm.CRC16_MODBUS, 'source': Source.FROM_ADDRESS},
              end_byte={'use': False, 'length': 1, 'value': 0xFF},
              params=[], #{'name': 'A', 'value': 0, 'length': 2, 'sign': False}
              order=[Block.START_BYTE, Block.ADDRESS, 'command_code', Block.LENGTH_FIELD, Block.DATA, Block.CHECKSUM, Block.END_BYTE]):
    blocks = {}

    # Сборка стартового байта
    if start_byte['use']:
        if start_byte['value'] < 256 ** start_byte['length']:
            blocks[Block.START_BYTE] = start_byte['value'].to_bytes(start_byte['length'], byteorder)
        else:
            return {'error': True, 'result': 'start_byte слишком большой'}

    # Сборка адреса
    if address['use']:
        if address['value'] < 256 ** address['length']:
            blocks[Block.ADDRESS] = address['value'].to_bytes(address['length'], byteorder)
        else:
            return {'error': True, 'result': 'address слишком большой'}

    # Сборка команды
    if command_code['use']:
        if command_code['value'] < 256 ** command_code['length']:
            blocks['command_code'] = command_code['value'].to_bytes(command_code['length'], byteorder)
        else:
            return {'error': True, 'result': 'command_code слишком большой'}

    # Сборка данных
    data_block = bytearray()
    for param in params:
        value = param['value']
        if not param.get('sign', False) and value < 0:
            return {'error': True, 'result': f"Параметр {param['name']} отрицательный, но sign=False"}
        max_val = 256 ** param['length']
        if param.get('sign', False):
            if not (-max_val // 2 <= value < max_val // 2):
                return {'error': True, 'result': f'{param["name"]} вне диапазона signed {param["length"]} байт'}
        else:
            if not (0 <= value < max_val):
                return {'error': True, 'result': f'{param["name"]} вне диапазона unsigned {param["length"]} байт'}
        data_block.extend(value.to_bytes(param['length'], byteorder, signed=param.get('sign', False)))
    blocks[Block.DATA] = bytes(data_block)

    # Сборка длины
    if length_field['use']:
        if length_field['include'] == Source.DATA_ONLY:
            length = len(blocks[Block.DATA])
        elif length_field['include'] == Source.COMMAND_AND_DATA:
            length = len(blocks.get('command_code', b'')) + len(blocks[Block.DATA])
        elif length_field['include'] == Source.ADDRESS_COMMAND_DATA:
            length = len(blocks.get(Block.ADDRESS, b'')) + len(blocks.get('command_code', b'')) + len(blocks[Block.DATA])
        elif length_field['include'] == Source.FROM_COMMAND:
            length = len(blocks.get('command_code', b'')) + length_field['length'] + len(blocks[Block.DATA])
        elif length_field['include'] == Source.FROM_ADDRESS:
            length = len(blocks.get(Block.ADDRESS, b'')) + len(blocks.get('command_code', b'')) + length_field[
                'length'] + len(blocks[Block.DATA])
        elif length_field['include'] == Source.FROM_LENGTH:
            length = length_field['length'] + len(blocks[Block.DATA])
        elif length_field['include'] == Source.ALL:
            current_len = sum(len(b) for b in blocks.values())
            length = current_len + length_field['length'] + checksum['length'] * checksum['use'] + end_byte['length'] * \
                     end_byte['use']
        else:
            return {'error': True, 'result': f"Неизвестный include: {length_field['include']}"}

        if length < 256 ** length_field['length']:
            blocks[Block.LENGTH_FIELD] = length.to_bytes(length_field['length'], byteorder)
        else:
            return {'error': True, 'result': 'Длина слишком большая для length_field'}

    # Сборка scope для checksum
    if checksum['use']:
        scope = bytearray()
        if checksum['source'] == Source.DATA_ONLY:
            scope = blocks[Block.DATA]
        elif checksum['source'] == Source.COMMAND_AND_DATA:
            scope = blocks.get('command_code', b'') + blocks[Block.DATA]
        elif checksum['source'] == Source.ADDRESS_COMMAND_DATA:
            scope = blocks.get(Block.ADDRESS, b'') + blocks.get('command_code', b'') + blocks[Block.DATA]
        elif checksum['source'] == Source.FROM_ADDRESS:
            scope = blocks.get(Block.ADDRESS, b'') + blocks.get('command_code', b'') + blocks.get(Block.LENGTH_FIELD, b'') + \
                    blocks[Block.DATA]
        elif checksum['source'] == Source.FROM_COMMAND:
            scope = blocks.get('command_code', b'') + blocks.get(Block.LENGTH_FIELD, b'') + blocks[Block.DATA]
        elif checksum['source'] == Source.FROM_LENGTH:
            scope = blocks.get(Block.LENGTH_FIELD, b'') + blocks[Block.DATA]
        else:
            return {'error': True, 'result': f"Неизвестный source: {checksum['source']}"}

        data = bytes(scope)
        algo = checksum['algorithm']
        crc = crc_calc(algo, data)

        if isinstance(crc, dict) and crc.get('error'):
            return crc

        if crc < 256 ** checksum['length']:
            blocks[Block.CHECKSUM] = crc.to_bytes(checksum['length'], byteorder)
        else:
            return {'error': True, 'result': 'crc слишком большой'}

    # Сборка end_byte
    if end_byte['use']:
        if end_byte['value'] < 256 ** end_byte['length']:
            blocks[Block.END_BYTE] = end_byte['value'].to_bytes(end_byte['length'], byteorder)
        else:
            return {'error': True, 'result': 'end_byte слишком большой'}

    # Финальная сборка по order
    result = bytearray()
    for step in order:
        if step in blocks:
            result.extend(blocks[step])

    return {'error': False, 'result': bytes(result)}


def bin_decoder(cmd, start_byte={'use': False, 'length': 1, 'value': 0xFF},
                address={'use': False, 'length': 1, 'value': 0x01},
                command_code={'use': False, 'length': 1, 'value': 0xaf},
                length_field={'use': False, 'length': 1, 'include': Source.DATA_ONLY},
                byteorder='little',
                checksum={'use': False, 'length': 2, 'algorithm': ChecksumAlgorithm.CRC16_MODBUS, 'source': Source.DATA_ONLY},
                end_byte={'use': False, 'length': 1, 'value': 0xFF},
                params=[], #{'name': 'A', 'value': 0, 'length': 2, 'sign': False}
                order=[Block.START_BYTE, Block.ADDRESS, 'command_code', Block.LENGTH_FIELD, Block.DATA, Block.CHECKSUM, Block.END_BYTE]):
    if not isinstance(cmd, (bytes, bytearray)):
        return {'error': True, 'result': 'cmd должен быть bytes'}

    report = {}
    pos = 0
    raw_blocks = {}

    # Заранее считаем ожидаемую длину данных из params
    expected_data_len = sum(p['length'] for p in params)

    for step in order:
        if step == Block.START_BYTE and start_byte['use']:
            if pos + start_byte['length'] > len(cmd):
                return {'error': True, 'result': 'Пакет короче ожидаемого (start_byte)'}
            raw_blocks[Block.START_BYTE] = cmd[pos:pos + start_byte['length']]
            report[Block.START_BYTE] = int.from_bytes(raw_blocks[Block.START_BYTE], byteorder)
            if report[Block.START_BYTE] != start_byte['value']:
                return {'error': True,
                        'result': f'start_byte не совпадает: ожидалось {start_byte["value"]}, получено {report["start_byte"]}'}
            pos += start_byte['length']

        elif step == Block.ADDRESS and address['use']:
            if pos + address['length'] > len(cmd):
                return {'error': True, 'result': 'Пакет короче ожидаемого (address)'}
            raw_blocks[Block.ADDRESS] = cmd[pos:pos + address['length']]
            report[Block.ADDRESS] = int.from_bytes(raw_blocks[Block.ADDRESS], byteorder)
            pos += address['length']

        elif step == 'command_code' and command_code['use']:
            if pos + command_code['length'] > len(cmd):
                return {'error': True, 'result': 'Пакет короче ожидаемого (command_code)'}
            raw_blocks['command_code'] = cmd[pos:pos + command_code['length']]
            report['command_code'] = int.from_bytes(raw_blocks['command_code'], byteorder)
            pos += command_code['length']

        elif step == Block.LENGTH_FIELD:
            if length_field['use']:
                if pos + length_field['length'] > len(cmd):
                    return {'error': True, 'result': 'Пакет короче ожидаемого (length_field)'}
                raw_blocks[Block.LENGTH_FIELD] = cmd[pos:pos + length_field['length']]
                report[Block.LENGTH_FIELD] = int.from_bytes(raw_blocks[Block.LENGTH_FIELD], byteorder)
                pos += length_field['length']

        elif step == Block.DATA:
            # Если length_field используется — берём из него, иначе из суммы params
            if length_field['use']:
                data_len = report.get(Block.LENGTH_FIELD, 0)
            else:
                data_len = expected_data_len

            if data_len == 0:
                return {'error': True, 'result': 'Длина данных равна 0, нечего читать'}

            if pos + data_len > len(cmd):
                return {'error': True, 'result': f'Пакет короче ожидаемого (data), нужно {data_len} байт'}

            raw_blocks[Block.DATA] = cmd[pos:pos + data_len]
            pos += data_len

            # Разбор параметров
            data_pos = 0
            report['params'] = {}
            for param in params:
                if data_pos + param['length'] > len(raw_blocks[Block.DATA]):
                    return {'error': True, 'result': f'Недостаточно данных для параметра {param["name"]}'}
                param_bytes = raw_blocks[Block.DATA][data_pos:data_pos + param['length']]
                report['params'][param['name']] = int.from_bytes(param_bytes, byteorder,
                                                                 signed=param.get('sign', False))
                data_pos += param['length']

        elif step == Block.CHECKSUM and checksum['use']:
            if pos + checksum['length'] > len(cmd):
                return {'error': True, 'result': 'Пакет короче ожидаемого (checksum)'}
            raw_blocks[Block.CHECKSUM] = cmd[pos:pos + checksum['length']]
            report[Block.CHECKSUM] = int.from_bytes(raw_blocks[Block.CHECKSUM], byteorder)
            pos += checksum['length']

        elif step == Block.END_BYTE and end_byte['use']:
            if pos + end_byte['length'] > len(cmd):
                return {'error': True, 'result': 'Пакет короче ожидаемого (end_byte)'}
            raw_blocks[Block.END_BYTE] = cmd[pos:pos + end_byte['length']]
            report[Block.END_BYTE] = int.from_bytes(raw_blocks[Block.END_BYTE], byteorder)
            if report[Block.END_BYTE] != end_byte['value']:
                return {'error': True,
                        'result': f'end_byte не совпадает: ожидалось {end_byte["value"]}, получено {report["end_byte"]}'}
            pos += end_byte['length']

    # Проверка CRC
    if checksum['use']:
        scope = bytearray()
        if checksum['source'] == Source.DATA_ONLY:
            scope = raw_blocks.get(Block.DATA, b'')
        elif checksum['source'] == Source.COMMAND_AND_DATA:
            scope = raw_blocks.get('command_code', b'') + raw_blocks.get(Block.DATA, b'')
        elif checksum['source'] == Source.ADDRESS_COMMAND_DATA:
            scope = raw_blocks.get(Block.ADDRESS, b'') + raw_blocks.get('command_code', b'') + raw_blocks.get(Block.DATA, b'')
        elif checksum['source'] == Source.FROM_ADDRESS:
            scope = raw_blocks.get(Block.ADDRESS, b'') + raw_blocks.get('command_code', b'') + raw_blocks.get(
                Block.LENGTH_FIELD, b'') + raw_blocks.get(Block.DATA, b'')
        elif checksum['source'] == Source.FROM_COMMAND:
            scope = raw_blocks.get('command_code', b'') + raw_blocks.get(Block.LENGTH_FIELD, b'') + raw_blocks.get(Block.DATA,
                                                                                                               b'')
        elif checksum['source'] == Source.FROM_LENGTH:
            scope = raw_blocks.get(Block.LENGTH_FIELD, b'') + raw_blocks.get(Block.DATA, b'')
        else:
            return {'error': True, 'result': f"Неизвестный source: {checksum['source']}"}

        calculated_crc = crc_calc(checksum['algorithm'], bytes(scope))
        if isinstance(calculated_crc, dict) and calculated_crc.get('error'):
            return calculated_crc

        if calculated_crc != report[Block.CHECKSUM]:
            return {'error': True,
                    'result': f'CRC не совпадает: ожидалось {calculated_crc}, получено {report["checksum"]}'}

    # Проверка, что весь пакет разобран
    if pos != len(cmd):
        return {'error': True, 'result': f'Лишние байты в конце пакета: {pos} разобрано из {len(cmd)}'}

    return {'error': False, 'result': report}

def bin_decoder_expected_length(start_byte={'use': True, 'length': 1, 'value': 0xFF},
                address={'use': True, 'length': 1, 'value': 0x01},
                command_code={'use': True, 'length': 1, 'value': 0xaf},
                length_field={'use': True, 'length': 1, 'include': Source.DATA_ONLY},
                byteorder='little',
                checksum={'use': True, 'length': 2, 'algorithm': ChecksumAlgorithm.CRC16_MODBUS, 'source': Source.DATA_ONLY},
                end_byte={'use': True, 'length': 1, 'value': 0xFF},
                params=[{'name': 'A', 'value': 0, 'length': 2, 'sign': False}],
                order=[Block.START_BYTE, Block.ADDRESS, 'command_code', Block.LENGTH_FIELD, Block.DATA, Block.CHECKSUM, Block.END_BYTE]):


    length = start_byte['use'] * start_byte['length']
    length += address['use'] * address['length']
    length += command_code['use'] * command_code['length']
    length += length_field['use'] * length_field['length']
    length += checksum['use'] * checksum['length']
    length += end_byte['use'] * end_byte['length']
    for param in params:
        length += param['length']

    return {'error': False, 'result': length}
