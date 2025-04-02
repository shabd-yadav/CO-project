import sys

REG = [0] * 32
REG[2] = 380  # x2 = sp initialized to 380
PC = 0

# Memory initialized using specified hex addresses
memory_values = {
    "0x00010000": 0, "0x00010004": 0, "0x00010008": 0, "0x0001000C": 0,
    "0x00010010": 0, "0x00010014": 0, "0x00010018": 0, "0x0001001C": 0,
    "0x00010020": 0, "0x00010024": 0, "0x00010028": 0, "0x0001002C": 0,
    "0x00010030": 0, "0x00010034": 0, "0x00010038": 0, "0x0001003C": 0,
    "0x00010040": 0, "0x00010044": 0, "0x00010048": 0, "0x0001004C": 0,
    "0x00010050": 0, "0x00010054": 0, "0x00010058": 0, "0x0001005C": 0,
    "0x00010060": 0, "0x00010064": 0, "0x00010068": 0, "0x0001006C": 0,
    "0x00010070": 0, "0x00010074": 0, "0x00010078": 0, "0x0001007C": 0
}

MEMORY_KEYS = list(memory_values.keys())

# Helper functions
def bin_to_dec(binary, signed=True):
    if not signed:
        return int(binary, 2)
    if binary[0] == '1':
        return int(binary, 2) - (2 ** len(binary))
    else:
        return int(binary, 2)

def dec_to_bin(val, bits=32):
    if val < 0:
        val = (2 ** bits) + val
    return format(val, f'0{bits}b')

def extract_fields(binary):
    return {
        'opcode': binary[25:],
        'rd': int(binary[20:25], 2),
        'funct3': binary[17:20],
        'rs1': int(binary[12:17], 2),
        'rs2': int(binary[7:12], 2),
        'funct7': binary[0:7],
        'imm_i': bin_to_dec(binary[0:12]),
        'imm_b': bin_to_dec(binary[0] + binary[24] + binary[1:7] + binary[20:24] + '0', signed=True),
    }

def handle_r_type(fields):
    rs1, rs2, rd = fields['rs1'], fields['rs2'], fields['rd']
    funct3, funct7 = fields['funct3'], fields['funct7']

    if funct3 == '000' and funct7 == '0000000':  # add
        REG[rd] = REG[rs1] + REG[rs2]
    elif funct3 == '000' and funct7 == '0100000':  # sub
        REG[rd] = REG[rs1] - REG[rs2]
    elif funct3 == '010':  # slt
        REG[rd] = int(REG[rs1] < REG[rs2])
    elif funct3 == '101':  # srl
        shift_amount = REG[rs2] % 32
        REG[rd] = int(REG[rs1] % (2 ** 32) // (2 ** shift_amount))
    elif funct3 == '110':  # or
        REG[rd] = REG[rs1] | REG[rs2]
    elif funct3 == '111':  # and
        REG[rd] = REG[rs1] & REG[rs2]

def handle_i_type(fields):
    rs1, rd = fields['rs1'], fields['rd']
    imm = fields['imm_i']
    if fields['opcode'] == '0010011':  # addi
        REG[rd] = REG[rs1] + imm
    elif fields['opcode'] == '1100111':  # jalr
        global PC
        temp = PC + 4
        PC = (REG[rs1] + imm) & ~1
        REG[rd] = temp

def handle_b_type(fields):
    rs1, rs2 = fields['rs1'], fields['rs2']
    imm = fields['imm_b']
    if fields['funct3'] == '000':  # beq
        if REG[rs1] == REG[rs2]:
            return imm
    return 0

def handle_instruction(fields):
    opcode = fields['opcode']
    if opcode == '0110011':
        handle_r_type(fields)
    elif opcode == '0010011' or opcode == '1100111':
        handle_i_type(fields)

def dump_state(fout):
    # Print PC normally, but each register as an unsigned 32-bit value.
    fout.write(f"{PC} " + ' '.join(str(REG[i] & 0xFFFFFFFF) for i in range(32)) + "\n")

def dump_memory(fout):
    for addr in MEMORY_KEYS:
        fout.write(f"{addr}:{memory_values[addr]}\n")

def simulate(input_file, output_file):
    global PC, REG
    REG = [0] * 32
    REG[2] = 380  # Set x2 = sp = 380
    PC = 0

    with open(input_file, 'r') as fin:
        instructions = [line.strip() for line in fin.readlines() if line.strip()]

    with open(output_file, 'w') as fout:
        while PC < len(instructions) * 4:
            instr_index = PC // 4
            instr = instructions[instr_index]

            if instr == '00000000000000000000000001100011':  # HALT
                dump_state(fout)
                break

            fields = extract_fields(instr)

            if fields['opcode'] == '1100011':  # beq
                offset = handle_b_type(fields)
                if offset != 0:
                    dump_state(fout)       # Dump state before branch is taken
                    PC += offset
                    dump_state(fout)       # Dump state immediately after branch jump
                else:
                    PC += 4
                    dump_state(fout)
            else:
                handle_instruction(fields)
                PC += 4
                dump_state(fout)

        dump_memory(fout)

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python mysim.py <input_file> <output_file>")
    else:
        simulate(sys.argv[1], sys.argv[2])
