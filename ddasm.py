import sys
import logging
from asminfo import asminfo
from datetime import datetime

log_file = None


def main(argv):
    global log_file

    try:
        log_file = open('build.log', 'w')
        log("DDASM v0.1", True)
    except IOError as ioe:
        print('Failed to open log file (build.log). Is it still open?')
        print(ioe.args[1])
        print('FAILURE')
        sys.exit(-1)

    # Parse input arguments
    try:
        file_names = get_file_names(argv)
    except ValueError:
        print('FAILURE - check build.log')
        log('FAILURE', False)
        log_file.close()
        sys.exit(-1)
    except Exception as e:
        log('Unknown error in "get_file_names()".', True)
        log('FAILURE - check python logs', True)
        log_file.close()
        logging.exception(e)
        sys.exit(-1)

    # Read and pre-process program
    try:
        analysed_program = load_program(file_names['input_file'])
    except IOError:
        print('FAILURE - check build.log')
        log('FAILURE', False)
        log_file.close()
        sys.exit(-1)
    except ValueError:
        print('FAILURE - check build.log')
        log('FAILURE', False)
        log_file.close()
        sys.exit(-1)
    except Exception as e:
        log('Unexpected error in "load_program()".', True)
        log('FAILURE - check python logs', True)
        log_file.close()
        logging.exception(e)
        sys.exit(-1)

    # Read ROM template
    try:
        rom = load_template(file_names['template_file'])
    except ValueError or IOError:
        print('FAILURE - check build.log')
        log('FAILURE', False)
        log_file.close()
        sys.exit(-1)
    except Exception as e:
        log('Unexpected error in "load_template()".', True)
        log('FAILURE - check python logs', True)
        log_file.close()
        logging.exception(e)
        sys.exit(-1)

    # generate VHDL ROM file
    try:
        generate_rom_file(analysed_program, rom, file_names['output_file'])
    except ValueError or IOError:
        print('FAILURE - check build.log')
        log('FAILURE', False)
        log_file.close()
        sys.exit(-1)
    except Exception as e:
        log('Unexpected error in "generate_rom_file()".', True)
        log('FAILURE - check python logs', True)
        log_file.close()
        logging.exception(e)
        sys.exit(-1)

    log("SUCCESS", True)
    log_file.close()
    sys.exit(0)


def log(message, do_print):
    global log_file

    log_file.write(message)
    log_file.write('\n')

    if do_print:
        print(message)


def get_file_names(argv):
    argc = len(argv)
    do_print = False

    fns = {'input_file': '', 'output_file': '', 'template_file': 'ROM_template.vhd'}
    if argc == 1:
        err = 'ERROR: Not enough input arguments (' + str(argc-1) + '). Expecting at least 1.'
        log(err, do_print)
        raise ValueError
    elif argc == 2:
        fns['input_file'] = argv[1]
    elif argc == 3:
        fns['input_file'] = argv[1]
        fns['output_file'] = argv[2]
    else:
        err = 'ERROR: Too many input arguments (' + str(argc - 1) + '). Expecting 2 at most.'
        log(err, False)
        raise ValueError

    if len(fns['output_file']) == 0:
        dot_index = fns['input_file'].find('.')
        if dot_index < 0:
            log('WARNING: Input file is missing an extension!', True)
            input_file_name = fns['input_file']
        else:
            input_file_name = fns['input_file'][0:dot_index]
        fns['output_file'] = input_file_name + '.vhd'

    msg = ' - input:    ' + fns['input_file'] + '\n'
    msg += ' - output:   ' + fns['output_file'] + '\n'
    msg += ' - template: ' + fns['template_file'] + '\n'
    log(msg, False)

    return fns


def load_program(filename):
    do_print = False
    # load the program
    try:
        with open(filename) as f:
            raw_text = f.readlines()
    except IOError:
        err = 'ERROR: Failed to open program (' + filename + ').'
        log(err, True)
        raise IOError

    log('Analyzing program...', True)

    # analyse text
    line_index = 0
    pinfo = {'program': {}, 'labels': {}, 'symbols': {}, 'size': 0}
    address = 0
    for line in raw_text:
        is_instruction = False
        # split line into categories
        sline = line.strip().lower()
        scindex = sline.find(';')
        # isolate instruction from comment
        if scindex >= 0:
            asm = sline[0:scindex].strip()
        else:
            asm = sline
        # check for label
        scindex = asm.find(':')
        if scindex == 0:
            err = 'ERROR: Semicolon (:) at the start of line.\n'
            err += '\tline ' + str(line_index+1) + ' -> ' + line
            err += 'Expecting a label.'
            log(err, True)
            raise ValueError
        if scindex > 0:
            # we have a label, now we do some checks
            label = asm[0:scindex].strip()
            # check if first character is a number
            if label[0].isdigit():
                err = 'ERROR: Label can not start with a number.\n'
                err += '\tline ' + str(line_index+1) + ' -> ' + line.strip()
                log(err, True)
                raise ValueError
            # check if the label contains spaces
            if (label.find(' ') > 0) or (label.find('\t') > 0):
                err = 'ERROR: Label can not contain spaces.\n'
                err += '\tline ' + str(line_index+1) + ' -> ' + line.strip()
                log(err, True)
                raise ValueError
            # check if the label is already defined
            defined_labels = pinfo['labels'].keys()
            if label in defined_labels:
                err = 'ERROR: Label "' + label + '" already defined.\n'
                err += '\tline ' + str(line_index+1) + ' -> ' + line.strip()
                log(err, True)
                raise ValueError
            else:
                # add label to list
                pinfo['labels'][label] = '%02x' % address
                # now we do some further checking
                if 'reset' in defined_labels:
                    if pinfo['labels']['reset'] != '00':
                        err = 'ERROR: Label "reset" should have address "00".\n'
                        err += '\tline ' + str(line_index+1) + ' -> ' + line.strip()
                        log(err, True)
                        raise ValueError
                if 'isr' in defined_labels:
                    if pinfo['labels']['isr'] != '02':
                        err = 'ERROR: Label "isr" should have address "02".\n'
                        err += '\tline ' + str(line_index+1) + ' -> ' + line.strip()
                        log(err, True)
                        raise ValueError

            # in case that an instruction follows the label
            asm = asm[scindex:].replace(':', ' ').strip()

        vhdl_comment = ' -- ' + asm + '\n'

        ins = None
        op_1 = None
        op_2 = None
        # parse instruction
        ops = split_instruction(asm)
        if len(ops) > 0:
            is_instruction = True
            ins = ops[0]
            if len(ops) > 1:
                op_1 = ops[1]
                if len(ops) > 2:
                    op_2 = ops[2]
                    if len(ops) > 3:
                        err = 'ERROR: Wrong instruction format.\n'
                        err += '\tline ' + str(line_index + 1) + ' -> ' + line.strip()
                        log(err, True)
                        raise ValueError

            # check for virtual instruction and if so do replacement
            if ins in asminfo['virtual_instructions']:
                op_2 = asminfo['virtual_instructions'][ins]['operand_2']
                ins = asminfo['virtual_instructions'][ins]['replace_with']

        # update program info (and set next instruction address)
        if is_instruction:
            pinfo['program'][line_index] = {'address': address,
                                            'instruction': ins,
                                            'operand_1': op_1,
                                            'operand_2': op_2,
                                            'comment': vhdl_comment}
            address = address + 2

        # process next line
        line_index = line_index + 1

    # Log a list of the labels that are defined in the program
    log('- Labels defined in ' + filename + ':', do_print)
    labels_table = format_symbols_table(pinfo['labels'], 'label', 'address (hex)')
    log(labels_table, do_print)
    # TODO: log other symbols
    log('- Variables defined in ' + filename + ':', do_print)
    symbols_table = format_symbols_table(pinfo['symbols'], 'variables', 'register')
    log(symbols_table, do_print)

    pinfo['size'] = address - 2
    msg = ' - Program size: ' + str(pinfo['size']) + ' bytes.\n\nAnalysis complete.\n\n'
    log(msg, True)

    return pinfo


def load_template(filename):
    dt = datetime.now()
    datestr = dt.strftime('-- Create Date: %H:%M:%S %d-%m-%Y\r\n')
    # print(datestr)
    tinfo = {'first_part': list(), 'last_part': list(), 'program_space': None}

    log('Loading ROM template...', True)

    # load the template
    try:
        with open(filename) as f:
            raw_text = f.readlines()
    except IOError as ioe:
        err = 'ERROR: Failed to load template file (' + filename + ').'
        log(err, True)
        log(ioe.args[1], False)
        raise IOError

    section = ['start', 'program', 'end']
    si = 0
    for line in raw_text:
        if section[si] == 'start':
            if '-- Create Date' in line:
                tinfo['first_part'].append(datestr)
            else:
                tinfo['first_part'].append(line)
                if '-- program start' in line:
                    si += 1
                    tinfo['program_space'] = 0
        elif section[si] == 'program':
            if '-- program end' in line:
                si += 1
                tinfo['last_part'].append(line)
            else:
                tinfo['program_space'] += 1
        elif section[si] == 'end':
            tinfo['last_part'].append(line)
        else:
            log('ERROR: Error while reading template file.', True)
            raise ValueError

    if section[si] != 'end':
        log('ERROR: ROM template is missing mandatory lines.', True)
        raise ValueError

    log('ROM template loaded.\n', True)

    return tinfo


def generate_rom_file(pinfo, rom, filename):
    do_print = False
    log('Generating ROM memory file...', True)

    try:
        rom_file = open(filename, 'w')
    except IOError:
        log('ERROR: Failed to open target file.', True)
        raise IOError

    # check if memory space has not been succeeded
    if pinfo['size'] > rom['program_space']:
        err = 'ERROR: Program size (' + pinfo['size'] + ' bytes) exceeds available memory (' \
              + rom['program_space'] + ' bytes).'
        log(err, True)
        raise ValueError

    # Write first part of ROM file
    for line in rom['first_part']:
        rom_file.write(line)

    # Write program to ROM file
    last_address = 0
    for line in pinfo['program']:
        instruction_info = pinfo['program'][line]
        log(str(instruction_info), do_print)

        # get instruction type
        try:
            instruction_type = asminfo['instructions'][instruction_info['instruction']]['type']
        except KeyError:
            err = 'ERROR: Unknown instruction "' + instruction_info['instruction'] + '" (line ' + str(line+1) + ').'
            log(err, True)
            raise ValueError

        # get instruction opcode
        instruction_opcode = asminfo['instructions'][instruction_info['instruction']]['opcode']
        # print(instruction_type)

        rom_line = vhdl_fixed_start(instruction_info['address'])
        if instruction_type == 'jump':
            # get memory address
            if instruction_info['operand_1'] is None:
                err = 'ERROR: Jump address not defined for instruction "' + instruction_info['instruction']\
                      + '" (line ' + str(line+1) + ').'
                log(err, True)
                raise ValueError

            # lookup address in case label is used
            address = lookup_name(instruction_info['operand_1'], pinfo['labels'])
            if address is None:
                err = 'ERROR: Name "' + instruction_info['operand_1'] + '" is not defined (line ' + str(line+1) + ').'
                log(err, True)
                raise ValueError

            # convert hex address to binary representation
            memory_address = address_hex_to_binary(address)

            # assemble jump instruction
            rom_line += instruction_opcode + '000",' + instruction_info['comment']
            if instruction_info['address'] == (rom['program_space'] - 2):
                rom_line += vhdl_fixed_start(instruction_info['address'] + 1) + memory_address + '"\n'
            else:
                rom_line += vhdl_fixed_start(instruction_info['address'] + 1) + memory_address + '",\n'

        elif instruction_type == 'jump_no_address':
            # assemble jump instruction (no address specified)
            rom_line += instruction_opcode + '000",' + instruction_info['comment']
            if instruction_info['address'] == (rom['program_space'] - 2):
                rom_line += vhdl_fixed_start(instruction_info['address']+1) + '00000000"\n'
            else:
                rom_line += vhdl_fixed_start(instruction_info['address']+1) + '00000000",\n'

        elif instruction_type == 'single_register':
            # get destination/source register code
            try:
                rds_code = asminfo['registers'][instruction_info['operand_1']]
            except KeyError:
                err = 'ERROR: Wrong register name "' + instruction_info['operand_1'] + '" (line ' + str(line+1) + ').'
                log(err, True)
                raise ValueError
            # assemble single register instruction
            rom_line += instruction_opcode + rds_code + '",' + instruction_info['comment']
            if instruction_info['address'] == (rom['program_space'] - 2):
                rom_line += vhdl_fixed_start(instruction_info['address']+1) + rds_code + '00000"\n'
            else:
                rom_line += vhdl_fixed_start(instruction_info['address']+1) + rds_code + '00000",\n'

        elif instruction_type == 'register_to_register':
            # get destination register code
            try:
                rd_code = asminfo['registers'][instruction_info['operand_1']]
            except KeyError:
                err = 'ERROR: Wrong register name "' + instruction_info['operand_1'] + '" (line ' + str(line+1) + ').'
                log(err, True)
                raise ValueError
            # get source register code
            try:
                rs_code = asminfo['registers'][instruction_info['operand_2']]
            except KeyError:
                err = 'ERROR: Wrong register name "' + instruction_info['operand_2'] + '" (line ' + str(line+1) + ').'
                log(err, True)
                raise ValueError
            # assemble register-to-register instruction
            rom_line += instruction_opcode + rd_code + '",' + instruction_info['comment']
            if instruction_info['address'] == (rom['program_space'] - 2):
                rom_line += vhdl_fixed_start(instruction_info['address'] + 1) + rs_code + '00000"\n'
            else:
                rom_line += vhdl_fixed_start(instruction_info['address'] + 1) + rs_code + '00000",\n'

        elif instruction_type == 'register_to_memory':
            # get memory address
            # check if 0 < length <= 2
            if instruction_info['operand_1'] is None:
                err = 'ERROR: Target address unspecified for instruction "' + instruction_info['instruction']\
                      + '" (line ' + str(line+1) + ').'
                log(err, True)
                raise ValueError
            # TODO: replace with lookup
            if len(instruction_info['operand_1']) > 2:
                err = 'ERROR: Target address "' + instruction_info['operand_1'] + '" is too long (line '\
                      + str(line+1) + ').'
                log(err, True)
                raise ValueError
            # convert to binary representation
            try:
                memory_address = address_hex_to_binary(instruction_info['operand_1'])
            except KeyError:
                err = 'ERROR: "' + instruction_info['operand_1'] + '" is not a hexadecimal address (line '\
                      + str(line+1) + ').'
                log(err, True)
                raise ValueError

            # get source register code
            try:
                rs_code = asminfo['registers'][instruction_info['operand_2']]
            except KeyError:
                err = 'ERROR: Wrong register name "' + instruction_info['operand_2'] + '" (line ' + str(line+1) + ').'
                log(err, True)
                raise ValueError
            # assemble register-to-memory instruction
            rom_line += instruction_opcode + rs_code + '",' + instruction_info['comment']
            if instruction_info['address'] == (rom['program_space'] - 2):
                rom_line += vhdl_fixed_start(instruction_info['address'] + 1) + memory_address + '"\n'
            else:
                rom_line += vhdl_fixed_start(instruction_info['address'] + 1) + memory_address + '",\n'

        elif instruction_type == 'x_to_register':
            # get destination register code
            try:
                rd_code = asminfo['registers'][instruction_info['operand_1']]
            except KeyError:
                err = 'ERROR: Wrong register name "' + instruction_info['operand_1'] + '" (line ' + str(line+1) + ').'
                log(err, True)
                raise ValueError

            # get memory address or literal
            # check if 0 < length <= 2
            if instruction_info['operand_2'] is None:
                err = 'ERROR: Literal or memory location unspecified for instruction "'\
                      + instruction_info['instruction'] + '" (line ' + str(line + 1) + ').'
                log(err, True)
                raise ValueError
            if len(instruction_info['operand_2']) > 2:
                err = 'ERROR: Literal or memory location "' + instruction_info['operand_2'] + '" is too long (line '\
                      + str(line + 1) + ').'
                log(err, True)
                raise ValueError
            # convert to binary representation
            try:
                address_literal = address_hex_to_binary(instruction_info['operand_2'])
            except KeyError:
                err = 'ERROR: "' + instruction_info['operand_2'] + '" is not a hexadecimal address or number (line '\
                      + str(line + 1) + ').'
                log(err, True)
                raise ValueError

            # assemble memory/literal-to-register instruction
            rom_line += instruction_opcode + rd_code + '",' + instruction_info['comment']
            if instruction_info['address'] == (rom['program_space'] - 2):
                rom_line += vhdl_fixed_start(instruction_info['address'] + 1) + address_literal + '"\n'
            else:
                rom_line += vhdl_fixed_start(instruction_info['address'] + 1) + address_literal + '",\n'
        else:
            # unsupported instruction type
            err = 'ERROR: Unknown instruction type (' + instruction_type + ').'
            log(err, True)
            raise ValueError

        log(rom_line, do_print)
        rom_file.write(rom_line)
        last_address = instruction_info['address'] + 2

    # fill remaining memory space with zeros
    for remaining_address in range(last_address, rom['program_space']):
        if remaining_address == (rom['program_space']-1):
            rom_line = vhdl_fixed_start(remaining_address) + '00000000"\n'
        else:
            rom_line = vhdl_fixed_start(remaining_address) + '00000000",\n'
        rom_file.write(rom_line)

    # write last part of template to ROM file
    for line in rom['last_part']:
        rom_file.write(line)

    rom_file.close()
    log('Program ROM complete.', True)


def vhdl_fixed_start(address):
    rom_start = '\t\t%3d => "' % address
    return rom_start


def split_instruction(ins):
    newins = ins.replace(',', ' ')
    splitins = newins.split()
    return splitins


def lookup_name(name, labels):
    if is_hex(name):
        return name

    if is_label(name, labels):
        return labels[name]

    # TODO: expand to look-up variables and symbols

    return None


def address_hex_to_binary(address):
    binary_lookup = {
        '0': '0000',
        '1': '0001',
        '2': '0010',
        '3': '0011',
        '4': '0100',
        '5': '0101',
        '6': '0110',
        '7': '0111',
        '8': '1000',
        '9': '1001',
        'a': '1010',
        'b': '1011',
        'c': '1100',
        'd': '1101',
        'e': '1110',
        'f': '1111'
    }

    if len(address) == 1:
        binary_address = '0000'
    else:
        try:
            binary_address = binary_lookup[address[0]]
        except KeyError as ke:
            raise ke

    try:
        binary_address += binary_lookup[address[1]]
    except KeyError as ke:
        raise ke

    return binary_address


def is_hex(s):
    try:
        int(s, 16)
        return True
    except ValueError:
        return False


def is_label(s, labels):
    try:
        labels[s]   # Exploiting possible KeyError
        return True
    except KeyError:
        return False


def format_symbols_table(symbols_list, symbol_name, value='address'):
    if not bool(symbols_list.keys()):
        msg = '\n\tNo symbols of type "' + symbol_name + '" have been defined.\n'
        return msg

    longest_name = 0
    longest_value = 0
    # determine maximum length of items in each column
    for symbol in symbols_list.keys():
        if len(symbol) > longest_name:
            longest_name = len(symbol)
        if len(symbols_list[symbol]) > longest_value:
            longest_value = len(symbols_list[symbol])
    if longest_name < len(symbol_name):
        longest_name = len(symbol_name)
    if longest_value < len(value):
        longest_value = len(value)

    # top rule
    table = '\n\t+'
    for x in range(0, longest_name):
        table += '-'
    table += '--+'
    for x in range(0, longest_value):
        table += '-'
    table += '--+\n'

    # table header
    table += '\t| ' + symbol_name
    for x in range(len(symbol_name), longest_name):
        table += ' '
    table += ' | ' + value
    for x in range(len(value), longest_value):
        table += ' '
    table += ' |\n'

    # middle rule
    table += '\t+'
    for x in range(0, longest_name):
        table += '-'
    table += '--+'
    for x in range(0, longest_value):
        table += '-'
    table += '--+\n'

    # print lines
    for symbol in symbols_list.keys():
        table += '\t| ' + symbol
        for x in range(len(symbol), longest_name):
            table += ' '
        table += ' | ' + symbols_list[symbol]
        for x in range(len(symbols_list[symbol]), longest_value):
            table += ' '
        table += ' |\n'

    # bottom rule
    table += '\t+'
    for x in range(0, longest_name):
        table += '-'
    table += '--+'
    for x in range(0, longest_value):
        table += '-'
    table += '--+\n'

    return table


if __name__ == "__main__":
    main(sys.argv)
