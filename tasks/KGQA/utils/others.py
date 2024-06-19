
class ColorMessage:
    @staticmethod
    def red(msg):
        return "\033[91m" + msg + "\033[0m"

    @staticmethod
    def green(msg):
        return "\033[92m" + msg + "\033[0m"

    @staticmethod
    def cyan(msg):
        return "\033[96m" + msg + "\033[0m"

    @staticmethod
    def yellow(msg):
        return "\033[93m" + msg + "\033[0m"
    
    ## only for debug, delete later
    @staticmethod
    def na(msg):
        return "\033[94m" + msg + "\033[0m"