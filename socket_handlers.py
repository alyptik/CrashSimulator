from tracereplay_python import *
import os
import logging

def bind_entry_handler(syscall_id, syscall_object, pid):
    logging.debug('Entering bind entry handler')
    p = tracereplay.peek_register(pid, tracereplay.ECX)
    params = extract_socketcall_parameters(pid, p, 1)
    fd_from_execution = int(params[0])
    fd_from_trace = int(syscall_object.args[0].value)
    logging.debug('File descriptor from execution: %d', fd_from_execution)
    logging.debug('File descriptor from trace: %d', fd_from_trace)
    if fd_from_execution != fd_from_trace:
        raise ReplayDeltaError('File descriptor from execution ({}) '
                               'does not match file descriptor from trace ({})' \
                               .format(fd_from_execution, fd_from_trace))
    if fd_from_trace in tracereplay.REPLAY_FILE_DESCRIPTORS:
        logging.debug('Replaying this system call')
        subcall_return_success_handler(syscall_id, syscall_object, pid)
    else:
        logging.debug('Not replaying this call')

def bind_exit_handler(syscall_id, syscall_object, pid):
    pass

def getpeername_entry_handler(syscall_id, syscall_object, pid):
    logging.debug('Entering getpeername handler')
    # Pull out the info that we can check
    ecx = tracereplay.peek_register(pid, tracereplay.ECX)
    params = extract_socketcall_parameters(pid, ecx, 3)
    fd = params[0]
    # We don't compare params[1] because it is the address of an empty buffer
    # We don't compare params[2] because it is the address of an out parameter
    # Get values from trace for comparison
    fd_from_trace = syscall_object.args[0].value
    # Check to make sure everything is the same
    if fd != int(fd_from_trace):
        raise ReplayDeltaError('File descriptor from execution ({}) '
                               'does not match file descriptor from trace ({})' \
                                .format(fd, fd_from_trace))
    #Decide if this is a file descriptor we want to deal with
    if fd_from_trace in tracereplay.REPLAY_FILE_DESCRIPTORS:
        logging.info('Replaying this system call')
        noop_current_syscall(pid)
        if syscall_object.ret[0] != -1:
            logging.debug('Got successful getpeername call')
            addr = params[1]
            length_addr = params[2]
            length = int(syscall_object.args[2].value.strip('[]'))
            logging.debug('Addr: %d', addr)
            logging.debug('Length addr: %d', length_addr)
            logging.debug('Length: %d', length)
            sockfields = syscall_object.args[1].value
            family = sockfields[0].value
            port = int(sockfields[1].value)
            ip = sockfields[2].value
            logging.debug('Family: %s', family)
            logging.debug('Port: %d', port)
            logging.debug('Ip: %s', ip)
            if family != 'AF_INET':
                raise NotImplementedException('getpeername only supports AF_INET')
            tracereplay.populate_af_inet_sockaddr(pid,
                                                  addr,
                                                  port,
                                                  ip,
                                                  length_addr,
                                                  length)
        else:
            logging.debug('Got unsuccessful getpeername call')
        apply_return_conditions(pid, syscall_object)
    else:
        logging.info('Not replaying this system call')

def getsockname_entry_handler(syscall_id, syscall_object, pid):
    logging.debug('Entering getsockname handler')
    # Pull out the info that we can check
    ecx = tracereplay.peek_register(pid, tracereplay.ECX)
    params = extract_socketcall_parameters(pid, ecx, 3)
    fd = params[0]
    # We don't compare params[1] because it is the address of an empty buffer
    # We don't compare params[2] because it is the address of an out parameter
    # Get values from trace for comparison
    fd_from_trace = syscall_object.args[0].value
    # Check to make sure everything is the same
    if fd != int(fd_from_trace):
        raise ReplayDeltaError('File descriptor from execution ({}) does not match '
                        'file descriptor from trace ({})'
                        .format(fd, fd_from_trace))
    #Decide if this is a file descriptor we want to deal with
    if fd_from_trace in tracereplay.REPLAY_FILE_DESCRIPTORS:
        logging.info('Replaying this system call')
        noop_current_syscall(pid)
        if syscall_object.ret[0] != -1:
            logging.debug('Got successful getsockname call')
            addr = params[1]
            length_addr = params[2]
            length = int(syscall_object.args[2].value.strip('[]'))
            logging.debug('Addr: %d', addr)
            logging.debug('Length addr: %d', length_addr)
            logging.debug('Length: %d', length)
            sockfields = syscall_object.args[1].value
            family = sockfields[0].value
            port = int(sockfields[1].value)
            ip = sockfields[2].value
            logging.debug('Family: %s', family)
            logging.debug('Port: %d', port)
            logging.debug('Ip: %s', ip)
            if family != 'AF_INET':
                raise NotImplementedException('getsockname only supports AF_INET')
            tracereplay.populate_af_inet_sockaddr(pid,
                                                  addr,
                                                  port,
                                                  ip,
                                                  length_addr,
                                                  length)
        else:
            logging.debug('Got unsuccessful getsockname call')
        apply_return_conditions(pid, syscall_object)
    else:
        logging.info('Not replaying this system call')

def getsockname_exit_handler(syscall_id, syscall_object, pid):
    pass

def shutdown_subcall_entry_handler(syscall_id, syscall_object, pid):
    logging.debug('Entering shutdown entry handler')
    # Pull out the info we can check
    ecx = tracereplay.peek_register(pid, tracereplay.ECX)
    params = extract_socketcall_parameters(pid, ecx, 2)
    fd = params[0]
    fd_from_trace = syscall_object.args[0].value
    # TODO: We need to check the 'how' parameter here
    # Check to make sure everything is the same 
    if fd != int(fd_from_trace):
        raise ReplayDeltaError('File descriptor from execution ({}) '
                               'does not match file descriptor from trace ({})' \
                               .format(fd, fd_from_trace))
    # Decide if we want to replay this system call
    if fd_from_trace in tracereplay.REPLAY_FILE_DESCRIPTORS:
        logging.info('Replaying this system call')
        noop_current_syscall(pid)
        apply_return_conditions(pid, syscall_object)
    else:
        logging.info('Not replaying this system call')

def getsockopt_entry_handler(syscall_id, syscall_object, pid):
    logging.debug('Entering getsockopt handler')
    # Pull out what we can compare
    ecx = tracereplay.peek_register(pid, tracereplay.ECX)
    params = extract_socketcall_parameters(pid, ecx, 5)
    fd = params[0]
    fd_from_trace = int(syscall_object.args[0].value)
    optval_addr = params[3]
    optval_len_addr = params[4]
    # We don't check param[3] because it is an address of an empty buffer
    # We don't check param[4] because it is an address of an empty length
    # Check to make sure everything is the same
    if fd != int(fd_from_trace):
        raise ReplayDeltaError('File descriptor from execution ({}) '
                               'does not match file descriptor from trace ({})'
                               .format(fd, fd_from_trace))
    # This if is sufficient for now for the implemented options
    if params[1] != 1 or params[2] != 4:
        raise NotImplementedError('Unimplemented getsockopt level or optname')
    if fd_from_trace in tracereplay.REPLAY_FILE_DESCRIPTORS:
        logging.info('Replaying this system call')
        optval_len = int(syscall_object.args[4].value.strip('[]'))
        if optval_len != 4:
            raise NotImplementedException('getsockopt() not implemented for '
                                          'optval sizes other than 4')
        optval = int(syscall_object.args[3].value.strip('[]'))
        logging.debug('Optval: %s', optval)
        logging.debug('Optval Length: %s', optval_len)
        logging.debug('Optval addr: %x', optval_addr % 0xffffffff)
        logging.debug('Optval Lenght addr: %d', optval_len_addr % 0xffffffff)
        noop_current_syscall(pid)
        logging.debug('Writing values')
        tracereplay.populate_int(pid, optval_addr, optval)
        tracereplay.populate_int(pid, optval_len_addr, 4)
        apply_return_conditions(pid, syscall_object)
    else:
        logging.info('Not replaying this system call')

#Horrible hack
def socket_exit_handler(syscall_id, syscall_object, pid):
    pass

# TODO: There is a lot more checking to be done here
def socket_subcall_entry_handler(syscall_id, syscall_object, pid):
    logging.debug('Entering socket subcall entry handler')
    ecx = tracereplay.peek_register(pid, tracereplay.ECX)
    params = extract_socketcall_parameters(pid, ecx, 3)
    # Only PF_INET and PF_LOCAL socket calls are handled
    execution_is_PF_INET = (params[0] == tracereplay.PF_INET)
    trace_is_PF_INET = (str(syscall_object.args[0]) == '[\'PF_INET\']')
    execution_is_PF_LOCAL = (params[0] == 1) #define PF_LOCAL 1
    trace_is_PF_LOCAL = (str(syscall_object.args[0]) == '[\'PF_LOCAL\']')
    logging.debug('Execution is PF_INET: %s', execution_is_PF_INET)
    logging.debug('Trace is PF_INET: %s', trace_is_PF_INET)
    logging.debug('Exeuction is PF_LOCAL: %s', execution_is_PF_LOCAL)
    logging.debug('Trace is PF_LOCAL: %s', trace_is_PF_LOCAL)
    if execution_is_PF_INET != trace_is_PF_INET:
        raise Exception('Encountered socket subcall with mismatch between '
                        'execution protocol family and trace protocol family')
    if execution_is_PF_LOCAL != trace_is_PF_LOCAL:
        raise Exception('Encountered socket subcall with mismatch between '
                        'execution protocol family and trace protocol family')
    # Decide if we want to deal with this socket call or not
    if trace_is_PF_INET or \
       execution_is_PF_INET or \
       trace_is_PF_LOCAL or \
       execution_is_PF_LOCAL:
        noop_current_syscall(pid)
        fd = syscall_object.ret
        logging.debug('File Descriptor from trace: %s', fd)
        if fd not in tracereplay.REPLAY_FILE_DESCRIPTORS:
            tracereplay.REPLAY_FILE_DESCRIPTORS.append(fd[0])
        else:
            raise Exception('File descriptor from trace is already tracked')
        apply_return_conditions(pid, syscall_object)
    else:
        logging.info('Ignoring non-PF_INET call to socket')

def accept_subcall_entry_handler(syscall_id, syscall_object, pid):
    logging.debug('Checking if line from trace is interrupted accept')
    # Hack to fast forward through interrupted accepts
    while syscall_object.ret[0] == '?':
        logging.debug('Got interrupted accept. Will advance past')
        syscall_object = tracereplay.system_calls.next()
        logging.debug('Got new line %s', syscall_object.original_line)
        if syscall_object.name != 'accept':
            raise Exception('Attempt to advance past interrupted accept line '
                            'failed. Next system call was not accept!')
    ecx = tracereplay.peek_register(pid, tracereplay.ECX)
    params = extract_socketcall_parameters(pid, ecx, 3)
    # Pull out everything we can check
    fd = params[0]
    fd_from_trace = syscall_object.args[0].value
    # We don't check param[1] because it is the address of a buffer
    # We don't check param[2] because it is the address of a length
    # Check to make sure everything is the same
    if fd != int(fd_from_trace):
        raise Exception('File descriptor from execution ({}) does not match '
                        'file descriptor from trace ({})'
                        .format(fd, fd_from_trace))
    # Decide if this is a system call we want to replay
    if fd_from_trace in tracereplay.REPLAY_FILE_DESCRIPTORS:
        logging.debug('Replaying this system call')
        noop_current_syscall(pid)
        if syscall_object.ret[0] != -1:
            ret = syscall_object.ret[0]
            if ret in tracereplay.REPLAY_FILE_DESCRIPTORS:
                raise Exception('Syscall object return value ({}) already exists in'
                                'tracked file descriptors list ({})'
                                .format(ret, tracereplay.REPLAY_FILE_DESCRIPTORS))
            tracereplay.REPLAY_FILE_DESCRIPTORS.append(ret)
        apply_return_conditions(pid, syscall_object)
    else:
        logging.info('Not replaying this system call')

def accept_exit_handler(syscall_id, syscall_object, pid):
    pass
