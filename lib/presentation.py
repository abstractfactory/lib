# from __future__ import absolute_import

import lib.controller
import lib.application


def main(path, port=None):
    import pigui.pyqt5.util

    application = lib.application.Lib(port)

    with pigui.pyqt5.util.application_context():
        controller = lib.controller.Lib()

        model = lib.model.Model()
        controller.set_model(model)
        application.set_model(model)

        application.set_controller(controller)

        controller.resize(*lib.settings.WINDOW_SIZE)
        controller.animated_show()

        model.setup(path)


if __name__ == '__main__':
    """Example"""

    import pifou
    pifou.setup_log()
    pifou.setup_log('lib')

    main(
        path=r'C:\studio\content\jobs\machine\content',
        port=None
    )
