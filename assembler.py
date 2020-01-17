import datetime
from random import randint
import sys
import os


INSTRUCTIONS = ['ADD', 'SUB', 'MULU', 'DIVU', 'MOVE', 'CMP', 'BRA', 'BEQ', 'BGT', 'BLT', 'SWAP', 'STOP']
LOC_TABLE = [] # Table to keep track of every location counter change
SYMBOLS = {} # Dictionary that will hold labels and their locations
USED_LABELS = {} # Dictionary that will hold the used labels and their locations
OPCODE = ''
OPERAND = ''
LOCCTR = 0
NUM_ERRORS = 0 # Keeps track of the number of errors



def main(argv):
    filename = argv[0]
    pass1(filename)
    pass2(filename)



def listFileHeader(fname, lst_file):
    # Writes the header to the list file with the date, time, and file location
    today = datetime.datetime.today()
    time = '{:02d}'.format(getattr(today, 'hour')) + ':' + \
           '{:02d}'.format(getattr(today, 'minute')) + ':' + \
           '{:02d}'.format(getattr(today, 'second'))

    dir_path = os.path.dirname(os.path.realpath(__file__))

    lst_file.write('SIM68 ASSEMBLER\t\tVersion 1.00\t\t2017 Sam Farber\n\n')
    lst_file.write('Date: ' + today.strftime('%d %b %Y') + '      ')
    lst_file.write('Time: ' + time + '      Source:\n')
    lst_file.write(dir_path + '/' + fname + '\n\n')


def pass1(fname):
    # Reads in file line by line
    program = readFile(fname)

    # Gets cleaner version of file with no empty lines or tabs
    content = cleanContent(program)
    content = listToUpper(content)

    global LOCCTR
    global NUM_ERRORS

    for i in range(len(content)):
        label = ''

        # A list of the strings that are separated by a space in each line
        strs = content[i].split()

        # Continues if line is not a comment
        if content[i][0] != ';' and content[i][0] != '*':
            LOC_TABLE.append(LOCCTR) # Keeps track of location counter

            if strs[0] == 'END': # end of file
                return
            elif program[i][0] == ' ' or program[i][0] == '\t': # No label
                OPCODE = strs[0]
                OPERAND = strs[1]
            else: # There is a label
                if '(' in strs[0] or ')' in strs[0]: # Labels can't have parens
                    NUM_ERRORS += 1
                else:
                    label = strs[0]
                OPCODE = strs[1]
                OPERAND = strs[2]


            if label != '':
                if SYMBOLS.has_key(label): # Checks if label was already defined
                    NUM_ERRORS += 1

                else:
                    SYMBOLS[label] = LOCCTR # Keeps track of label and it's loc

            if OPCODE in INSTRUCTIONS:
                # Mapping the opcode to the function called to check for errors
                options = {'ADD' : addIsLegal,
                           'SUB' : subIsLegal,
                           'MULU' : muluIsLegal,
                           'DIVU' : divuIsLegal,
                           'MOVE' : moveIsLegal,
                           'CMP' : cmpIsLegal,
                           'BRA' : braIsLegal,
                           'BEQ' : braIsLegal,
                           'BGT' : braIsLegal,
                           'BLT' : braIsLegal,
                           'SWAP' : swapIsLegal,
                           'STOP' : stopIsLegal,
                           }
                isLegal = options[OPCODE](OPERAND)

                if not isLegal:
                    NUM_ERRORS += 1

                else:
                    if OPCODE != 'MOVE': # All non-move instructs increment by 2
                        LOCCTR += 2
                    else:
                        LOCCTR += moveInstrLength(OPERAND) # Depends on mem use

            elif OPCODE == 'ORG':
                # Checks for operand errors here
                if (OPERAND[0] != '$' and OPERAND[0] != '%') and \
                                        not OPERAND.isdigit():
                    NUM_ERRORS += 1
                elif (OPERAND[0] == '$' or OPERAND[0] == '%') and \
                                        not OPERAND[1:].isdigit():
                    NUM_ERRORS += 1

                else:
                    LOCCTR = toDecimal(OPERAND) # Location counter change

            elif OPCODE == 'DS':
                LOCCTR += (2 * toDecimal(OPERAND))

            elif OPCODE == 'DC':
                operlength = len(OPERAND.split(','))
                LOCCTR += 2 * operlength

            else: # Invalid opcode
                NUM_ERRORS += 1



def pass2(fname):
    global NUM_ERRORS

    labels = []
    for elem in SYMBOLS:
        labels.append(elem)

    # Increments ERRORS for the # of times a label's used without being defined
    used_list = []
    for elem in USED_LABELS:
        used_list.append(elem)
    intersection = set(used_list).intersection(labels)

    NUM_ERRORS += len(used_list) - len(intersection)

    # Creates list of each line in file
    program = readFile(fname)
    content = cleanContent(program)
    content = listToUpper(content)

    # Initializes object code output file
    root = fname.partition('.')[0] # Gets root of filename
    hex_fname = root + '.hex'
    hex_file = open(hex_fname, 'a')
    hex_file.write('S004000000FB\n') # Initialize first object record

    # Initializes list output file
    lst_fname = root + '.lst'
    lst_file = open(lst_fname, 'a')
    listFileHeader(fname, lst_file)


    label = ''

    loc_count = 0 # Counter for indexing LOC_TABLE
    obj_org = str(0) # Location to write at beginning of line in object file
    obj_line = '' # The line that is written to the object file

    for i in range(len(content)):
        # A list of the strings that are separated by a space in each line
        strs = content[i].split()

        obj_code = ''
        line_len = 24 if i > 8 else 25

        # Continues if line is not a comment
        if content[i][0] != ';' and content[i][0] != '*':
            if strs[0] == 'END': # End of file outputs for both files
                for _ in range(line_len):
                    lst_file.write(' ')
                lst_file.write(str(i + 1) + ' ') # Index number
                lst_file.write(program[i] + '\n\n') # Original program
                lst_file.write('Assembly errors: ' + str(NUM_ERRORS))
                lst_file.close()

                obj_count = decToHex(len(obj_line) / 2 + 3)[2:]
                obj_line = 'S1' + obj_count + obj_org + obj_line + randHex()
                hex_file.write(obj_line + '\n')
                hex_file.write('S9031000EC')
                hex_file.close()
                return

            elif program[i][0] == ' ' or program[i][0] == '\t': # No label
                OPCODE = strs[0]
                OPERAND = strs[1]
            else: # There is a label
                label = strs[0]
                OPCODE = strs[1]
                OPERAND = strs[2]

            if OPCODE in INSTRUCTIONS:
                # Mapping the opcode to the function to be called
                options = {'ADD' : add,
                           'SUB' : sub,
                           'MULU' : mulu,
                           'DIVU' : divu,
                           'MOVE' : move,
                           'CMP' : cmp,
                           'BRA' : bra,
                           'BEQ' : beq,
                           'BGT' : bgt,
                           'BLT' : blt,
                           'SWAP' : swap,
                           'STOP' : stop,
                           }
                # Hex code generated from instruction and its operand
                obj_code = options[OPCODE](OPERAND)

            elif OPCODE == 'DC':
                # Converts operand to object code
                obj_code = decToHex(int(OPERAND))

            if OPCODE == 'DS':
                # If object file line is too long, a new line is created with
                # a new location, otherwise, location is kept track of still
                ds_len = int(OPERAND) * 2
                if ds_len + len(obj_line) > 32:
                    obj_line = 'S1' + decToHex(len(obj_line)/2 + 3)[2:] \
                                    + obj_org + obj_line + randHex()
                    hex_file.write(obj_line + '\n')
                obj_org = decToHex(LOC_TABLE[loc_count+1])


            if OPCODE == 'ORG':
                lst_line = decToHex(LOC_TABLE[loc_count + 1]) + ' ' + obj_code

                if hex_file.tell() > 13: # Checks if its the first line in file
                    obj_line = 'S1' + decToHex(len(obj_line)/2 + 3)[2:] \
                                    + obj_org + obj_line + randHex()
                    hex_file.write(obj_line + '\n')
                    obj_line = ''
                obj_org = decToHex(LOC_TABLE[loc_count + 1])



            else:
                lst_line = decToHex(LOC_TABLE[loc_count]) + ' ' + obj_code

            loc_count += 1
            lst_file.write(lst_line)

            for _ in range(line_len - len(lst_line)):
                lst_file.write(' ')

            line_num = str(i + 1)
            lst_file.write(line_num + ' ') # Writes index number in list file
            lst_file.write(program[i] + '\n') # Writes original program

            # Used to keep track of object code that didn't fit in prev line
            split_obj = obj_code.replace(' ', '')
            split_obj = [split_obj[i:i+4] for i in range(0, len(split_obj), 4)]

            for i in range(len(split_obj)):
                if len(obj_line) < 32: # Can keep writing to current line
                    obj_line += split_obj[0]
                    del split_obj[0]

                else: # Make a new line
                    obj_line = 'S113' + obj_org + obj_line + randHex()
                    hex_file.write(obj_line + '\n')
                    obj_line = ''.join(split_obj)
                    obj_org = toDecimal(obj_org) + 16
                    obj_org = decToHex(obj_org)
                    break

    # If end is not called in the program
    lst_file.write('\n\nAssembly errors: ' + str(NUM_ERRORS))
    lst_file.close()

    obj_count = decToHex(len(obj_line) / 2 + 3)[2:]
    obj_line = 'S1' + obj_count + obj_org + obj_line + randHex()
    hex_file.write(obj_line + '\n')
    hex_file.write('S9031000EC')
    hex_file.close()



def readFile(fname):
    # Reads in file line by line
    with open(fname) as f:
        program = f.readlines() # List of each line
    program = [x.replace('\n','') for x in program] # Converts '\n' to empty str
    program = [x.replace('\r','') for x in program] # Converts '\r' to empty str
    program = filter(None, program) # Removes empty string elements from list

    return program



def addIsLegal(operand):
    if ',' not in operand: # Comma has to be present
        return False
    elif operand[0] != 'D' or int(operand[1]) > 3 or int(operand[1]) < 0:
        return False
    elif operand[3] != 'D' and operand[3] != 'A':
        return False
    elif int(operand[4]) > 3 or int(operand[4]) < 0:
        return False

    return True


def subIsLegal(operand):
    if ',' not in operand: # Comma has to be present
        return False
    elif operand[0] != 'D' or int(operand[1]) > 3 or int(operand[1]) < 0:
        return False
    elif operand[3] != 'D' or int(operand[4]) > 3 or int(operand[4]) < 0:
        return False

    return True

def muluIsLegal(operand):
    # Same operand requirements as sub
    return subIsLegal(operand)

def divuIsLegal(operand):
    # Same operand requirements as sub
    return subIsLegal(operand)

def moveIsLegal(operand):
    global USED_LABELS

    if ',' not in operand or len(operand.split(',')) != 2 or len(operand) < 5:
        return False
    params = operand.split(',') # list of both parameters
    for i in range(2):
        if params[i][-1] == ')' and params[i][-4] == '(':
            if params[i][-3] == 'A' and int(params[i][-2]) >= 0 and \
                                        int(params[i][-2]) <= 3:
                USED_LABELS[params[i][0:-4]] = LOCCTR # Accounts for used labels
            else:
                return False

        elif len(params[i]) != 2: # Non mem use has to have length 2
            return False
        elif params[i][0] != 'A' and params[i][0] != 'D':
            return False
        elif int(params[i][1]) > 3 or int(params[i][1]) < 0: # Can only be 0-3
            return False

    return True

def cmpIsLegal(operand):
    # Same operand requirements as sub
    return subIsLegal(operand)

def braIsLegal(operand):
    global USED_LABELS
    USED_LABELS[operand] = LOCCTR # Keeps track of used labels

    if ',' not in operand and '(' not in operand: # No commas or parens
        return True

    return False

def swapIsLegal(operand):
    if len(operand) != 2: # Length has to be 2
        return False
    elif operand[0] != 'D' or int(operand[1]) > 3 or int(operand[1]) < 0:
        return False

    return True

def stopIsLegal(operand):
    return operand == '#$2700' # Only legal operand for stop



def add(operand):
    if not addIsLegal(operand):
        return ''

    bin_code = '1101' # Binary code to start all add instructions
    params = operand.split(',')

    # Source register binary representation
    source_reg = toThreeDig("{0:b}".format(int(params[1][1])))

    bin_code += source_reg

    if params[1][0] == 'D':
        bin_code += '001000'
    else:
        bin_code += '011000'

    # Destination register binary representation
    dest_reg = toThreeDig("{0:b}".format(int(params[0][1])))

    bin_code += dest_reg

    return binToHex(bin_code)


def sub(operand):
    if not subIsLegal(operand):
        return ''

    bin_code = '1001' # Binary code to start all sub instructions
    params = operand.split(',')

    # Source register binary representation
    source_reg = toThreeDig("{0:b}".format(int(params[1][1])))

    bin_code += source_reg

    bin_code += '001000'

    # Destination register binary representation
    dest_reg = toThreeDig("{0:b}".format(int(params[0][1])))

    bin_code += dest_reg

    return binToHex(bin_code)

def mulu(operand):
    if not muluIsLegal(operand):
        return ''

    bin_code = '1100' # Binary code to start all mulu instructions
    params = operand.split(',')

    # Source register binary representation
    source_reg = toThreeDig("{0:b}".format(int(params[1][1])))

    bin_code += source_reg

    bin_code += '011000'

    # Destination register binary representation
    dest_reg = toThreeDig("{0:b}".format(int(params[0][1])))

    bin_code += dest_reg

    return binToHex(bin_code)

def divu(operand):
    if not divuIsLegal(operand):
        return ''

    bin_code = '1000' # Binary code to start all divu instructions
    params = operand.split(',')

    # Source register binary representation
    source_reg = toThreeDig("{0:b}".format(int(params[1][1])))

    bin_code += source_reg

    bin_code += '011000'

    # Destination register binary representation
    dest_reg = toThreeDig("{0:b}".format(int(params[0][1])))

    bin_code += dest_reg

    return binToHex(bin_code)

def move(operand):
    if not moveIsLegal(operand):
        return ''

    bin_code = '0011' # Binary code to start all move instructions
    params = operand.split(',')

    if '(' not in operand: # No memory usage
        # Source register binary representation
        source_reg = toThreeDig("{0:b}".format(int(params[1][1])))

        bin_code += source_reg

        if params[1][0] == 'D':
            if params[0][0] == 'D':
                bin_code += '000000'
            else:
                bin_code += '000001'
        else:
            if params[0][0] == 'D':
                bin_code += '001000'
            else:
                bin_code += '001001'

        # Destination register binary representation
        dest_reg = toThreeDig("{0:b}".format(int(params[0][1])))

        bin_code += dest_reg

        return binToHex(bin_code)

    elif operand.count('(') == 1: # One parameter uses memory
        if '(' in params[1]:
            # Source register binary representation
            source_reg = toThreeDig("{0:b}".format(int(params[1][-2])))
            bin_code += source_reg

            if params[0][0] == 'A':
                bin_code += '101001'
            else:
                bin_code += '101000'

            # Destination register binary representation
            dest_reg = toThreeDig("{0:b}".format(int(params[0][1])))
            bin_code += dest_reg

            bin_code = binToHex(bin_code)

            label = params[1].split('(')[0]
            if not SYMBOLS.has_key(label):
                return ''

            bin_code += ' ' + decToHex(SYMBOLS[label])

            return bin_code

        else:
            # Source register binary representation
            source_reg = toThreeDig("{0:b}".format(int(params[1][1])))
            bin_code += source_reg

            if params[1][0] == 'A':
                bin_code += '001101'
            else:
                bin_code += '000101'

            # Destination register binary representation
            dest_reg = toThreeDig("{0:b}".format(int(params[0][-2])))
            bin_code += dest_reg

            bin_code = binToHex(bin_code)

            label = params[0].split('(')[0]
            if not SYMBOLS.has_key(label): # Checks if label is in symbols
                return ''

            bin_code += ' ' + decToHex(SYMBOLS[label])

            return bin_code

    else: # Both parameters use memory
        # Source register binary representation
        source_reg = toThreeDig("{0:b}".format(int(params[1][-2])))
        bin_code += source_reg

        bin_code += '101101'

        # Destination register binary representation
        dest_reg = toThreeDig("{0:b}".format(int(params[0][-2])))
        bin_code += dest_reg

        bin_code = binToHex(bin_code)

        label1 = params[0].split('(')[0]
        label2 = params[1].split('(')[0]
        # Checks to make sure labels are in the symbol table
        if not SYMBOLS.has_key(label1) or not SYMBOLS.has_key(label2):
            return ''

        bin_code += ' ' + decToHex(SYMBOLS[label1]) + ' ' + \
                          decToHex(SYMBOLS[label2])

        return bin_code


def cmp(operand):
    if not cmpIsLegal(operand):
        return ''

    bin_code = '1011' # Binary code to start all divu instructions
    params = operand.split(',')

    # Source register binary representation
    source_reg = toThreeDig("{0:b}".format(int(params[1][1])))

    bin_code += source_reg

    bin_code += '001000'

    # Destination register binary representation
    dest_reg = toThreeDig("{0:b}".format(int(params[0][1])))

    bin_code += dest_reg

    return binToHex(bin_code)

def forAllBranch(bin_code, operand):
    if not braIsLegal(operand):
        return ''

    hex_code = binToHex(bin_code) # Converts binary representation to hex

    displ = SYMBOLS[operand] - USED_LABELS[operand] # Finds the displacement
    displ = twosComplHex(displ) # Allows for negative hex values
    hex_code += displ

    return hex_code

def bra(operand):
    return forAllBranch('01100000',operand)

def beq(operand):
    return forAllBranch('01100111', operand)

def bgt(operand):
    return forAllBranch('01101110', operand)

def blt(operand):
    return forAllBranch('01101101', operand)

def swap(operand):
    bin_code = '0100100001000'

    # Destination register binary representation
    dest_reg = toThreeDig("{0:b}".format(int(operand[1])))
    bin_code += dest_reg

    return binToHex(bin_code)

def stop(operand):
    bin_code = '0100111001110010'
    return binToHex(bin_code)

def cleanContent(program):
    # Removes new lines from elements in list
    # Replaces tabs with spaces in each string
    content = []
    for i in range(len(program)):
        content.append(program[i])#.strip('\n'))
        content[i] = content[i].replace('\t', ' ')

    content = [x.strip() for x in content] # Removes all preceding spaces
    content = filter(None, content) # Removes empty string elements from list

    return content

def listToUpper(list):
    # Converts all strings in list to uppercase
    for i in range(len(list)):
        list[i] = list[i].upper()
    return list


def toThreeDig(bin_num):
    # Used for binary representation of the register numbers
    while len(bin_num) != 3:
        bin_num = '0' + bin_num

    return bin_num

def binToHex(bin_num):
    # Converts binary to a 4 digit hex code
    split_bin_code = [bin_num[i:i+4] for i in range(0, len(bin_num), 4)]
    hex_code = ''

    for i in range(len(bin_num)/4):
        hex_code += hex(int(split_bin_code[i], 2))[2:].upper()

    return hex_code

def decToHex(num):
    # Converts decimal to 4 digit hex code
    hex_num = hex((num + (1 << 16)) % (1 << 16)).split('x')[-1]
    while len(hex_num) != 4:
        hex_num = '0' + hex_num

    return hex_num.upper()

def twosComplHex(num):
    # Returns two's complement for branching displacement
    hex_num = hex((num + (1 << 8)) % (1 << 8)).split('x')[-1]
    if len(hex_num) != 2:
        hex_num = '0' + hex_num

    return hex_num.upper()

def randHex():
    # Returns a 2 digit random hex value
    rand = randint(1,255)
    randHex = hex(rand).split('x')[-1].upper()
    if len(randHex) == 1:
        randHex = '0' + randHex
    return randHex

def toDecimal(operand):
    # Converts hex or binary number to decimal
    if ',' not in operand:
        if operand[0] == '$':
            return int(operand[1:], 16)

        elif operand[0] == '%':
            return int(operand[1:], 2)[2:]

        elif operand in SYMBOLS:
            return SYMBOLS[operand]

        else:
            return int(operand, 16)


def moveInstrLength(operand):
    # Decides how much to increment locctr based on move operand
    if '(' not in operand:
        return 2
    else:
        return 4 if operand.count('(') == 1 else 6





if __name__ == "__main__": main(sys.argv[1:])
