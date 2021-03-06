# pylint: disable=W0613, C0302
# unused arguments, too many ines

"""File manipulation handlers
"""


from __future__ import print_function
from time import strptime, mktime

from getdents_parser import parse_getdents_structure
from os_dict import FCNTL64_INT_TO_CMD
from os_dict import PERM_INT_TO_PERM
from os_dict import STAT_CONST
from os_dict import MAGIC_NAME_TO_MAGIC
from errno_dict import ERRNO_CODES

# from util import *
from util import (cleanup_quotes,
                  ReplayDeltaError,
                  logging,
                  cint,
                  noop_current_syscall,
                  apply_return_conditions,
                  should_replay_based_on_fd,
                  cleanup_return_value,
                  validate_integer_argument,
                  find_arg_matching_string,
                  peek_string,
                  is_file_mmapd_at_any_time,
                  swap_trace_fd_to_execution_fd,
                  add_replay_fd,
                  add_os_fd_mapping,
                  remove_replay_fd,
                  remove_os_fd_mapping,
                  offset_file_descriptor,)


def eventfd2_entry_handler(syscall_id, syscall_object, pid):
    """Replay Always
    Checks:
    0: unsigned int initval: initial kernel counter value
    Sets:
    return value: new file descriptor or -1 (error)
        (added as replay file descriptor)
    errno

    Not Implemented:
    * Check int flags value
    """

    logging.debug('Entering eventfd2 entry handler')
    validate_integer_argument(pid, syscall_object, 0, 0)
    add_replay_fd(int(syscall_object.ret[0]))
    noop_current_syscall(pid)
    apply_return_conditions(pid, syscall_object)


def ftruncate_entry_handler(syscall_id, syscall_object, pid):
    """Replay Optional - File Descriptor Dependent
    Checks:
    0: int fd: file descriptor
    1: off_t length: length after truncate
    Sets:
    if replayed:
    return value: 0 (success) or -1 (error)
    errno
    if not replayed:
    call exit handler
    """

    logging.debug('Entering ftruncate entry handler')
    validate_integer_argument(pid, syscall_object, 0, 0)
    validate_integer_argument(pid, syscall_object, 1, 1)
    if should_replay_based_on_fd(int(syscall_object.args[0].value)):
        logging.debug('Replaying this system call')
        noop_current_syscall(pid)
        apply_return_conditions(pid, syscall_object)
    else:
        logging.debug('Not replaying this system call')
        swap_trace_fd_to_execution_fd(pid, 0, syscall_object)


def ftruncate_exit_handler(syscall_id, syscall_object, pid):
    """Used only if not replayed
    Checks:
    return value: 0 (success) or -1 (error)
    Sets:
    None
    """

    logging.debug('Entering ftruncate exit handler')
    ret_val_from_trace = int(syscall_object.ret[0])
    ret_val_from_execution = cint.peek_register(pid, cint.EAX)
    if ret_val_from_trace != ret_val_from_execution:
        raise ReplayDeltaError('Return value from trace ({}) does not match '
                               'return value from execution ({})'
                               .format(ret_val_from_trace,
                                       ret_val_from_execution))


def ftruncate64_entry_handler(syscall_id, syscall_object, pid):
    """Replay Optional - File Descriptor Dependent
    Checks:
    0: int fd: file descriptor
    1: off64_t length: length after truncate
    Sets:
    if replayed:
    return value: 0 (success) or -1 (error)
    errno
    if not replayed:
    call exit handler
    """

    logging.debug('Entering ftruncate entry handler')
    validate_integer_argument(pid, syscall_object, 0, 0)
    validate_integer_argument(pid, syscall_object, 1, 1)
    if should_replay_based_on_fd(int(syscall_object.args[0].value)):
        logging.debug('Replaying this system call')
        noop_current_syscall(pid)
        apply_return_conditions(pid, syscall_object)
    else:
        logging.debug('Not replaying this system call')
        swap_trace_fd_to_execution_fd(pid, 0, syscall_object)


def ftruncate64_exit_handler(syscall_id, syscall_object, pid):
    """Used only if not replayed
    Checks:
    return value: 0 (success) or -1 (failure)
    Sets:
    None
    """
    logging.debug('Entering ftruncate exit handler')
    ret_val_from_trace = int(syscall_object.ret[0])
    ret_val_from_execution = cint.peek_register(pid, cint.EAX)
    if ret_val_from_trace != ret_val_from_execution:
        raise ReplayDeltaError('Return value from trace ({}) does not match '
                               'return value from execution ({})'
                               .format(ret_val_from_trace,
                                       ret_val_from_execution))


def creat_entry_handler(syscall_id, syscall_object, pid):
    """ Replay Optional - is new file or device mmapped at any time
    Checks:
    0: char* pathname: pathname of file or device being created
    Sets:
    if replayed:
    return value: file descriptor or -1 (error)
        (added as replay file descriptor)
    errno
    if not replayed:
    None

    Not Implemented:
    * Check mode_t mode value
    """

    logging.debug('Entering creat entry handler')
    filename_from_trace = cleanup_quotes(syscall_object.args[0].value)
    filename_from_execution = peek_string(pid, cint.peek_register(pid,
                                                                  cint.EBX))
    logging.debug('Filename from trace: %s', filename_from_trace)
    logging.debug('Filename from execution: %s', filename_from_execution)
    if filename_from_trace != filename_from_execution:
        raise ReplayDeltaError('Filename from trace ({}) does not match '
                               'filename from execution ({})'
                               .format(filename_from_trace,
                                       filename_from_execution))
    if not is_file_mmapd_at_any_time(filename_from_trace):
        logging.debug('File is not mmapped at any time, will replay')
        noop_current_syscall(pid)
        apply_return_conditions(pid, syscall_object)
        add_replay_fd(syscall_object.ret[0])


def unlinkat_entry_handler(syscall_id, syscall_object, pid):
    logging.debug('Entering unlinkat entry handler')
    name_from_execution = peek_string(pid,
                                      cint.peek_register(pid,
                                                         cint.ECX))
    name_from_trace = cleanup_quotes(syscall_object.args[1].value)
    logging.debug('Name from execution: %s', name_from_execution)
    logging.debug('Name from trace: %s', name_from_trace)
    if name_from_execution != name_from_trace:
        raise ReplayDeltaError('Name from execution ({}) does not match '
                               'name from trace ({})'
                               .format(name_from_execution,
                                       name_from_trace))
    if not syscall_object.args[0].value == 'AT_FDCWD':
        if not should_replay_based_on_fd(int(syscall_object.args[0].value)) \
           or is_file_mmapd_at_any_time(name_from_trace):
            logging.debug('Not replaying this system call')
            swap_trace_fd_to_execution_fd(pid, 0, syscall_object)
    else:
        logging.debug('Replaying this system call')
        noop_current_syscall(pid)
        apply_return_conditions(pid, syscall_object)


def unlink_entry_handler(syscall_id, syscall_object, pid):
    logging.debug('Entering unlink entry handler')
    name_from_execution = peek_string(pid,
                                      cint.peek_register(pid,
                                                         cint.EBX))
    name_from_trace = cleanup_quotes(syscall_object.args[0].value)
    logging.debug('Name from execution: %s', name_from_execution)
    logging.debug('Name from trace: %s', name_from_trace)
    if name_from_execution != name_from_trace:
        raise ReplayDeltaError('Name from execution ({}) does not match '
                               'name from trace ({})'
                               .format(name_from_execution,
                                       name_from_trace))
    if is_file_mmapd_at_any_time(name_from_trace):
        logging.debug('File is mmap\'d at some point. Will not replay')
    else:
        logging.debug('Replaying this system call')
        noop_current_syscall(pid)
        apply_return_conditions(pid, syscall_object)


def rename_entry_handler(syscall_id, syscall_object, pid):
    logging.debug('entering rename entry handler')
    name1_from_trace = cleanup_quotes(syscall_object.args[0].value)
    name1_from_execution = peek_string(pid,
                                       cint.peek_register(pid,
                                                          cint.EBX))
    name2_from_trace = cleanup_quotes(syscall_object.args[1].value)
    name2_from_execution = peek_string(pid,
                                       cint.peek_register(pid,
                                                          cint.ECX))
    if name1_from_execution != name1_from_trace:
        raise ReplayDeltaError('Name1 from execution ({}) does not match '
                               'name1 from trace ({})'
                               .format(name1_from_execution,
                                       name1_from_trace))
    if name2_from_execution != name2_from_trace:
        raise ReplayDeltaError('Name2 from execution ({}) does not match '
                               'name2 from trace ({})'
                               .format(name2_from_execution,
                                       name2_from_trace))
    if is_file_mmapd_at_any_time(name1_from_trace) or \
       is_file_mmapd_at_any_time(name2_from_trace):
        logging.debug('One of the involved filenames is mmapd at some point '
                      'will not replay system call')
    else:
        logging.debug('Replaying this system call')
        noop_current_syscall(pid)
        apply_return_conditions(pid, syscall_object)


def mkdir_entry_handler(syscall_id, syscall_object, pid):
    logging.debug('Entering mkdir entry handler')
    noop_current_syscall(pid)
    apply_return_conditions(pid, syscall_object)


def writev_entry_handler(syscall_id, syscall_object, pid):
    logging.debug('Entering writev entry handler')
    # Validate file descriptor
    validate_integer_argument(pid, syscall_object, 0, 0)
    # Validate iovec count
    validate_integer_argument(pid,
                              syscall_object,
                              len(syscall_object.args)-1,
                              2)
    vectors = int(syscall_object.args[-1].value)
    args = syscall_object.args[1:-1]
    logging.debug(args)
    datas = [args[x].value for x in range(0, len(args), 2)]
    datas[0] = datas[0].lstrip('[{')
    datas = [x.lstrip('{') for x in datas]
    datas = [x.lstrip('"').rstrip('"') for x in datas]
    datas = [x.decode('string-escape').encode('hex') for x in datas]
    lengths = [args[x].value for x in range(1, len(args), 2)]
    lengths[0] = lengths[0][0]
    lengths = [int(x.rstrip('}]')) for x in lengths]
    logging.debug('Vectors: %d', vectors)
    logging.debug('Datas: %s', datas)
    logging.debug('Lengths: %s', lengths)
    addr = cint.peek_register(pid, cint.ECX)
    logging.debug('Addr: %d', addr)
    vector_addresses = []
    for i in range(vectors):
        vector_addresses.append(cint.peek_address(pid, addr + (i * 8)))
    # We may need to copy buffers over manually at some point.
    # Working for now.
    fd = int(syscall_object.args[0].value)
    if should_replay_based_on_fd(fd):
        logging.debug('We will replay this system call')
        noop_current_syscall(pid)
        apply_return_conditions(pid, syscall_object)
    else:
        logging.debug('Not replaying this system call')
        swap_trace_fd_to_execution_fd(pid, 0, syscall_object)


def writev_exit_handler(syscall_id, syscall_object, pid):
    logging.debug('Entering writev_exit_handler (does nothing)')


def pipe_entry_handler(syscall_id, syscall_object, pid):
    logging.debug('Entering pipe entry handler')
    read_end_from_trace = int(syscall_object.args[0].value)
    write_end_from_trace = int(syscall_object.args[1].value.strip(']'))
    if is_mmapd_before_close(read_end_from_trace,
                             tracereplay.system_calls) \
       or is_mmapd_before_close(write_end_from_trace,
                                tracereplay.system_calls):
        raise NotImplementedError('mmap() on file descriptors allocated by '
                                  'pipe() is unsupported')
    logging.debug('Read end from trace: %d', read_end_from_trace)
    logging.debug('Write end from trace: %d', write_end_from_trace)
    array_addr = cint.peek_register(pid, cint.EBX)
    add_replay_fd(read_end_from_trace)
    add_replay_fd(write_end_from_trace)
    noop_current_syscall(pid)
    cint.populate_pipefd_array(pid,
                               array_addr,
                               read_end_from_trace,
                               write_end_from_trace)
    apply_return_conditions(pid, syscall_object)


def dup_entry_handler(syscall_id, syscall_object, pid):
    logging.debug('Entering dup handler')
    validate_integer_argument(pid, syscall_object, 0, 0)
    oldfd = int(syscall_object.args[0].value)
    if should_replay_based_on_fd(oldfd):
        noop_current_syscall(pid)
        returned_fd = int(syscall_object.ret[0])
        add_replay_fd(returned_fd)
        apply_return_conditions(pid, syscall_object)
    else:
        logging.debug('Not replaying this system call')
        swap_trace_fd_to_execution_fd(pid, 0, syscall_object)


def dup_exit_handler(syscall_id, syscall_object, pid):
    logging.debug('Entering dup exit handler')
    exec_fd = cint.peek_register(pid, cint.EAX)
    trace_fd = int(syscall_object.ret[0])
    logging.debug('Execution return value: %d', exec_fd)
    logging.debug('Trace return value: %d', trace_fd)

    if exec_fd != trace_fd:
        raise Exception('Return value from execution ({}) differs from '
                        'return value from trace ({})'
                        .format(exec_fd,
                                trace_fd))
    if exec_fd >= 0:
        add_os_fd_mapping(exec_fd, trace_fd)
    cint.poke_register(pid, cint.EAX, trace_fd)


def close_entry_handler(syscall_id, syscall_object, pid):
    logging.debug('Entering close entry handler')
    validate_integer_argument(pid, syscall_object, 0, 0)
    fd_from_trace = int(syscall_object.args[0].value)
    # We always replay unsuccessful close calls
    if int(syscall_object.ret[0]) == -1 \
       or should_replay_based_on_fd(fd_from_trace):
        noop_current_syscall(pid)
        if syscall_object.ret[0] != -1:
            logging.debug('Got successful close call')
            remove_replay_fd(fd_from_trace)
        else:
            logging.debug('Replaying unsuccessful close call')
        apply_return_conditions(pid, syscall_object)
    else:
        logging.info('Not replaying this system call')
        swap_trace_fd_to_execution_fd(pid, 0, syscall_object)


def close_exit_handler(syscall_id, syscall_object, pid):
    logging.debug('Entring close exit handler')
    ret_val_from_trace = syscall_object.ret[0]
    ret_val_from_execution = cint.peek_register(pid, cint.EAX)
    logging.debug('Return value from trace: %d', ret_val_from_trace)
    logging.debug('Return value from execution: %d', ret_val_from_execution)
    check_ret_val_from_trace = ret_val_from_trace
    if syscall_object.ret[0] == -1:
        logging.debug('Got unsuccessful close exit')
        errno_ret = (ERRNO_CODES[syscall_object.ret[1]] * -1)
        logging.debug('Errno return value: %d', errno_ret)
        check_ret_val_from_trace = errno_ret
    if ret_val_from_execution != check_ret_val_from_trace:
        raise Exception('Return value from execution ({}) differs from '
                        'Return value from trace ({})'
                        .format(ret_val_from_execution,
                                check_ret_val_from_trace))
    remove_os_fd_mapping(int(syscall_object.args[0].value))


def read_entry_handler(syscall_id, syscall_object, pid):
    fd = cint.peek_register(pid, cint.EBX)
    fd_from_trace = syscall_object.args[0].value
    logging.debug('File descriptor from execution: %s', fd)
    logging.debug('File descriptor from trace: %s', fd_from_trace)
    if should_replay_based_on_fd(fd_from_trace):
        ret_val = cleanup_return_value(syscall_object.ret[0])
        noop_current_syscall(pid)
        if ret_val != -1:
            # file descriptor
            validate_integer_argument(pid, syscall_object, 0, 0)
            # bytes to read
            validate_integer_argument(pid, syscall_object, 2, 2)
            buffer_address = cint.peek_register(pid, cint.ECX)
            buffer_size_from_execution = cint.peek_register(pid,
                                                            cint.EDX)
            buffer_size_from_trace = int(syscall_object.args[2].value)
            logging.debug('Address: %x', buffer_address & 0xffffffff)
            logging.debug('Buffer size from execution: %d',
                          buffer_size_from_execution)
            logging.debug('Buffer size from trace: %d', buffer_size_from_trace)
            data = syscall_object.args[1].value
            data = cleanup_quotes(data)
            data = data.decode('string_escape')
            if len(data) != ret_val:
                raise ReplayDeltaError('Decoded bytes length ({}) does not '
                                       'equal return value from trace ({})'
                                       .format(len(data), ret_val))
            cint.populate_char_buffer(pid,
                                      buffer_address,
                                      data)
            buf = cint.copy_address_range(pid,
                                          buffer_address,
                                          buffer_address + ret_val)
            if buf != data:
                raise ReplayDeltaError('Data copied by read() handler doesn\'t'
                                       ' match after copy')
        apply_return_conditions(pid, syscall_object)
    else:
        logging.debug("Ignoring read call to untracked file descriptor")
        swap_trace_fd_to_execution_fd(pid, 0, syscall_object)


def readv_entry_handler(syscall_id, syscall_object, pid):
    logging.debug('Entering readv entry handler')
    validate_integer_argument(pid, syscall_object, 0, 0)
    if syscall_object.ret[0] != -1:
        addr = cint.peek_register(pid, cint.ECX)
        logging.debug('Addr: %x', addr & 0xffffffff)
        iovs = _collect_readv_iovs(syscall_object)
        print(len(iovs[1]['iov_data']))
        print(iovs)
        noop_current_syscall(pid)
        cint.populate_readv_vectors(pid,
                                    addr,
                                    iovs)
        apply_return_conditions(pid, syscall_object)
    else:
        swap_trace_fd_to_execution_fd(pid, 0, syscall_object)


def _collect_readv_iovs(syscall_object):
    iov_count = int(syscall_object.args[-1].value)
    tmp = []
    for i in range(1, len(syscall_object.args)-1, 2):
        iov_data = syscall_object.args[i].value.split('"', 1)[1]
        iov_data = iov_data.rsplit('"', 1)[0].decode('string-escape')
        iov_len = syscall_object.args[i+1].value
        if isinstance(iov_len, list):
            iov_len = iov_len[0]
        iov_len = int(iov_len.strip('\'[]{}'))
        if len(iov_data) != iov_len:
            raise ReplayDeltaError('Length of parsed iov_data ({}) does not '
                                   'match specified length ({})'
                                   .format(len(iov_data),
                                           iov_len))
        tmp += [{'iov_data': iov_data, 'iov_len': iov_len}]
    if len(tmp) != iov_count:
        raise ReplayDeltaError('Number of iovs parsed ({}) does not match'
                               'specified number ({})'.format(len(tmp),
                                                              iov_count))
    return tmp


# Note: This handler only takes action on syscalls made to file descriptors we
# are tracking. Otherwise it simply does any required debug-printing and lets
# it execute
def write_entry_handler(syscall_id, syscall_object, pid):
    validate_integer_argument(pid, syscall_object, 0, 0)
    validate_integer_argument(pid, syscall_object, 2, 2)
    bytes_addr = cint.peek_register(pid, cint.ECX)
    bytes_len = cint.peek_register(pid, cint.EDX)
    bytes_from_trace = cleanup_quotes(syscall_object.args[1].value)
    bytes_from_execution = cint.copy_address_range(pid,
                                                   bytes_addr,
                                                   bytes_addr + bytes_len)
    bytes_from_trace = bytes_from_trace.decode('string-escape')
    logging.debug(bytes_from_trace.encode('hex'))
    logging.debug(bytes_from_execution.encode('hex'))
    if bytes_from_trace != bytes_from_execution:
        raise ReplayDeltaError('Bytes from trace don\'t match bytes from '
                               'execution!')
    fd = int(syscall_object.args[0].value)
    if should_replay_based_on_fd(fd):
        # Print the bytes if writing to stdout or stderr so output is visible
        if fd == 1 or fd == 2:
            print(bytes_from_trace)
        noop_current_syscall(pid)
        apply_return_conditions(pid, syscall_object)
    else:
        logging.debug('Ignoring write to un-replayed file descriptor')
        swap_trace_fd_to_execution_fd(pid, 0, syscall_object)


# Once again, this only has to be here until the new "open" machinery
# is in place
def write_exit_handler(syscall_id, syscall_object, pid):
    logging.debug('Entering write exit handler')
    ret_val = cint.peek_register(pid, cint.EAX)
    ret_val_from_trace = int(syscall_object.ret[0])
    logging.debug('Return value from execution: %d', ret_val)
    logging.debug('Return value from trace: %d', ret_val_from_trace)
    if ret_val != ret_val_from_trace:
        raise ReplayDeltaError('Return value from execution ({}) differed '
                               'from return value from trace ({})'
                               .format(ret_val, ret_val_from_trace))


def llseek_entry_handler(syscall_id, syscall_object, pid):
    logging.debug('Entering llseek entry handler')
    if should_replay_based_on_fd(int(syscall_object.args[0].value)):
        logging.debug('Call using replayed file descriptor. Replaying this '
                      'system call')
        noop_current_syscall(pid)
        if syscall_object.ret[0] != -1:
            result = int(syscall_object.args[2].value.strip('[]'))
            result_addr = int(cint.peek_register(pid, cint.ESI))
            logging.debug('result: %s', result)
            logging.debug('result_addr: %s', result_addr)
            logging.debug('Got successful llseek call')
            logging.debug('Populating result')
            cint.populate_llseek_result(pid, result_addr, result)
        else:
            logging.debug('Got unsucceesful llseek call')
        apply_return_conditions(pid, syscall_object)
    else:
        logging.debug('Not replaying this system call')
        swap_trace_fd_to_execution_fd(pid, 0, syscall_object)


def llseek_exit_handler(syscall_id, syscall_object, pid):
    logging.debug('llseek exit handler doesn\'t do anything')


def getcwd_entry_handler(syscall_id, syscall_object, pid):
    logging.debug('Entering getcwd entry handler')
    array_addr = cint.peek_register(pid, cint.EBX)
    data = str(syscall_object.args[0].value.strip('"'))
    data_length = int(syscall_object.ret[0])
    noop_current_syscall(pid)
    if data_length != 0:
        logging.debug('Got successful getcwd call')
        logging.debug('Data: %s', data)
        data = data + '\0'
        logging.debug('Data length: %s', data_length)
        logging.debug('Populating character array')
        cint.populate_char_buffer(pid,
                                  array_addr,
                                  data)
    else:
        logging.debug('Got unsuccessful getcwd call')
    apply_return_conditions(pid, syscall_object)


def readlink_entry_handler(syscall_id, syscall_object, pid):
    """Concerns: We always replay. There could be issues around files that are
    mmap()'d at some point
    """
    logging.debug('Entering readlink entry handler')
    ebx = cint.peek_register(pid, cint.EBX)
    # Check the filename
    fn_from_execution = peek_string(pid, ebx)
    fn_from_trace = cleanup_quotes(syscall_object.args[0].value)
    if fn_from_execution != fn_from_trace:
        raise ReplayDeltaError('File name from execution ({}) does not match '
                               'file name from trace ({})'
                               .format(fn_from_execution, fn_from_trace))
    array_addr = cint.peek_register(pid, cint.ECX)
    data = cleanup_quotes(syscall_object.args[1].value)
    data_length = int(syscall_object.ret[0])
    noop_current_syscall(pid)
    if data_length != -1:
        logging.debug('Got successful readlink call')
        logging.debug('Data: %s', data)
        logging.debug('Data length: %s', data_length)
        logging.debug('Populating character array')
        cint.populate_char_buffer(pid,
                                  array_addr,
                                  data)
    else:
        logging.debug('Got unsuccessful readlink call')
    apply_return_conditions(pid, syscall_object)


def statfs64_entry_handler(syscall_id, syscall_object, pid):
    logging.debug('Entering statfs64 handler')
    ebx = cint.peek_register(pid, cint.EBX)
    ecx = cint.peek_register(pid, cint.ECX)
    edx = cint.peek_register(pid, cint.EDX)
    edi = cint.peek_register(pid, cint.EDI)
    esi = cint.peek_register(pid, cint.ESI)
    logging.debug("EBX: %s, ECX: %s, EDX: %s, ESI: %s, EDI: %s",
                  ebx, ecx, edx, edi, esi)
    addr = edx
    noop_current_syscall(pid)
    if syscall_object.ret[0] == -1:
        logging.debug('Got unsuccessful statfs64 call')
    else:
        logging.debug('Got successful statfs64 call')
        idx, arg = find_arg_matching_string(syscall_object.args[1:],
                                            'f_type')[0]
        f_type = arg
        f_type = f_type[f_type.rfind('=')+1:]
        f_type = f_type.strip('{}')
        f_type = _cleanup_f_type(f_type)

        idx, arg = find_arg_matching_string(syscall_object.args[1:],
                                            'f_bsize')[0]
        f_bsize = arg
        f_bsize = int(f_bsize[f_bsize.rfind('=')+1:])
        logging.debug('f_bsize: %d', f_bsize)

        idx, arg = find_arg_matching_string(syscall_object.args[1:],
                                            'f_blocks')[0]
        f_blocks = arg
        f_blocks = int(f_blocks[f_blocks.rfind('=')+1:])
        logging.debug('f_blocks: %d', f_blocks)

        idx, arg = find_arg_matching_string(syscall_object.args[1:],
                                            'f_bfree')[0]
        f_bfree = arg
        f_bfree = int(f_bfree[f_bfree.rfind('=')+1:])
        logging.debug('f_bfree: %d', f_bfree)

        idx, arg = find_arg_matching_string(syscall_object.args[1:],
                                            'f_bavail')[0]
        f_bavail = arg
        f_bavail = int(f_bavail[f_bavail.rfind('=')+1:])
        logging.debug('f_bavail: %d', f_bavail)

        idx, arg = find_arg_matching_string(syscall_object.args[1:],
                                            'f_files')[0]
        f_files = arg
        f_files = int(f_files[f_files.rfind('=')+1:])
        logging.debug('f_files: %d', f_files)

        idx, arg = find_arg_matching_string(syscall_object.args[1:],
                                            'f_ffree')[0]
        f_ffree = arg
        f_ffree = int(f_ffree[f_ffree.rfind('=')+1:])
        logging.debug('f_ffree: %d', f_ffree)

        idx, arg = find_arg_matching_string(syscall_object.args[1:],
                                            'f_fsid')[0]
        f_fsid0 = arg
        f_fsid0 = int(f_fsid0.split('{')[1])

        f_fsid1 = int(syscall_object.args[idx+2].value.rstrip('}'))

        logging.debug('f_fsid1: %s', f_fsid0)
        logging.debug('f_fsid2: %s', f_fsid1)

        idx, arg = find_arg_matching_string(syscall_object.args[1:],
                                            'f_namelen')[0]
        f_namelen = arg
        f_namelen = int(f_namelen[f_namelen.rfind('=')+1:])
        logging.debug('f_namelen: %d', f_namelen)

        idx, arg = find_arg_matching_string(syscall_object.args[1:],
                                            'f_frsize')[0]
        f_frsize = arg
        f_frsize = int(f_frsize[f_frsize.rfind('=')+1:])
        logging.debug('f_frsize: %d', f_frsize)

        idx, arg = find_arg_matching_string(syscall_object.args[1:],
                                            'f_flags')[0]
        f_flags = arg
        f_flags = int(f_flags[f_flags.rfind('=')+1:].rstrip('}'))

        logging.debug('f_flags: %d', f_flags)
        logging.debug('pid: %d', pid)
        logging.debug('addr: %x', addr & 0xffffffff)
        cint.populate_statfs64_structure(pid,
                                         addr,
                                         f_type,
                                         f_bsize,
                                         f_blocks,
                                         f_bfree,
                                         f_bavail,
                                         f_files,
                                         f_ffree,
                                         f_fsid0,
                                         f_fsid1,
                                         f_namelen,
                                         f_frsize,
                                         f_flags)
    apply_return_conditions(pid, syscall_object)


def open_entry_handler(syscall_id, syscall_object, pid):
    logging.debug('Entering open entry handler')
    ebx = cint.peek_register(pid, cint.EBX)
    fn_from_execution = peek_string(pid, ebx)
    fn_from_trace = syscall_object.args[0].value.strip('"')
    logging.debug('Filename from trace: %s', fn_from_trace)
    logging.debug('Filename from execution: %s', fn_from_execution)
    if fn_from_execution != fn_from_trace:
        raise Exception('File name from execution ({}) differs from '
                        'file name from trace ({})'.format(fn_from_execution,
                                                           fn_from_trace))
    fd_from_trace = int(syscall_object.ret[0])
    if fd_from_trace == -1 or not is_file_mmapd_at_any_time(fn_from_trace):
        if fd_from_trace == -1:
            logging.debug('This is an unsuccessful open call. We will replay '
                          'it')
        else:
            logging.debug('File descriptor is not mmap\'d before it is closed '
                          'so we will replay it')
            add_replay_fd(fd_from_trace)
        noop_current_syscall(pid)
        apply_return_conditions(pid, syscall_object)
    else:
        logging.debug('Resultant file descriptor is mmap\'d before close. '
                      'Will not replay')


def open_exit_handler(syscall_id, syscall_object, pid):
    logging.debug('Entering open exit handler')
    ret_val_from_trace = int(syscall_object.ret[0])
    ret_val_from_execution = cint.peek_register(pid, cint.EAX)
    if ret_val_from_trace == -1:
        errno_ret = (ERRNO_CODES[syscall_object.ret[1]] * -1)
        logging.debug('Errno return value: %d', errno_ret)
        check_ret_val_from_trace = errno_ret
    else:
        check_ret_val_from_trace = offset_file_descriptor(ret_val_from_trace)
    logging.debug('Return value from execution: %d', ret_val_from_execution)
    logging.debug('Return value from trace: %d', ret_val_from_trace)
    logging.debug('Check return value from trace: %d',
                  check_ret_val_from_trace)
    if ret_val_from_execution >= 0:
        add_os_fd_mapping(ret_val_from_execution, ret_val_from_trace)
    cint.poke_register(pid, cint.EAX, ret_val_from_trace)


def openat_entry_handler(syscall_id, syscall_object, pid):
    logging.debug('Entering openat entry handler')
    ecx = cint.peek_register(pid, cint.ECX)
    fn_from_execution = peek_string(pid, ecx)
    fn_from_trace = syscall_object.args[1].value.strip('"')
    logging.debug('Filename from trace: %s', fn_from_trace)
    logging.debug('Filename from execution: %s', fn_from_execution)
    if fn_from_execution != fn_from_trace:
        raise Exception('File name from execution ({}) differs from '
                        'file name from trace ({})'.format(fn_from_execution,
                                                           fn_from_trace))
    fd_from_trace = int(syscall_object.ret[0])
    if fd_from_trace == -1 or not is_file_mmapd_at_any_time(fn_from_trace):
        if fd_from_trace == -1:
            logging.debug('This is an unsuccessful open call. We will replay '
                          'it')
        else:
            logging.debug('File descriptor is not mmap\'d before it is closed '
                          'so we will replay it')
            add_replay_fd(fd_from_trace)
        noop_current_syscall(pid)
        apply_return_conditions(pid, syscall_object)
    else:
        logging.debug('Resultant file descriptor is mmap\'d before close. '
                      'Will not replay')


def openat_exit_handler(syscall_id, syscall_object, pid):
    logging.debug('Entering openat exit handler')
    ret_val_from_trace = int(syscall_object.ret[0])
    ret_val_from_execution = cint.peek_register(pid, cint.EAX)
    if ret_val_from_trace == -1:
        errno_ret = (ERRNO_CODES[syscall_object.ret[1]] * -1)
        logging.debug('Errno return value: %d', errno_ret)
        check_ret_val_from_trace = errno_ret
    else:
        check_ret_val_from_trace = offset_file_descriptor(ret_val_from_trace)
    logging.debug('Return value from execution: %d', ret_val_from_execution)
    logging.debug('Return value from trace: %d', ret_val_from_trace)
    logging.debug('Check return value from trace: %d',
                  check_ret_val_from_trace)
    if ret_val_from_execution >= 0:
        add_os_fd_mapping(ret_val_from_execution, ret_val_from_trace)
    cint.poke_register(pid, cint.EAX, ret_val_from_trace)


def fstat64_entry_handler(syscall_id, syscall_object, pid):
    logging.debug('Entering fstat64 handler')
    if not should_replay_based_on_fd(int(syscall_object.args[0].value)):
        swap_trace_fd_to_execution_fd(pid, 0, syscall_object)
        return
    buf_addr = cint.peek_register(pid, cint.ECX)
    logging.debug('ECX: %x', (buf_addr & 0xffffffff))
    if syscall_object.ret[0] == -1:
        logging.debug('Got unsuccessful fstat64 call')
    else:
        logging.debug('Got successful fstat64 call')
        # There should always be an st_dev
        idx, arg = find_arg_matching_string(syscall_object.args[1:],
                                            'st_dev')[0]
        st_dev1 = arg
        st_dev1 = int(st_dev1.split('(')[1])
        # must increment idx by 2 in order to account for slicing out the
        # initial file descriptor
        st_dev2 = syscall_object.args[idx+2].value
        st_dev2 = int(st_dev2.strip(')'))
        logging.debug('st_dev1: %s', st_dev1)
        logging.debug('st_dev2: %s', st_dev2)

        # st_rdev is optional
        st_rdev1 = 0
        st_rdev2 = 0
        r = find_arg_matching_string(syscall_object.args[1:],
                                     'st_rdev')
        if len(r) > 0:
            idx, arg = r[0]
            logging.debug('We have a st_rdev argument')
            st_rdev1 = arg
            st_rdev1 = int(st_rdev1.split('(')[1])
            st_rdev2 = syscall_object.args[idx+2].value
            st_rdev2 = int(st_rdev2.strip(')'))
            logging.debug('st_rdev1: %d', st_rdev1)
            logging.debug('st_rdev2: %d', st_rdev2)

        # st_ino
        r = find_arg_matching_string(syscall_object.args[1:],
                                     'st_ino')
        idx, arg = r[0]
        st_ino = int(arg.split('=')[1])
        logging.debug('st_ino: %d', st_ino)

        # st_mode
        r = find_arg_matching_string(syscall_object.args[1:],
                                     'st_mode')
        idx, arg = r[0]
        st_mode = int(cleanup_st_mode(arg.split('=')[1]))
        logging.debug('st_mode: %d', st_mode)

        # st_nlink
        r = find_arg_matching_string(syscall_object.args[1:],
                                     'st_nlink')
        idx, arg = r[0]
        st_nlink = int(arg.split('=')[1])
        logging.debug('st_nlink: %d', st_nlink)

        # st_uid
        r = find_arg_matching_string(syscall_object.args[1:],
                                     'st_uid')
        idx, arg = r[0]
        st_uid = int(arg.split('=')[1])
        logging.debug('st_uid: %d', st_uid)

        # st_gid
        r = find_arg_matching_string(syscall_object.args[1:],
                                     'st_gid')
        idx, arg = r[0]
        st_gid = int(arg.split('=')[1])
        logging.debug('st_gid: %d', st_gid)

        # st_blocksize
        r = find_arg_matching_string(syscall_object.args[1:],
                                     'st_blksize')
        idx, arg = r[0]
        st_blksize = int(arg.split('=')[1])
        logging.debug('st_blksize: %d', st_blksize)

        # st_blocks
        r = find_arg_matching_string(syscall_object.args[1:],
                                     'st_blocks')
        idx, arg = r[0]
        st_blocks = int(arg.split('=')[1])
        logging.debug('st_block: %d', st_blocks)

        # st_size is optional
        r = find_arg_matching_string(syscall_object.args[1:],
                                     'st_size')
        if len(r) >= 1:
            idx, arg = r[0]
            st_size = int(arg.split('=')[1])
            logging.debug('st_size: %d', st_size)
        else:
            st_size = 0
            logging.debug('optional st_size not present')
        # st_atime
        r = find_arg_matching_string(syscall_object.args[1:],
                                     'st_atime')
        idx, arg = r[0]
        value = arg.split('=')[1]
        if value == '0':
            logging.debug('Got zero st_atime')
            st_atime = 0
        else:
            logging.debug('Got normal st_atime')
            st_atime = int(mktime(strptime(value, '%Y/%m/%d-%H:%M:%S')))
        logging.debug('st_atime: %d', st_atime)

        # st_mtime
        r = find_arg_matching_string(syscall_object.args[1:],
                                     'st_mtime')
        idx, arg = r[0]
        value = arg.split('=')[1]
        if value == '0':
            logging.debug('Got zero st_mtime')
            st_mtime = 0
        else:
            logging.debug('Got normal st_mtime')
            st_mtime = int(mktime(strptime(value, '%Y/%m/%d-%H:%M:%S')))
        logging.debug('st_mtime: %d', st_mtime)

        # st_ctime
        r = find_arg_matching_string(syscall_object.args[1:],
                                     'st_ctime')
        idx, arg = r[0]
        value = arg.split('=')[1].strip('}')
        if value == '0':
            logging.debug('Got zero st_ctime')
            st_ctime = 0
        else:
            logging.debug('Got normal st_ctime')
            st_ctime = int(mktime(strptime(value, '%Y/%m/%d-%H:%M:%S')))
        logging.debug('st_ctime: %d', st_ctime)

        logging.debug('Injecting values into structure')
        logging.debug('pid: %d', pid)
        logging.debug('addr: %d', buf_addr)
        cint.populate_stat64_struct(pid,
                                    buf_addr,
                                    int(st_dev1),
                                    int(st_dev2),
                                    st_blocks,
                                    st_nlink,
                                    st_gid,
                                    st_blksize,
                                    int(st_rdev1),
                                    int(st_rdev2),
                                    st_size,
                                    st_mode,
                                    st_uid,
                                    st_ino,
                                    st_ctime,
                                    st_mtime,
                                    st_atime)
    noop_current_syscall(pid)
    apply_return_conditions(pid, syscall_object)


def fstatat64_entry_handler(syscall_id, syscall_object, pid):
    logging.debug('Entering fstatat64 handler')
    if not syscall_object.args[0].value == 'AT_FDCWD':
        if not should_replay_based_on_fd(int(syscall_object.args[0].value)):
            swap_trace_fd_to_execution_fd(pid, 0, syscall_object)
            return
    # At this point we replay calls with either AT_FDCWD or replay fds
    buf_addr = cint.peek_register(pid, cint.EDX)
    logging.debug('EDX: %x', (buf_addr & 0xffffffff))
    # TODO: Check path name
    if syscall_object.ret[0] == -1:
        logging.debug('Got unsuccessful fstatat64 call')
    else:
        # HACK: Delete path name so everything lines up nicely
        syscall_object.args = list(syscall_object.args)
        del(syscall_object.args[1])
        syscall_object.args = tuple(syscall_object.args)
        logging.debug('Got successful fstatat64 call')
        # There should always be an st_dev
        idx, arg = find_arg_matching_string(syscall_object.args[1:],
                                            'st_dev')[0]
        st_dev1 = arg
        st_dev1 = int(st_dev1.split('(')[1])
        # must increment idx by 2 in order to account for slicing out the
        # initial file descriptor
        st_dev2 = syscall_object.args[idx+2].value[0]
        st_dev2 = int(st_dev2.strip(')'))
        logging.debug('st_dev1: %s', st_dev1)
        logging.debug('st_dev2: %s', st_dev2)

        # st_rdev is optional
        st_rdev1 = 0
        st_rdev2 = 0
        r = find_arg_matching_string(syscall_object.args[1:],
                                     'st_rdev')
        if len(r) > 0:
            idx, arg = r[0]
            logging.debug('We have a st_rdev argument')
            st_rdev1 = arg
            st_rdev1 = int(st_rdev1.split('(')[1])
            st_rdev2 = syscall_object.args[idx+2].value
            st_rdev2 = int(st_rdev2.strip(')'))
            logging.debug('st_rdev1: %d', st_rdev1)
            logging.debug('st_rdev2: %d', st_rdev2)

        # st_ino
        r = find_arg_matching_string(syscall_object.args[1:],
                                     'st_ino')
        idx, arg = r[0]
        st_ino = int(arg.split('=')[1])
        logging.debug('st_ino: %d', st_ino)

        # st_mode
        r = find_arg_matching_string(syscall_object.args[1:],
                                     'st_mode')
        idx, arg = r[0]
        st_mode = int(cleanup_st_mode(arg.split('=')[1]))
        logging.debug('st_mode: %d', st_mode)

        # st_nlink
        r = find_arg_matching_string(syscall_object.args[1:],
                                     'st_nlink')
        idx, arg = r[0]
        st_nlink = int(arg.split('=')[1])
        logging.debug('st_nlink: %d', st_nlink)

        # st_uid
        r = find_arg_matching_string(syscall_object.args[1:],
                                     'st_uid')
        idx, arg = r[0]
        st_uid = int(arg.split('=')[1])
        logging.debug('st_uid: %d', st_uid)

        # st_gid
        r = find_arg_matching_string(syscall_object.args[1:],
                                     'st_gid')
        idx, arg = r[0]
        st_gid = int(arg.split('=')[1])
        logging.debug('st_gid: %d', st_gid)

        # st_blocksize
        r = find_arg_matching_string(syscall_object.args[1:],
                                     'st_blksize')
        idx, arg = r[0]
        st_blksize = int(arg.split('=')[1])
        logging.debug('st_blksize: %d', st_blksize)

        # st_blocks
        r = find_arg_matching_string(syscall_object.args[1:],
                                     'st_blocks')
        idx, arg = r[0]
        st_blocks = int(arg.split('=')[1])
        logging.debug('st_block: %d', st_blocks)

        # st_size is optional
        r = find_arg_matching_string(syscall_object.args[1:],
                                     'st_size')
        if len(r) >= 1:
            idx, arg = r[0]
            st_size = int(arg.split('=')[1])
            logging.debug('st_size: %d', st_size)
        else:
            st_size = 0
            logging.debug('optional st_size not present')
        # st_atime
        r = find_arg_matching_string(syscall_object.args[1:],
                                     'st_atime')
        idx, arg = r[0]
        value = arg.split('=')[1]
        if value == '0':
            logging.debug('Got zero st_atime')
            st_atime = 0
        else:
            logging.debug('Got normal st_atime')
            st_atime = int(mktime(strptime(value, '%Y/%m/%d-%H:%M:%S')))
        logging.debug('st_atime: %d', st_atime)

        # st_mtime
        r = find_arg_matching_string(syscall_object.args[1:],
                                     'st_mtime')
        idx, arg = r[0]
        value = arg.split('=')[1]
        if value == '0':
            logging.debug('Got zero st_mtime')
            st_mtime = 0
        else:
            logging.debug('Got normal st_mtime')
            st_mtime = int(mktime(strptime(value, '%Y/%m/%d-%H:%M:%S')))
        logging.debug('st_mtime: %d', st_mtime)

        # st_ctime
        r = find_arg_matching_string(syscall_object.args[1:],
                                     'st_ctime')
        idx, arg = r[0]
        value = arg.split('=')[1].strip('}')
        if value == '0':
            logging.debug('Got zero st_ctime')
            st_ctime = 0
        else:
            logging.debug('Got normal st_ctime')
            st_ctime = int(mktime(strptime(value, '%Y/%m/%d-%H:%M:%S')))
        logging.debug('st_ctime: %d', st_ctime)

        logging.debug('Injecting values into structure')
        logging.debug('pid: %d', pid)
        logging.debug('addr: %d', buf_addr)
        cint.populate_stat64_struct(pid,
                                    buf_addr,
                                    int(st_dev1),
                                    int(st_dev2),
                                    st_blocks,
                                    st_nlink,
                                    st_gid,
                                    st_blksize,
                                    int(st_rdev1),
                                    int(st_rdev2),
                                    st_size,
                                    st_mode,
                                    st_uid,
                                    st_ino,
                                    st_ctime,
                                    st_mtime,
                                    st_atime)
    noop_current_syscall(pid)
    apply_return_conditions(pid, syscall_object)


def stat64_entry_handler(syscall_id, syscall_object, pid):
    # horrible work arouund
    if syscall_object.args[0].value == '"/etc/resolv.conf"':
        logging.error('Workaround for stat64 problem')
        return
    buf_addr = cint.peek_register(pid, cint.ECX)
    logging.debug('ECX: %x', (buf_addr & 0xffffffff))
    if syscall_object.ret[0] == -1:
        logging.debug('Got unsuccessful stat64 call')
    else:
        logging.debug('Got successful stat64 call')
        # There should always be an st_dev
        idx, arg = find_arg_matching_string(syscall_object.args[1:],
                                            'st_dev')[0]
        st_dev1 = arg
        st_dev1 = int(st_dev1.split('(')[1])
        # must increment idx by 2 in order to account for slicing out the
        # initial file descriptor
        st_dev2 = syscall_object.args[idx+2].value
        st_dev2 = int(st_dev2.strip(')'))
        logging.debug('st_dev1: %s', st_dev1)
        logging.debug('st_dev2: %s', st_dev2)

        # st_rdev is optional
        st_rdev1 = 0
        st_rdev2 = 0
        r = find_arg_matching_string(syscall_object.args[1:],
                                     'st_rdev')
        if len(r) > 0:
            idx, arg = r[0]
            logging.debug('We have a st_rdev argument')
            st_rdev1 = arg
            st_rdev1 = int(st_rdev1.split('(')[1])
            st_rdev2 = syscall_object.args[idx+2].value
            st_rdev2 = int(st_rdev2.strip(')'))
            logging.debug('st_rdev1: %d', st_rdev1)
            logging.debug('st_rdev2: %d', st_rdev2)

        # st_ino
        r = find_arg_matching_string(syscall_object.args[1:],
                                     'st_ino')
        idx, arg = r[0]
        st_ino = int(arg.split('=')[1])
        logging.debug('st_ino: %d', st_ino)

        # st_mode
        r = find_arg_matching_string(syscall_object.args[1:],
                                     'st_mode')
        idx, arg = r[0]
        st_mode = int(cleanup_st_mode(arg.split('=')[1]))
        logging.debug('st_mode: %d', st_mode)

        # st_nlink
        r = find_arg_matching_string(syscall_object.args[1:],
                                     'st_nlink')
        idx, arg = r[0]
        st_nlink = int(arg.split('=')[1])
        logging.debug('st_nlink: %d', st_nlink)

        # st_uid
        r = find_arg_matching_string(syscall_object.args[1:],
                                     'st_uid')
        idx, arg = r[0]
        st_uid = int(arg.split('=')[1])
        logging.debug('st_uid: %d', st_uid)

        # st_gid
        r = find_arg_matching_string(syscall_object.args[1:],
                                     'st_gid')
        idx, arg = r[0]
        st_gid = int(arg.split('=')[1])
        logging.debug('st_gid: %d', st_gid)

        # st_blocksize
        r = find_arg_matching_string(syscall_object.args[1:],
                                     'st_blksize')
        idx, arg = r[0]
        st_blksize = int(arg.split('=')[1])
        logging.debug('st_blksize: %d', st_blksize)

        # st_blocks
        r = find_arg_matching_string(syscall_object.args[1:],
                                     'st_blocks')
        idx, arg = r[0]
        st_blocks = int(arg.split('=')[1])
        logging.debug('st_block: %d', st_blocks)

        # st_size is optional
        r = find_arg_matching_string(syscall_object.args[1:],
                                     'st_size')
        if len(r) >= 1:
            idx, arg = r[0]
            st_size = int(arg.split('=')[1])
            logging.debug('st_size: %d', st_size)
        else:
            st_size = 0
            logging.debug('optional st_size not present')
        # st_atime
        r = find_arg_matching_string(syscall_object.args[1:],
                                     'st_atime')
        idx, arg = r[0]
        value = arg.split('=')[1]
        if value == '0':
            logging.debug('Got zero st_atime')
            st_atime = 0
        else:
            logging.debug('Got normal st_atime')
            st_atime = int(mktime(strptime(value, '%Y/%m/%d-%H:%M:%S')))
        logging.debug('st_atime: %d', st_atime)

        # st_mtime
        r = find_arg_matching_string(syscall_object.args[1:],
                                     'st_mtime')
        idx, arg = r[0]
        value = arg.split('=')[1]
        if value == '0':
            logging.debug('Got zero st_mtime')
            st_mtime = 0
        else:
            logging.debug('Got normal st_mtime')
            st_mtime = int(mktime(strptime(value, '%Y/%m/%d-%H:%M:%S')))
        logging.debug('st_mtime: %d', st_mtime)

        # st_ctime
        r = find_arg_matching_string(syscall_object.args[1:],
                                     'st_ctime')
        idx, arg = r[0]
        value = arg.split('=')[1].strip('}')
        if value == '0':
            logging.debug('Got zero st_ctime')
            st_ctime = 0
        else:
            logging.debug('Got normal st_ctime')
            st_ctime = int(mktime(strptime(value, '%Y/%m/%d-%H:%M:%S')))
        logging.debug('st_ctime: %d', st_ctime)

        logging.debug('Injecting values into structure')
        logging.debug('pid: %d', pid)
        logging.debug('addr: %d', buf_addr)
        cint.populate_stat64_struct(pid,
                                    buf_addr,
                                    int(st_dev1),
                                    int(st_dev2),
                                    st_blocks,
                                    st_nlink,
                                    st_gid,
                                    st_blksize,
                                    int(st_rdev1),
                                    int(st_rdev2),
                                    st_size,
                                    st_mode,
                                    st_uid,
                                    st_ino,
                                    st_ctime,
                                    st_mtime,
                                    st_ctime)
    noop_current_syscall(pid)
    apply_return_conditions(pid, syscall_object)


def lstat64_entry_handler(syscall_id, syscall_object, pid):
    buf_addr = cint.peek_register(pid, cint.ECX)
    logging.debug('ECX: %x', (buf_addr & 0xffffffff))
    if syscall_object.ret[0] == -1:
        logging.debug('Got unsuccessful lstat64 call')
    else:
        logging.debug('Got successful lstat64 call')
        # There should always be an st_dev
        idx, arg = find_arg_matching_string(syscall_object.args[1:],
                                            'st_dev')[0]
        st_dev1 = arg
        st_dev1 = int(st_dev1.split('(')[1])
        # must increment idx by 2 in order to account for slicing out the
        # initial file descriptor
        st_dev2 = syscall_object.args[idx+2].value
        st_dev2 = int(st_dev2.strip(')'))
        logging.debug('st_dev1: %s', st_dev1)
        logging.debug('st_dev2: %s', st_dev2)

        # st_rdev is optional
        st_rdev1 = 0
        st_rdev2 = 0
        r = find_arg_matching_string(syscall_object.args[1:],
                                     'st_rdev')
        if len(r) > 0:
            idx, arg = r[0]
            logging.debug('We have a st_rdev argument')
            st_rdev1 = arg
            st_rdev1 = int(st_rdev1.split('(')[1])
            st_rdev2 = syscall_object.args[idx+2].value
            st_rdev2 = int(st_rdev2.strip(')'))
            logging.debug('st_rdev1: %d', st_rdev1)
            logging.debug('st_rdev2: %d', st_rdev2)

        # st_ino
        r = find_arg_matching_string(syscall_object.args[1:],
                                     'st_ino')
        idx, arg = r[0]
        st_ino = int(arg.split('=')[1])
        logging.debug('st_ino: %d', st_ino)

        # st_mode
        r = find_arg_matching_string(syscall_object.args[1:],
                                     'st_mode')
        idx, arg = r[0]
        st_mode = int(cleanup_st_mode(arg.split('=')[1]))
        logging.debug('st_mode: %d', st_mode)

        # st_nlink
        r = find_arg_matching_string(syscall_object.args[1:],
                                     'st_nlink')
        idx, arg = r[0]
        st_nlink = int(arg.split('=')[1])
        logging.debug('st_nlink: %d', st_nlink)

        # st_uid
        r = find_arg_matching_string(syscall_object.args[1:],
                                     'st_uid')
        idx, arg = r[0]
        st_uid = int(arg.split('=')[1])
        logging.debug('st_uid: %d', st_uid)

        # st_gid
        r = find_arg_matching_string(syscall_object.args[1:],
                                     'st_gid')
        idx, arg = r[0]
        st_gid = int(arg.split('=')[1])
        logging.debug('st_gid: %d', st_gid)

        # st_blocksize
        r = find_arg_matching_string(syscall_object.args[1:],
                                     'st_blksize')
        idx, arg = r[0]
        st_blksize = int(arg.split('=')[1])
        logging.debug('st_blksize: %d', st_blksize)

        # st_blocks
        r = find_arg_matching_string(syscall_object.args[1:],
                                     'st_blocks')
        idx, arg = r[0]
        st_blocks = int(arg.split('=')[1])
        logging.debug('st_block: %d', st_blocks)

        # st_size is optional
        r = find_arg_matching_string(syscall_object.args[1:],
                                     'st_size')
        if len(r) >= 1:
            idx, arg = r[0]
            st_size = int(arg.split('=')[1])
            logging.debug('st_size: %d', st_size)
        else:
            st_size = 0
            logging.debug('optional st_size not present')
        # st_atime
        r = find_arg_matching_string(syscall_object.args[1:],
                                     'st_atime')
        idx, arg = r[0]
        value = arg.split('=')[1]
        if value == '0':
            logging.debug('Got zero st_atime')
            st_atime = 0
        else:
            logging.debug('Got normal st_atime')
            st_atime = int(mktime(strptime(value, '%Y/%m/%d-%H:%M:%S')))
        logging.debug('st_atime: %d', st_atime)

        # st_mtime
        r = find_arg_matching_string(syscall_object.args[1:],
                                     'st_mtime')
        idx, arg = r[0]
        value = arg.split('=')[1]
        if value == '0':
            logging.debug('Got zero st_mtime')
            st_mtime = 0
        else:
            logging.debug('Got normal st_mtime')
            st_mtime = int(mktime(strptime(value, '%Y/%m/%d-%H:%M:%S')))
        logging.debug('st_mtime: %d', st_mtime)

        # st_ctime
        r = find_arg_matching_string(syscall_object.args[1:],
                                     'st_ctime')
        idx, arg = r[0]
        value = arg.split('=')[1].strip('}')
        if value == '0':
            logging.debug('Got zero st_ctime')
            st_ctime = 0
        else:
            logging.debug('Got normal st_ctime')
            st_ctime = int(mktime(strptime(value, '%Y/%m/%d-%H:%M:%S')))
        logging.debug('st_ctime: %d', st_ctime)

        logging.debug('Injecting values into structure')
        logging.debug('pid: %d', pid)
        logging.debug('addr: %d', buf_addr)
        cint.populate_stat64_struct(pid,
                                    buf_addr,
                                    int(st_dev1),
                                    int(st_dev2),
                                    st_blocks,
                                    st_nlink,
                                    st_gid,
                                    st_blksize,
                                    int(st_rdev1),
                                    int(st_rdev2),
                                    st_size,
                                    st_mode,
                                    st_uid,
                                    st_ino,
                                    st_ctime,
                                    st_mtime,
                                    st_ctime)
    noop_current_syscall(pid)
    apply_return_conditions(pid, syscall_object)


def fchown_entry_handler(syscall_id, syscall_object, pid):
    logging.debug('Entering fchown entry handler')
    validate_integer_argument(pid, syscall_object, 0, 0)
    # TODO: Validate second argument here. Issue -> it is a flags object
    validate_integer_argument(pid, syscall_object, 2, 2)
    if should_replay_based_on_fd(int(syscall_object.args[0].value)):
        logging.debug('Replaying this system call')
        noop_current_syscall(pid)
        apply_return_conditions(pid, syscall_object)
    else:
        logging.debug('Not replaying this system call')
        swap_trace_fd_to_execution_fd(pid, 0, syscall_object)


def fchmod_entry_handler(syscall_id, syscall_object, pid):
    logging.debug('Entering fchmod entry handler')
    validate_integer_argument(pid, syscall_object, 0, 0)
    if should_replay_based_on_fd(int(syscall_object.args[0].value)):
        logging.debug('Replaying this system call')
        noop_current_syscall(pid)
        apply_return_conditions(pid, syscall_object)
    else:
        logging.debug('Not replaying this system call')
        swap_trace_fd_to_execution_fd(pid, 0, syscall_object)


def flistxattr_entry_handler(syscall_id, syscall_object, pid):
    logging.debug('In flistxattr entry handler')
    # validate file descriptor
    validate_integer_argument(pid, syscall_object, 0, 0)
    # validate buffer size
    validate_integer_argument(pid, syscall_object, 2, 2)
    fd = int(syscall_object.args[0].value)
    if should_replay_based_on_fd(fd):
        if syscall_object.ret[0] != -1:
            buffer_address = cint.peek_register(pid, cint.ECX)
            logging.debug('buffer address: %x', buffer_address)
            # if param 2 is NULL, we don't populate
            if buffer_address != 0:
                data = cleanup_quotes(syscall_object.args[1].value)
                if data == 'NULL':
                    data = ''
                else:
                    data = data.decode('string-escape')
                logging.debug('data: %s', data)
                cint.populate_char_buffer(pid,
                                          buffer_address,
                                          data)
        logging.debug('Replaying this system call')
        noop_current_syscall(pid)
        apply_return_conditions(pid, syscall_object)
    else:
        logging.debug('Not replaying this system call')
        swap_trace_fd_to_execution_fd(pid, 0, syscall_object)


def flixtxattr_exit_handler(syscall_id, syscall_object, pid):
    logging.debug('Entering flistxattr exit handler')
    ret_val = cint.peek_register(pid, cint.EAX)
    ret_val_from_trace = int(syscall_object.ret[0])
    logging.debug('Return value from execution: %d', ret_val)
    logging.debug('Return value from trace: %d', ret_val_from_trace)
    if ret_val != ret_val_from_trace:
        raise ReplayDeltaError('Return value from execution ({}) differed '
                               'from return value from trace ({})'
                               .format(ret_val, ret_val_from_trace))


def fgetxattr_entry_handler(syscall_id, syscall_object, pid):
    logging.debug('In fgetxattr entry handler')
    # validate file descriptor
    validate_integer_argument(pid, syscall_object, 0, 0)
    # validate buffer size
    validate_integer_argument(pid, syscall_object, 3, 3)
    fd = int(syscall_object.args[0].value)
    if should_replay_based_on_fd(fd):
        if syscall_object.ret[0] != -1:
            buffer_address = cint.peek_register(pid, cint.EDX)
            logging.debug('buffer address: %x', buffer_address)
            # if param 2 is NULL, we don't populate
            if buffer_address != 0:
                data = cleanup_quotes(syscall_object.args[1].value)
                if data == 'NULL':
                    data = ''
                else:
                    data = data.decode('string-escape')
                logging.debug('data: %s', data)
                cint.populate_char_buffer(pid,
                                          buffer_address,
                                          data)
        logging.debug('Replaying this system call')
        noop_current_syscall(pid)
        apply_return_conditions(pid, syscall_object)
    else:
        logging.debug('Not replaying this system call')
        swap_trace_fd_to_execution_fd(pid, 0, syscall_object)


def fgetxattr_exit_handler(syscall_id, syscall_object, pid):
    logging.debug('Entering fgetxattr exit handler')
    ret_val = cint.peek_register(pid, cint.EAX)
    ret_val_from_trace = int(syscall_object.ret[0])
    logging.debug('Return value from execution: %d', ret_val)
    logging.debug('Return value from trace: %d', ret_val_from_trace)
    if ret_val != ret_val_from_trace:
        raise ReplayDeltaError('Return value from execution ({}) differed '
                               'from return value from trace ({})'
                               .format(ret_val, ret_val_from_trace))


def fsetxattr_entry_handler(syscall_id, syscall_object, pid):
    logging.debug('Entering fsetxattr entry handler')
    # validate file descriptor
    validate_integer_argument(pid, syscall_object, 0, 0)
    # validate size
    validate_integer_argument(pid, syscall_object, 3, 3)
    fd = int(syscall_object.args[0].value)
    if should_replay_based_on_fd(fd):
        logging.debug('Replaying this system call')
        noop_current_syscall(pid)
        apply_return_conditions(pid, syscall_object)
    else:
        logging.debug('Not replaying this system call')
        swap_trace_fd_to_execution_fd(pid, 0, syscall_object)


def fsetxattr_exit_handler(syscall_id, syscall_object, pid):
    logging.debug('Entering fstexattr exit handler')
    ret_val = cint.peek_register(pid, cint.EAX)
    ret_val_from_trace = int(syscall_object.ret[0])
    logging.debug('Return value from execution: %d', ret_val)
    logging.debug('Return value from trace: %d', ret_val_from_trace)
    if ret_val != ret_val_from_trace:
        raise ReplayDeltaError('Return value from execution ({}) differed '
                               'from return value from trace ({})'
                               .format(ret_val, ret_val_from_trace))


def getdents64_entry_handler(syscall_id, syscall_object, pid):
    logging.debug('Entering getdents64 entry handler')
    # Validate file descriptor
    validate_integer_argument(pid, syscall_object, 0, 0)
    # We must check the this argument manually because posix-omni-parser
    # does not split the list of structures up correctly
    size = cint.peek_register(pid, cint.EDX)
    size_from_trace = int(syscall_object.args[-1].value)
    if size != size_from_trace:
        raise ReplayDeltaError('Size from execution ({}) did not match size '
                               'from trace ({})'
                               .format(size, size_from_trace))

    fd = int(syscall_object.args[0].value)
    if should_replay_based_on_fd(fd):
        logging.debug('Replaying this system call')
        logging.debug('PID: %d', pid)
        addr = cint.peek_register(pid, cint.ECX)
        logging.debug('addr: %x', addr & 0xffffffff)
        retlen = int(syscall_object.ret[0])
        data = parse_getdents_structure(syscall_object)
        if len(data) > 0:
            cint.populate_getdents64_structure(pid, addr, data, retlen)
        noop_current_syscall(pid)
        apply_return_conditions(pid, syscall_object)
    else:
        logging.debug('Not replaying this system call')
        swap_trace_fd_to_execution_fd(pid, 0, syscall_object)


def getdents64_exit_handler(syscall_id, syscall_object, pid):
    logging.debug('Entering getdents64 exit handler')
    ret_val = cint.peek_register(pid, cint.EAX)
    ret_val_from_trace = int(syscall_object.ret[0])
    logging.debug('Return value from execution: %d', ret_val)
    logging.debug('Return value from trace: %d', ret_val_from_trace)
    if ret_val != ret_val_from_trace:
        raise ReplayDeltaError('Return value from execution ({}) differed '
                               'from return value from trace ({})'
                               .format(ret_val, ret_val_from_trace))


def getdents_entry_handler(syscall_id, syscall_object, pid):
    logging.debug('Entering getdents entry handler')
    # Validate file descriptor
    validate_integer_argument(pid, syscall_object, 0, 0)
    # We must check the this argument manually because posix-omni-parser
    # does not split the list of structures up correctly
    size = cint.peek_register(pid, cint.EDX)
    size_from_trace = int(syscall_object.args[-1].value)
    if size != size_from_trace:
        raise ReplayDeltaError('Size from execution ({}) did not match size '
                               'from trace ({})'
                               .format(size, size_from_trace))

    fd = int(syscall_object.args[0].value)
    if should_replay_based_on_fd(fd):
        logging.debug('Replaying this system call')
        logging.debug('PID: %d', pid)
        addr = cint.peek_register(pid, cint.ECX)
        logging.debug('addr: %x', addr & 0xffffffff)
        retlen = int(syscall_object.ret[0])
        data = parse_getdents_structure(syscall_object)
        if len(data) > 0:
            cint.populate_getdents_structure(pid, addr, data, retlen)
        noop_current_syscall(pid)
        apply_return_conditions(pid, syscall_object)
    else:
        logging.debug('Not replaying this system call')
        swap_trace_fd_to_execution_fd(pid, 0, syscall_object)


def getdents_exit_handler(syscall_id, syscall_object, pid):
    logging.debug('Entering getdents exit handler')
    ret_val = cint.peek_register(pid, cint.EAX)
    ret_val_from_trace = int(syscall_object.ret[0])
    logging.debug('Return value from execution: %d', ret_val)
    logging.debug('Return value from trace: %d', ret_val_from_trace)
    if ret_val != ret_val_from_trace:
        raise ReplayDeltaError('Return value from execution ({}) differed '
                               'from return value from trace ({})'
                               .format(ret_val, ret_val_from_trace))


def cleanup_st_mode(m):
    logging.debug('Cleaning up st_mode')
    m = m.split('|')
    logging.debug('Found st_mode parts: %s', m)
    tmp = 0
    for i in m:
        logging.debug('Got part: %s', i)
        if i[0] == '0':
            logging.debug('Interpreting part as base 8 int')
            val = int(i, 8)
            logging.debug('Part value in base 10: %d', val)
            logging.debug('Part value in base 8: %s', oct(val))
            tmp = tmp | val
        else:
            logging.debug('Interpreting part as S_<CONST>')
            try:
                val = STAT_CONST[i]
            except KeyError:
                raise ReplayDeltaError('Unsupported st_mode {}'.format(i))
            logging.debug('Part value in base 10: %d', val)
            logging.debug('Part value in base 8: %s', oct(val))
            tmp = tmp | val
        logging.debug('New value for tmp: %d', tmp)
    logging.debug('Final value for tmp: %d', tmp)
    return tmp


def _cleanup_f_type(t):
    logging.debug('Cleaning up f_type')
    try:
        return int(t, 16)
    except ValueError:
        try:
            return MAGIC_NAME_TO_MAGIC[t.strip('"')]
        except KeyError:
            raise ReplayDeltaError('Could not clean up f_type: ({})', t)


def fcntl64_entry_handler(syscall_id, syscall_object, pid):
    logging.debug('Entering fcntl64 entry handler')
    validate_integer_argument(pid, syscall_object, 0, 0)
    trace_fd = int(syscall_object.args[0].value)
    if should_replay_based_on_fd(trace_fd):
        operation = syscall_object.args[1].value[0].strip('[]\'')
        noop_current_syscall(pid)
        if (operation == 'F_GETFL' or operation == 'F_SETFL'
            or operation == 'F_SETFD' or operation == 'F_SETLKW'):
            apply_return_conditions(pid, syscall_object)
        elif (operation == 'F_GETFD'):
            _fcntl_f_getfd_handler(pid, syscall_object)
        elif operation == 'F_DUPFD':
            _fcntl_f_dupfd_handler(pid, syscall_object)
        else:
            raise NotImplementedError('Unimplemented fcntl64 operation {}'
                                      .format(operation))
    else:
        logging.debug('Not replaying this system call')
        swap_trace_fd_to_execution_fd(pid, 0, syscall_object)


def _fcntl_f_dupfd_handler(pid, syscall_object):
    logging.debug('Handling fcntl64 F_DUPFD operation')
    add_replay_fd(int(syscall_object.ret[0]))
    apply_return_conditions(pid, syscall_object)


def _fcntl_f_getfd_handler(pid, syscall_object):
    logging.debug('Handling fcntl64 F_GETFD operation')
    if syscall_object.ret[0] == 'FD_CLOEXEC':
        cint.poke_register(pid, cint.EAX, 0x1)
    else:
        cint.poke_register(pid, cint.EAX, int(syscall_object.ret[0]))


def open_entry_debug_printer(pid, orig_eax, syscall_object):
    logging.debug('This call tried to open: %s',
                  peek_string(pid,
                              cint.peek_register(pid,
                                                 cint.EBX)))


def write_entry_debug_printer(pid, orig_eax, syscall_object):
    fd = cint.peek_register(pid, cint.EBX)
    addr = cint.peek_register(pid, cint.ECX)
    data_count = cint.peek_register(pid, cint.EDX)
    data = cint.copy_address_range(pid, addr, addr + data_count)
    logging.debug('This call tried to write: %s', data.encode('string-escape'))
    logging.debug('Length: %d', data_count)
    logging.debug('File descriptor: %d', fd)


def fstat64_entry_debug_printer(pid, orig_eax, syscall_object):
    logging.debug('This call tried to fstat: %s',
                  cint.peek_register(pid, cint.EBX))


def close_entry_debug_printer(pid, orig_eax, syscall_object):
    logging.debug('This call tried to close: %s',
                  cint.peek_register(pid, cint.EBX))


def dup_entry_debug_printer(pid, orig_eax, syscall_object):
    logging.debug('This call tried to dup: %d',
                  cint.peek_register(pid, cint.EBX))


def fcntl64_entry_debug_printer(pid, orig_eax, syscall_object):
    logging.debug('This call tried to fcntl: %d',
                  cint.peek_register(pid, cint.EBX))
    logging.debug('fcntl command: %s',
                  FCNTL64_INT_TO_CMD[
                      cint.peek_register(pid, cint.ECX)])
    logging.debug('Param 3: %d',
                  cint.peek_register(pid, cint.EDX))


def stat64_entry_debug_printer(pid, orig_eax, syscall_object):
    path_addr = cint.peek_register(pid, cint.EBX)
    logging.debug('This call tried to use path: %s',
                  peek_string(pid, path_addr))


def access_entry_debug_printer(pid, orig_eax, syscall_object):
    path_addr = cint.peek_register(pid, cint.EBX)
    mode = cint.peek_register(pid, cint.ECX)
    logging.debug('This call tried to use path: %s',
                  peek_string(pid, path_addr))
    logging.debug('Mode: %s',
                  PERM_INT_TO_PERM[mode])


def read_entry_debug_printer(pid, orig_eax, syscall_object):
    fd = cint.peek_register(pid, cint.EBX)
    logging.debug('Tried to read from fd: %d', fd)


def unlink_entry_debug_printer(pid, orig_eax, syscall_object):
    name = peek_string(pid,
                       cint.peek_register(pid,
                                          cint.EBX))
    logging.debug('Tried to unlink name %s', name)


def lstat64_entry_debug_printer(pid, orig_eax, syscall_object):
    name = peek_string(pid,
                       cint.peek_register(pid,
                                          cint.EBX))
    logging.debug('Tried to lstat name: %s', name)
