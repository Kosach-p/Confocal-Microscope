device_command_struct = {
    "beam_steerers": {
        "device": {
            "name": "Galvo",
            "name_ru": "Гальвосканер",
            "client_attr": "Galvoscanner_client"
        },
        "commands": {
            "ECHO": {
                "send": ["echo"],
                "receive": ["echo_echo"]
            },
            "set_cord": {
                "send": ["x", "y"],
                "receive": ["echo_x", "echo_y"]
            },
            "get_cord": {
                "send": [],
                "receive": ["x", "y"]
            },
            "send_gcode_F": {
                "send": ["F"],
                "receive": ["status"]
            },
            "send_gcode_G00": {
                "send": ["x", "y"],
                "receive": ["status"]
            },
            "send_gcode_G01": {
                "send": ["x", "y"],
                "receive": ["status"]
            },
            "send_gcode_G04": {
                "send": ["P", "x"],
                "receive": ["status"]
            },
            "send_gcode_M03": {
                "send": [],
                "receive": ["status"]
            },
            "send_gcode_M05": {
                "send": [],
                "receive": ["status"]
            },
            "send_gcode_S": {
                "send": ["S"],
                "receive": ["status"]
            },
            "send_gcode_M112": {
                "send": [],
                "receive": []
            }
        }
    },
    "detectors": {
        "device": {
            "name": "PhotonCounter",
            "name_ru": "Счётчик фотонов",
            "client_attr": "PhotonCounter_client"
        },
        "commands": {
            "ECHO": {
                "send": ["echo"],
                "receive": ["echo_echo"]
            },
            "GetCurrentCount": {
                "send": [],
                "receive": ["status", "count"]
            },
            "StartCounting": {
                "send": [],
                "receive": []
            },
            "GetCounting": {
                "send": [],
                "receive": ["status", "count"]
            },
            "SetAccumTime": {
                "send": ["accum_time"],
                "receive": ["echo"]
            },
            "SetComparatorLevel": {
                "send": ["CompLevel"],
                "receive": ["echo"]
            }
        }
    },
    "positioners": {
        "device": {
            "name": "Piezo",
            "name_ru": "Пьезо",
            "client_attr": "Piezo_client"
        },
        "commands": {
            "ECHO": {
                "send": ["echo"],
                "receive": ["echo_echo"]
            },
            "send_gcode_F": {
                "send": ["F"],
                "receive": ["status"]
            },
            "send_gcode_G01": {
                "send": ["X", "Y", "Z"],
                "receive": ["status"]
            }
        }
    },
    "spectral_tuners": {
        "device": {
            "name": "StepperMotor",
            "name_ru": "Шаговый мотор",
            "client_attr": "StepperMotor_client"
        },
        "commands": {
            "ECHO": {
                "send": ["echo"],
                "receive": ["echo_echo"]
            },
            "stepper_motor_go": {
                "send": ["direction", "travel"],
                "receive": ["direction", "travel"]
            },
            "reset_end_caps_flag": {
                "send": ["flag"],
                "receive": ["echo"]
            },
            "get_stepper_status": {
                "send": ["param1", "param2"],
                "receive": ["status", "steps", "direction", "endcap1", "endcap2", "stall"]
            },
            "stepper_motor_hold": {
                "send": ["HOLD_Reset"],
                "receive": ["echo"]
            },
            "stepper_motor_current_settings": {
                "send": ["I_HOLD", "I_RUN", "I_HOLD_DELAY"],
                "receive": ["I_HOLD", "I_RUN", "I_HOLD_DELAY"]
            },
            "stepper_motor_StallGuard_settings": {
                "send": ["threshold"],
                "receive": ["echo"]
            },
            "stepper_motor_acceleration_settings": {
                "send": ["MAX_speed", "MIN_speed", "accel"],
                "receive": ["MAX_speed", "MIN_speed", "accel"]
            }
        }
    },
    "modulators": {
        "device": {
            "name": "Modulator",
            "name_ru": "Модулятор",
            "client_attr": "Modulator_client"
        },
        "commands": {
            "ECHO": {
                "send": ["echo"],
                "receive": ["echo_echo"]
            },
            "set_frq_1": {
                "send": ["frq"],
                "receive": ["frq_echo"]
            },
            "set_frq_2": {
                "send": ["frq"],
                "receive": ["frq_echo"]
            },
            "set_power": {
                "send": ["power"],
                "receive": ["power_echo"]
            },
            "sweep_frq_time_ms": {
                "send": ["time_ms"],
                "receive": ["time_echo"]
            },
            "sweep_frq_step": {
                "send": ["step"],
                "receive": ["step_echo"]
            },
            "sweep_frq_start": {
                "send": [],
                "receive": ["start_echo"]
            },
            "sweep_frq_stop": {
                "send": [],
                "receive": ["stop_echo"]
            },
        }
    }
}