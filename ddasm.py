"""
This is the main program file for the DDASM assembler. It will read a DDA program file and convert it to a VHDL \
description of a ROM file. This ROM file serves as the program memory for the LDD mark II processor.
DDASM = Digital Design Assmebly
LDD = Lab Digital Design
Digital Design refers to the Digital Design courses of the Faculty Engineering Technology - KU Leuven, Ghent
"""
import sys
import logging
from asminfo import asminfo
from datetime import datetime

log_file = None


def main(argv):
    """
    This function executes the necessary steps for assembling the program ROM.
        1) loading (and analysing) a program
        2) loading a ROM template file
        3) generating the ROM and writing to a VHDL file

    :param argv: The list of command line arguments passed to this script.
    :return: The script returns exit code 0 on success; -1 otherwise.
    """
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
        rom = load_template(file_names['template_file'], file_names['output_file'])
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
    """
    Log a message to the build log and print in the console (optionally).

    :param message: String containing the log message.
    :param do_print: Setting do_print to True will also display de logged message in the console.
    :return: Nothing
    """
    global log_file

    log_file.write(message)
    log_file.write('\n')

    if do_print:
        print(message)


def print_usage():
    """
    Print an informational message on how to use the DDASM assembler.

    :return: Nothing
    """
    print('USAGE: python ddasm.py program_name.dda [vhdl_rom.vhd]')
    print(' * program_name.dda : File containing the assembly program')
    print(' * vhdl_rom.vhd     : (optional) File where VHDL description of program ROM is written to.')
    print('                      If not specified, the file name will be "program_name.vhd".')


def get_file_names(argv):
    """
    Analyse the list of arguments to determine which files should be loaded.

    :param argv: This is the list of arguments passed with the "main" script. The first item in the list, argv[0], \
                 the name of the script.
    :return: a dictionary containing the name of the 'input_file', 'output_file' and the 'template_file'
    """
    argc = len(argv)
    do_print = True

    fns = {'input_file': '', 'output_file': '', 'template_file': 'ROM_template.vhd'}
    if argc == 1:
        err = 'ERROR: Not enough input arguments (' + str(argc-1) + '). Expecting at least 1.'
        log(err, do_print)
        print_usage()
        raise ValueError
    elif argc == 2:
        fns['input_file'] = argv[1]
    elif argc == 3:
        fns['input_file'] = argv[1]
        fns['output_file'] = argv[2]
    else:
        err = 'ERROR: Too many input arguments (' + str(argc - 1) + '). Expecting 2 at most.'
        log(err, False)
        print_usage()
        raise ValueError

    if len(fns['output_file']) == 0:
        dot_index = fns['input_file'].find('.')
        if dot_index < 0:
            log('WARNING: Input file name is missing an extension!', True)
            input_file_name = fns['input_file']
        else:
            input_file_name = fns['input_file'][0:dot_index]
        fns['output_file'] = input_file_name + '.vhd'
    else:
        dot_index = fns['output_file'].find('.')
        if dot_index < 0:
            log('WARNING: Output file name is missing an extension!', True)

    msg = ' - input:    ' + fns['input_file'] + '\n'
    msg += ' - output:   ' + fns['output_file'] + '\n'
    msg += ' - template: ' + fns['template_file'] + '\n'
    log(msg, False)

    return fns


def load_program(filename):
    """
    Load and analyse the DDASM program.

    :param filename: Specifies the name of the file that contains the program.
    :return: A dictionary containing information of the analysed program.
    """
    do_print = False
    # load the program
    try:
        with open(filename) as f:
            raw_text = f.readlines()
    except IOError:
        err = 'ERROR: Failed to open program (' + filename + ').'
        log(err, True)
        raise IOError

    log('Analysing program...', True)

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
        # check for #define
        if asm.lower().find('#define') >= 0:
            # check formatting of #define-directive
            ops = split_instruction(asm.lower())
            if len(ops) < 3:
                err = 'ERROR: "#define" is missing arguments'
                log(err, True)
            if len(ops) > 3:
                err = 'ERROR: Too much arguments with "#define"'
                log(err, True)
            if ops[0] != '#define':
                err = 'ERROR: Found something before #define. Check your code!'
                log(err, True)
            symbol = ops[1]
            value = ops[2]
            if symbol[0].isdigit():
                err = 'ERROR: Symbol name can not start with a number'
                log(err, True)
            # check if symbol is already defined
            defined_symbols = pinfo['symbols'].keys()
            if symbol in defined_symbols:
                err = 'ERROR: Symbol name "' + symbol + '" already defined.\n'
                err += '\tline ' + str(line_index + 1) + ' -> ' + line.strip()
                log(err, True)
                raise ValueError
            else:
                # if not, add it to the list
                pinfo['symbols'][symbol] = value
            # no need to further analyse this line, go to next
        else:
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
    # Log a list of the symbols that are defined in the program
    log('- Symbols defined in ' + filename + ':', do_print)
    symbols_table = format_symbols_table(pinfo['symbols'], 'symbols', 'value')
    log(symbols_table, do_print)

    # Update program size
    pinfo['size'] = address
    msg = ' - Program size: ' + str(pinfo['size']) + ' bytes.\n\nAnalysis complete.\n\n'
    log(msg, True)

    return pinfo


def load_template(filename, romfilename):
    """
    Load the template of the program ROM.

    :param filename: The program ROM template file name.
    :param romfilename: The file name of the resulting ROM file
    :return: A dictionary with program ROM structure and memory size
    """
    # To put creation date in ROM file
    dt = datetime.now()
    datestr = dt.strftime('--      Created: %H:%M:%S %d-%m-%Y\r\n')
    
    # To put filename in ROM file
    filestr = '--         File: ' + romfilename + '\r\n'
    
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
            if '--      Created' in line:
                tinfo['first_part'].append(datestr)
            elif '--         File' in line:
                tinfo['first_part'].append(filestr)
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
    """
    Generate program ROM file in VHDL containing the instructions of the assembled program

    :param pinfo: A dictionary containing the analyzed program (provided by load_program(...) ).
    :param rom: A dictionary containing the prorgam ROM structure (provided by load_template(...) )
    :param filename: The file name of the VHDL file.
    :return: Nothing
    """
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
    for line in sorted(pinfo['program']):
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
                err = 'ERROR: Jump address not defined for instruction "' + instruction_info['instruction'] \
                      + '" (line ' + str(line + 1) + ').'
                log(err, True)
                raise ValueError

            # lookup address in case label is used
            address = lookup_name(instruction_info['operand_1'], pinfo)
            if address is None:
                err = 'ERROR: Name "' + instruction_info['operand_1'] + '" is not defined (line ' + str(line + 1) + ').'
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

        elif instruction_type == 'jump_conditional':
            # get memory address
            if instruction_info['operand_1'] is None:
                err = 'ERROR: Jump address not defined for instruction "' + instruction_info['instruction']\
                      + '" (line ' + str(line+1) + ').'
                log(err, True)
                raise ValueError

            # lookup address in case label is used
            address = lookup_name(instruction_info['operand_1'], pinfo)
            if address is None:
                err = 'ERROR: Name "' + instruction_info['operand_1'] + '" is not defined (line ' + str(line+1) + ').'
                log(err, True)
                raise ValueError

            # convert hex address to binary representation
            memory_address = address_hex_to_binary(address)

            # look up conditional flag
            conditional_flag = asminfo['instructions'][instruction_info['instruction']]['flag']

            # assemble jump instruction
            rom_line += instruction_opcode + conditional_flag + '",' + instruction_info['comment']
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
            if instruction_info['operand_1'] is None:
                err = 'ERROR: Source/destination register not defined for instruction "'\
                      + instruction_info['instruction'] + '" (line ' + str(line+1) + ').'
                log(err, True)
                raise ValueError
            # look-up symbol
            operand_1 = lookup_name(instruction_info['operand_1'], pinfo)
            try:
                rds_code = asminfo['registers'][operand_1]
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

        elif instruction_type == 'register_to_register' or instruction_type == 'indirect_memory':
            # get destination register code
            if instruction_info['operand_1'] is None:
                err = 'ERROR: Destination register not defined for instruction "'\
                      + instruction_info['instruction'] + '" (line ' + str(line+1) + ').'
                log(err, True)
                raise ValueError
            # look-up symbol
            operand_1 = lookup_name(instruction_info['operand_1'], pinfo)
            try:
                rd_code = asminfo['registers'][operand_1]
            except KeyError:
                err = 'ERROR: Wrong register name "' + instruction_info['operand_1'] + '" (line ' + str(line+1) + ').'
                log(err, True)
                raise ValueError
            # get source register code
            if instruction_info['operand_2'] is None:
                err = 'ERROR: Source register not defined for instruction "'\
                      + instruction_info['instruction'] + '" (line ' + str(line+1) + ').'
                log(err, True)
                raise ValueError
            # look-up symbol
            operand_2 = lookup_name(instruction_info['operand_2'], pinfo)
            try:
                rs_code = asminfo['registers'][operand_2]
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
            # look-up symbol
            operand_1 = lookup_name(instruction_info['operand_1'], pinfo)
            if operand_1 is None:
                err = 'ERROR: Target address name "' + instruction_info['operand_1'] + '" unspecified for instruction "'\
                      + instruction_info['instruction'] + '" (line ' + str(line+1) + ').'
                log(err, True)
                raise ValueError
            else:
                instruction_info['operand_1'] = operand_1
            # make sure the address has the correct length
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
            if instruction_info['operand_2'] is None:
                err = 'ERROR: Source register not defined for instruction "'\
                      + instruction_info['instruction'] + '" (line ' + str(line+1) + ').'
                log(err, True)
                raise ValueError
            # look-up symbol
            operand_2 = lookup_name(instruction_info['operand_2'], pinfo)
            try:
                rs_code = asminfo['registers'][operand_2]
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
            if instruction_info['operand_1'] is None:
                err = 'ERROR: Destination register not defined for instruction "'\
                      + instruction_info['instruction'] + '" (line ' + str(line+1) + ').'
                log(err, True)
                raise ValueError
            # look-up symbol
            operand_1 = lookup_name(instruction_info['operand_1'], pinfo)
            try:
                rd_code = asminfo['registers'][operand_1]
            except KeyError:
                err = 'ERROR: Wrong register name "' + instruction_info['operand_1'] + '" (line ' + str(line+1) + ').'
                log(err, True)
                raise ValueError

            # get memory address or literal
            # check if operand_2 is present
            if instruction_info['operand_2'] is None:
                err = 'ERROR: Literal or memory location unspecified for instruction "'\
                      + instruction_info['instruction'] + '" (line ' + str(line + 1) + ').'
                log(err, True)
                raise ValueError
            # look-up symbol
            operand_2 = lookup_name(instruction_info['operand_2'], pinfo)
            if operand_2 is None:
                err = 'ERROR: Target address name "' + instruction_info['operand_2'] + '" unspecified for instruction "'\
                      + instruction_info['instruction'] + '" (line ' + str(line+1) + ').'
                log(err, True)
                raise ValueError
            else:
                instruction_info['operand_2'] = operand_2
            # check length
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
    """
    Generate the start of a line in the VHDL ROM.

    :param address: address of the ROM line.
    :return: a string containg the start of the ROM line.
    """
    rom_start = '\t\t%3d => "' % address
    return rom_start


def split_instruction(ins):
    """
    Split an assembly instruction into seperate parts.

    :param ins: The assembly line.
    :return: A list with the parts of the instruction.
    """
    newins = ins.replace(',', ' ')
    splitins = newins.split()
    return splitins


def lookup_name(name, pinfo):
    """
    Lookup if a symbol or label name is defined in the program info dictionary.

    :param name: Name to look up.
    :param pinfo: A dictionary containing the program info.
    :return: None if the name does not exist, otherwise the name itself.
    """
    if is_defined(name, asminfo['registers']):
        return name

    if is_defined(name, pinfo['labels']):
        return pinfo['labels'][name]

    if is_defined(name, pinfo['symbols']):
        return pinfo['symbols'][name]

    if is_hex(name):    # should be last to avoid early return on names that can be interpreted as hex (eg: BCD)
        return name

    return None


def address_hex_to_binary(address):
    """
    Convert a hexadecimal address (string representation) to binary (string representation).

    :param address: The address to convert.
    :return: The binary address.
    """
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
    """
    Test if a string is a hexadecimal in string representation.

    :param s: The string to test.
    :return: True if hexadecimal, False if not.
    """
    try:
        int(s, 16)
        return True
    except ValueError:
        return False


def is_defined(s, table):
    """
    Test if a symbol or label is defined.

    :param s: The symbol to look up.
    :param table: A dictionary containing the labels and symbols.
    :return: True if defined, False otherwise.
    """
    try:
        table[s]   # Exploiting possible KeyError
        return True
    except KeyError:
        return False


def format_symbols_table(symbols_list, symbol_name, value='address'):
    """
    Print out the table with symbols and labels in a readable format.

    :param symbols_list:
    :param symbol_name:
    :param value:
    :return: Nothing
    """
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
