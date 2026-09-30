from PyQt6.QtCore import QTimer


def add_simple_click_feedback(button, original_icon, feedback_icon, duration=500):
    def on_click():
        button.setIcon(feedback_icon)
        QTimer.singleShot(duration, lambda: button.setIcon(original_icon))

    button.setIcon(original_icon)
    button.clicked.connect(on_click)
    return button