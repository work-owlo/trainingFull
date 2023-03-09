import os

class Log:

    def __init__(self, filename):
        self.filename = filename

    def add_log(log):
        enabled = True
        if enabled:
            filename = 'logs.txt'
            # write the log to the file
            with open(filename, 'a') as f:
                f.write(log + '\n')
            # Log.limit_log_length()

    def limit_log_length():
        # throw error if log file is too long
        filename = 'static/logs.txt'
        num_lines = sum(1 for line in open(filename))
        if num_lines > 1000:
            raise Exception('Log file too long')