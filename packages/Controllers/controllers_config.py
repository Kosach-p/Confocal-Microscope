device_groups = {
    'modulators': {
        'ru': 'Генераторы',
        'en': 'Generators',
        'function': 'Генерация СВЧ сигнала'
    },
    'beam_steerers': {
        'ru': 'Сканеры  пучка (XY-отклонение)',
        'en': 'Beam Steerers (XY Deflection)',
        'function': 'Перемещают лазерный пучок в двух плоскостях'
    },
    'positioners': {
        'ru': 'Позиционеры (XYZ-перемещение)',
        'en': 'Positioners (XYZ Movement)',
        'function': 'Перемещают предметный столик в трёх направлениях'
    },
    'spectral_tuners': {
        'ru': 'Монохроматоры',
        'en': 'Monochromators',
        'function': 'Изменяют длину волны монохроматора'
    },
    'detectors': {
        'ru': 'Детекторы света',
        'en': 'Light detectors',
        'function': 'Измеряют интенсивность излучения'
    }
}


UNITS = {
    'beam_steerers': {
        'display_unit': 'lsb',
        'lsb_unit': 'lsb',
        'units': {
            'lsb': {
                'coef': 1.0, 'step': 1, 'decimal': 0,
                'ru': 'lsb', 'en': 'lsb',
            },
            'um': {
                'coef': 0.001, 'step': 1, 'decimal': 3,
                'ru': 'мкм', 'en': 'um',
            },
            'mm': {
                'coef': 1.0, 'step': 1, 'decimal': 3,
                'ru': 'мм', 'en': 'mm',
            },
            'm': {
                'coef': 1000.0, 'step': 0.001, 'decimal': 6,
                'ru': 'м', 'en': 'm',
            },
        },
    },

    'positioners': {
        'display_unit': 'mm',
        'lsb_unit': 'lsb',
        'units': {
            'lsb': {
                'coef': 1.0, 'step': 10, 'decimal': 0,
                'ru': 'lsb', 'en': 'lsb',
            },
            'um': {
                'coef': 0.001, 'step': 10, 'decimal': 3,
                'ru': 'мкм', 'en': 'um',
            },
            'mm': {
                'coef': 1.0, 'step': 1, 'decimal': 3,
                'ru': 'мм', 'en': 'mm',
            },
            'm': {
                'coef': 1000.0, 'step': 0.001, 'decimal': 6,
                'ru': 'м', 'en': 'm',
            },
        },
    },

    'modulators': {
        'display_unit': 'MHz',
        'lsb_unit': 'lsb',
        'units': {
            'lsb': {
                'coef': 1.0, 'step': 1, 'decimal': 0,
                'ru': 'lsb', 'en': 'lsb',
            },
            'Hz': {
                'coef': 1e-6, 'step': 1, 'decimal': 3,
                'ru': 'Гц', 'en': 'Hz',
            },
            'kHz': {
                'coef': 1e-3, 'step': 1, 'decimal': 3,
                'ru': 'кГц', 'en': 'kHz',
            },
            'MHz': {
                'coef': 1.0, 'step': 1, 'decimal': 3,
                'ru': 'МГц', 'en': 'MHz',
            },
            'GHz': {
                'coef': 1000.0, 'step': 0.001, 'decimal': 3,
                'ru': 'ГГц', 'en': 'GHz',
            },
        },
    },

    'spectral_tuners': {
        'display_unit': 'nm',
        'lsb_unit': 'lsb',
        'units': {
            'lsb': {
                'coef': 1.0, 'step': 1, 'decimal': 0,
                'ru': 'lsb', 'en': 'lsb',
            },
            'nm': {
                'coef': 0.001, 'step': 0.1, 'decimal': 3,
                'ru': 'нм', 'en': 'nm',
            },
            'um': {
                'coef': 1.0, 'step': 0.001, 'decimal': 4,
                'ru': 'мкм', 'en': 'um',
            },
            'mm': {
                'coef': 1000.0, 'step': 0.001, 'decimal': 6,
                'ru': 'мм', 'en': 'mm',
            },
        },
    },

    'detectors': {
        'display_unit': 'lsb',
        'lsb_unit': 'lsb',
        'units': {
            'lsb': {
                'coef': 1.0, 'step': 1, 'decimal': 0,
                'ru': 'lsb', 'en': 'lsb',
            },
            'V': {
                'coef': 1000.0, 'step': 0.001, 'decimal': 4,
                'ru': 'В', 'en': 'V',
            },
            'mV': {
                'coef': 1.0, 'step': 0.1, 'decimal': 3,
                'ru': 'мВ', 'en': 'mV',
            },
        },
    },

    'time': {
        'display_unit': 'ms',
        'lsb_unit': 'lsb',
        'units': {
            'lsb': {
                'coef': 1.0, 'step': 1, 'decimal': 0,
                'ru': 'lsb', 'en': 'lsb',
            },
            'us': {
                'coef': 1.0, 'step': 1, 'decimal': 0,
                'ru': 'мкс', 'en': 'us',
            },
            'ms': {
                'coef': 1000.0, 'step': 1, 'decimal': 0,
                'ru': 'мс', 'en': 'ms',
            },
            's': {
                'coef': 1_000_000.0, 'step': 0.001, 'decimal': 3,
                'ru': 'с', 'en': 's',
            },
            'min': {
                'coef': 60_000_000.0, 'step': 0.001, 'decimal': 3,
                'ru': 'мин', 'en': 'min',
            },
            'h': {
                'coef': 3_600_000_000.0, 'step': 0.001, 'decimal': 3,
                'ru': 'ч', 'en': 'h',
            },
        },
    },
}
