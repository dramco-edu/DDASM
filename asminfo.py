asminfo = {
    'instructions': {
        'nop': {
            'opcode': '00000',
            'type': 'jump_no_address'
        },
        'reti': {
            'opcode': '00001',
            'type': 'jump_no_address'
        },
        'retc': {
            'opcode': '00010',
            'type': 'jump_no_address'
        },
        'call': {
            'opcode': '00011',
            'type': 'jump'
        },
        'jmp': {
            'opcode': '00100',
            'type': 'jump'
        },
        'jz': {
            'opcode': '00101',
            'type': 'jump_conditional',
            'flag': '000'
        },
        'jc': {
            'opcode': '00101',
            'type': 'jump_conditional',
            'flag': '001'
        },
        'je': {
            'opcode': '00101',
            'type': 'jump_conditional',
            'flag': '010'
        },
        'jg': {
            'opcode': '00101',
            'type': 'jump_conditional',
            'flag': '011'
        },
        'js': {
            'opcode': '00101',
            'type': 'jump_conditional',
            'flag': '100'
        },
        'push': {
            'opcode': '01110',
            'type': 'single_register'
        },
        'pop': {
            'opcode': '01111',
            'type': 'single_register'
        },
        'not': {
            'opcode': '10000',
            'type': 'single_register'
        },
        'rr': {
            'opcode': '10001',
            'type': 'single_register'
        },
        'rl': {
            'opcode': '10010',
            'type': 'single_register'
        },
        'swap': {
            'opcode': '10011',
            'type': 'single_register'
        },
        'movr': {
            'opcode': '01011',
            'type': 'register_to_register'
        },
        'andr': {
            'opcode': '10101',
            'type': 'register_to_register'
        },
        'orr': {
            'opcode': '10111',
            'type': 'register_to_register'
        },
        'xorr': {
            'opcode': '11011',
            'type': 'register_to_register'
        },
        'addr': {
            'opcode': '11101',
            'type': 'register_to_register'
        },
        'subr': {
            'opcode': '',
            'type': 'register_to_register'
        },
        'cmpr': {
            'opcode': '11111',
            'type': 'register_to_register'
        },
        'str': {
            'opcode': '01101',
            'type': 'register_to_memory'
        },
        'ldr': {
            'opcode': '01100',
            'type': 'x_to_register'
        },
        'movl': {
            'opcode': '01010',
            'type': 'x_to_register'
        },
        'andl': {
            'opcode': '10100',
            'type': 'x_to_register'
        },
        'orl': {
            'opcode': '10110',
            'type': 'x_to_register'
        },
        'xorl': {
            'opcode': '11000',
            'type': 'x_to_register'
        },
        'addl': {
            'opcode': '10100',
            'type': 'x_to_register'
        },
        'subl': {
            'opcode': '11100',
            'type': 'x_to_register'
        },
        'cmpl': {
            'opcode': '11110',
            'type': 'x_to_register'
        },
        'ldrr': {
            'opcode': '00110',
            'type': 'indirect_memory'
        },
        'strr': {
            'opcode': '00111',
            'type': 'indirect_memory'
        }
    },
    'virtual_instructions': {
        'inc': {
            'replace_with': 'addl',
            'operand_2': '01'
        },
        'dec': {
            'replace_with': 'subl',
            'operand_2': '01'
        },
        'clr': {
            'replace_with': 'movl',
            'operand_2': '00'
        },
        'jump': {
            'replace_with': 'jmp',
            'operand_2': None
        }
    },
    'registers': {
        'r0': '000',
        'r1': '001',
        'r2': '010',
        'r3': '011',
        'r4': '100',
        'r5': '101',
        'r6': '110',
        'r7': '111'
    }
}


