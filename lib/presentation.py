from __future__ import absolute_import

import lib.widget
import lib.application


def main(url, representation=None, service=None):
    import pigui.util.pyqt5

    with pigui.util.pyqt5.app_context():
        app = lib.application.Lib(representation=representation)
                                  # service=service)
        widget = lib.widget.Lib()
        app.init_widget(widget)
        app.load(url)


if __name__ == '__main__':
    import pifou
    pifou.setup_log()

    main(
        url='/s/content/jobs/machine/content/assets',
        representation=None,
        # service='im.local'
        service='maya.local'
    )
