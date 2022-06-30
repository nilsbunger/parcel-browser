

class StopExecution(Exception):
    def _render_traceback_(self):
        pass

# Python notebook exit function to stop running without killing the kernel
def nb_exit():
    raise StopExecution

