from packages.core.services.preview_image import show_image, hide_image
import multiprocessing

#show_image('Icon/image/logo.png')
if __name__ == "__main__":
    multiprocessing.freeze_support()  # Надо, иначе мультипроцессинг будет каждый раз в exe открывать новое приложение

    from PyQt6.QtWidgets import QApplication
    from packages.Windows.MainWindow.MainWindow import MainWindow
    from sys import argv

    import matplotlib
    matplotlib.use('Agg')

    app = QApplication(argv)
    app.setStyle("Windows")

    window = MainWindow()

    window.show()
    window.center_on_screen()

    #hide_image()

    app.exec()

    window.device_manager.to_worker.put({'command': 'stop', 'id': -1, 'params': None})
    window.NodeEditorWindow.nodeeditor.ProcessManagerObj.kill()
    window.save_all_settings()