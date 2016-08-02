OS_CONST = {
    # asm-generic/fcntl.h
    'O_RDWR': 00000002,
    'SOL_SOCKET': 1,
    'SO_ERROR': 4,
    # asm-generic/fcntl.h
    'O_APPEND': 00002000
}

SOCK_CONST = {
    'SOCK_STREAM': 1,
    'SOCK_DGRAM': 2
}

STAT_CONST = {
    'S_IFMT': 00170000,
    'S_IFSOCK': 0140000,
    'S_IFLNK': 0120000,
    'S_IFREG': 0100000,
    'S_IFBLK': 0060000,
    'S_IFDIR': 0040000,
    'S_IFCHR': 0020000,
    'S_IFIFO': 0010000,
    'S_ISUID': 0004000,
    'S_ISGID': 0002000,
    'S_ISVTX': 0001000
}

FCNTL64_CMD_TO_INT = {
    'F_DUPFD':	0,
    'F_GETFD':	1,
    'F_SETFD':	2,
    'F_GETFL':	3,
    'F_SETFL':	4,
    'F_GETLK':	5,
    'F_SETLK':	6,
    'F_SETLKW': 7,
    'F_SETOWN': 8,
    'F_GETOWN': 9,
    'F_SETSIG': 10,
    'F_GETSIG': 11,
    'F_GETLK64': 12,
    'F_SETLK64': 13,
    'F_SETLKW64': 14,
    'F_SETOWN_EX': 15,
    'F_GETOWN_EX': 16,
    'F_GETOWNER_UIDS': 17
}

FCNTL64_INT_TO_CMD = {y: x for x, y in FCNTL64_CMD_TO_INT.iteritems()}

SIGNAL_SIG_TO_INT = {
    'SIGHUP': 1,
    'SIGINT': 2,
    'SIGQUIT': 3,
    'SIGILL': 4,
    'SIGTRAP': 5,
    'SIGABRT': 6,
    'SIGIOT': 6,
    'SIGBUS': 7,
    'SIGFPE': 8,
    'SIGKILL': 9,
    'SIGUSR1': 10,
    'SIGSEGV': 11,
    'SIGUSR2': 12,
    'SIGPIPE': 13,
    'SIGALRM': 14,
    'SIGTERM': 15,
    'SIGSTKFLT': 16,
    'SIGCHLD': 17,
    'SIGCONT': 18,
    'SIGSTOP': 19,
    'SIGTSTP': 20,
    'SIGTTIN': 21,
    'SIGTTOU': 22,
    'SIGURG': 23,
    'SIGXCPU': 24,
    'SIGXFSZ': 25,
    'SIGVTALRM': 26,
    'SIGPROF': 27,
    'SIGWINCH': 28,
    'SIGIO': 29,
    'SIGPOLL': 29,
    'SIGLOST': 29,
    'SIGPWR': 30,
    'SIGSYS': 31,
    'SIGUNUSED': 31,
    'SIGRTMIN': 32
}

SIGNAL_INT_TO_SIG = {y: x for x, y in SIGNAL_SIG_TO_INT.iteritems()}

IOCTLS_IOCTL_TO_INT = {
    'TCGETS': 0x5401,
    'TCSETS': 0x5402,
    'TCSETSW': 0x5403,
    'TCSETSF': 0x5404,
    'TCGETA': 0x5405,
    'TCSETA': 0x5406,
    'TCSETAW': 0x5407,
    'TCSETAF': 0x5408,
    'TCSBRK': 0x5409,
    'TCXONC': 0x540A,
    'TCFLSH': 0x540B,
    'TIOCEXCL':	0x540C,
    'TIOCNXCL':	0x540D,
    'TIOCSCTTY': 0x540E,
    'TIOCGPGRP': 0x540F,
    'TIOCSPGRP': 0x5410,
    'TIOCOUTQ': 0x5411,
    'TIOCSTI': 0x5412,
    'TIOCGWINSZ': 0x5413,
    'TIOCSWINSZ': 0x5414,
    'TIOCMGET':	0x5415,
    'TIOCMBIS':	0x5416,
    'TIOCMBIC':	0x5417,
    'TIOCMSET':	0x5418,
    'TIOCGSOFTCAR': 0x5419,
    'TIOCSSOFTCAR': 0x541A,
    'FIONREAD':	0x541B,
    'TIOCINQ':	0x541B,
    'TIOCLINUX': 0x541C,
    'TIOCCONS':	0x541D,
    'TIOCGSERIAL': 0x541E,
    'TIOCSSERIAL': 0x541F,
    'TIOCPKT': 0x5420,
    'FIONBIO': 0x5421,
    'TIOCNOTTY': 0x5422,
    'TIOCSETD':	0x5423,
    'TIOCGETD':	0x5424,
    'TCSBRKP': 0x5425,
    'TIOCSBRK':	0x5427,
    'TIOCCBRK':	0x5428,
    'TIOCGSID':	0x5429,
    'TIOCGRS485': 0x542E,
    'TIOCSRS485': 0x542F,
    'TCGETX': 0x5432,
    'TCSETX': 0x5433,
    'TCSETXF': 0x5434,
    'TCSETXW': 0x5435,
    'TIOCVHANGUP': 0x5437,
    'FIONCLEX':	0x5450,
    'FIOCLEX': 0x5451,
    'FIOASYNC':	0x5452,
    'TIOCSERCONFIG': 0x5453,
    'TIOCSERGWILD': 0x5454,
    'TIOCSERSWILD': 0x5455,
    'TIOCGLCKTRMIOS': 0x5456,
    'TIOCSLCKTRMIOS': 0x5457,
    'TIOCSERGSTRUCT': 0x5458,
    'TIOCSERGETLSR':   0x5459,
    'TIOCSERGETMULTI': 0x545A,
    'TIOCSERSETMULTI': 0x545B,
    'TIOCMIWAIT': 0x545C,
    'TIOCGICOUNT': 0x545D,
}

IOCTLS_INT_TO_IOCTL = {y: x for x, y in IOCTLS_IOCTL_TO_INT.iteritems()}

SHUTDOWN_INT_TO_CMD = {
    0: 'SHUT_RD',
    1: 'SHUT_WR',
    2: 'SHUT_RDWR'
}

SHUTDOWN_CMD_TO_INT = {y: x for x, y in SHUTDOWN_INT_TO_CMD.iteritems()}

SIGPROCMASK_INT_TO_CMD = {
    0: 'SIG_BLOCK',
    1: 'SIG_UNBLOCK',
    2: 'SIG_SETMASK'
}

SIGPROC_CMD_TO_INT = {y: x for x, y in SIGPROCMASK_INT_TO_CMD.iteritems()}

PERM_INT_TO_PERM = {
    4: 'R_OK',
    2: 'W_OK',
    1: 'X_OK',
    0: 'F_OK'
}

PERM_PERM_TO_INT = {y: x for x, y in PERM_INT_TO_PERM.iteritems()}
