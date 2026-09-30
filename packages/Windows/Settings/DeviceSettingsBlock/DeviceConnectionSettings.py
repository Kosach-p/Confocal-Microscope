import time

from PyQt6.uic import loadUi
from PyQt6.QtWidgets import QCheckBox, QComboBox, QLabel, QDoubleSpinBox, QGroupBox
from packages.core.config.path import ui
from packages.core.widgets.ComboBox import upgradeComboBox
from packages.core.widgets.SpinBox import upgradeDoubleSpinBox

from ui.ControllerSettings.DeviceConnectionSettings import Ui_GroupBox


class DeviceConnectionSettings(QGroupBox, Ui_GroupBox):
    def __init__(self):
        super().__init__()
        self.init_cplt = False
        self.setupUi(self)
        self.settings = {}

    def setUI(self):
        self.profile_list_comboBox = upgradeComboBox(self.findChild(QComboBox, "profile_list_comboBox"))
        self.profile_status_label = self.findChild(QLabel, "profile_status_label")
        self.use_ECHO_checkBox = self.findChild(QCheckBox, "use_ECHO_checkBox")
        self.ECHO_period_doubleSpinBox = upgradeDoubleSpinBox(self.findChild(QDoubleSpinBox, "ECHO_period_doubleSpinBox"))

        self.profile_state = {}
        self._updating_profile_list = False

        self.connection_init()

        self.on_use_ECHO_toggled()
        self.init_cplt = True

        self.set_settings(self.settings)

    def connection_init(self):
        self.use_ECHO_checkBox.toggled.connect(self.on_use_ECHO_toggled)
        self.profile_list_comboBox.currentIndexChanged.connect(self._on_current_index_changed)

    def on_use_ECHO_toggled(self):
        state = self.use_ECHO_checkBox.isChecked()
        self.ECHO_period_doubleSpinBox.setEnabled(state)

    def _on_current_index_changed(self, index):
        if self._updating_profile_list:
            return
        self._update_profile_status()

    def _update_profile_status(self):
        """Обновляет иконку статуса выбранного профиля"""
        if self.init_cplt is False:
            return
        current_data = self.profile_list_comboBox.currentData()
        current_text = self.profile_list_comboBox.currentText()
        profile = self.profile_state.get(current_data)

        if profile is not None:
            state = profile.get('state', 0)
            # state: 1 = подключён (✅), всё остальное = не подключён (❌)
            emoji = "✅" if state > 1 else "❌"
            text = f"{current_text} {emoji}"
            self.profile_status_label.setText(text)
        else:
            self.profile_status_label.setText("")

    def _are_profiles_equal(self, profiles: dict) -> bool:
        """Проверяет, совпадает ли новый список профилей с текущим"""
        if self.profile_list_comboBox.count() != len(profiles):
            return False

        for i in range(self.profile_list_comboBox.count()):
            key = self.profile_list_comboBox.itemData(i)
            text = self.profile_list_comboBox.itemText(i)
            if key not in profiles:
                return False
            if profiles[key].get('name', 'Без имени') != text:
                return False

        return True

    def set_profile_list(self, profiles: dict):
        """Устанавливает список профилей. Если список не изменился — ComboBox не трогает."""
        if self._are_profiles_equal(profiles) or self.init_cplt is False:
            return
        current_data = self.profile_list_comboBox.currentData()

        self._updating_profile_list = True

        self.profile_list_comboBox.clear()
        for key, value in profiles.items():
            name = value.get('name', 'Без имени')
            self.profile_list_comboBox.addItem(name, key)

        index = self.profile_list_comboBox.findData(current_data)
        if index >= 0:
            self.profile_list_comboBox.setCurrentIndex(index)
        elif self.profile_list_comboBox.count() > 0:
            self.profile_list_comboBox.setCurrentIndex(0)

        self._updating_profile_list = False
        self._update_profile_status()

    def set_profile_state(self, profiles_state: dict):
        """Обновляет состояние профилей"""
        self.profile_state = profiles_state

        if self.init_cplt:
            self._update_profile_status()
            self.set_profile_list(profiles_state)

    def get_settings(self) -> dict:
        if self.init_cplt is False:
            return self.settings
        current_data = self.profile_list_comboBox.currentData()
        current_text = self.profile_list_comboBox.currentText()
        echo_enable = self.use_ECHO_checkBox.isChecked()
        poll_interval = self.ECHO_period_doubleSpinBox.value()
        return {
            'profile': {"id": current_data, "name": current_text},
            'echo_enable': echo_enable,
            'poll_interval': poll_interval,
        }

    def set_settings(self, settings: dict):
        self.settings = settings
        if self.init_cplt:
            if 'profile' in settings:
                if not isinstance(settings['profile'], str):
                    name = settings['profile'].get("name", 'Без имени')
                    id = settings['profile'].get("id", -1)
                    self.profile_list_comboBox.addItem(name, id)

            if 'echo_enable' in settings:
                self.use_ECHO_checkBox.setChecked(settings['echo_enable'])

            if 'poll_interval' in settings:
                self.ECHO_period_doubleSpinBox.setValue(settings['poll_interval'])

