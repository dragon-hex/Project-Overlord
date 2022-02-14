# lance is vela, but interpreted, this will not compile your code.

import random # => for random number engine.

VERSION_STR = "1.0"

class not_closed_string(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

def tokenize(lines):
    """
    Find tokens and make them more evident.
    """
    line_index, line_counter = 0, len(lines)
    parsed_lines = []
    while line_index < line_counter:
        
        line                        = lines[line_index]
        token_index, token_counter  = 0, len(line)
        in_string, in_string_ch     = False, ' '
        acc, tokens                 = "", []

        while token_index < token_counter:
            token = line[token_index]
            if token == ' ' and not in_string:
                if len(acc) > 0: tokens.append(acc)
                acc = ""
            elif token == ',' and not in_string:
                # NOTE: the language do not need ','
                pass
            elif token == ';' and not in_string:
                if len(acc) > 0: tokens.append(acc)
                break
            elif token in ("'", '"') and not in_string:
                if len(acc) > 0: tokens.append(acc)
                acc, in_string_ch, in_string = token, token, True
            elif token in ("'", '"') and in_string and token == in_string_ch:
                if len(acc) > 0: tokens.append(acc+token)
                in_string, in_string_ch, acc = False, ' ', ''
            else:
                acc += token
            token_index += 1
        
        # check some stuff.
        if len(acc) > 0:    tokens.append(acc)
        if len(tokens) > 0: parsed_lines.append(tokens)
        if in_string:       raise not_closed_string("not closed string in line %d" % (line_index + 1))

        # if everything great, advance next line.
        line_index += 1
    return parsed_lines

class bad_syntax(Exception):
    def __init__(self, message):
        self.message = message
        self.__init__(message)

def organize_code(tokenized_code):
    """
    Split the code in the sections.
    Convert the tokenized code in more easy to manage one.
    """
    # Split the label in code sections, the labels are a way to do it.
    # This helps when determining the JUMP locations and offsets.
    labels, at_label = {'data':{'code':[],'priority':-1}}, '__dump'
    index, size = 0, len(tokenized_code)
    while index < size:
        token_list = tokenized_code[index]
        token_i, token_n = 0, len(token_list)
        p_code=[]
        while token_i < token_n:
            token = token_list[token_i]
            if token[len(token)-1] == ':':
                name = token[0:len(token)-1]
                at_label=name ; labels[at_label]={'code':[],'priority':0}
            elif token == 'data':
                # NOTE: remove the token 'data' and put the data
                # on the organized code section.
                if token_i + 2 > token_n:
                    raise bad_syntax("missing data arguments in line: %d" % index)
                data_struct = []
                for i in range(token_i, token_i+3):
                    data_struct.append(token_list[i])
                labels['data']['code'].append(data_struct)
                token_i = token_i + 2
            else:
                p_code.append(token)
            token_i = token_i + 1
        
        if len(p_code) > 0: labels[at_label]['code'].append(p_code)
        # finish by indexing the next line.
        index = index + 1
    
    # NOTE: say to data section to jump to the main function
    labels['data']['code'].append(["jump", "main"])
    return labels

def __show_organized_code(organized_code: dict):
    print("There are %d labels found." % len(organized_code.keys()))
    for key in organized_code.keys():
        print("[%s] begins..." % key)
        for code in organized_code[key]['code']:
            print("\t" + str(code))

class interpreter_err(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

ERR_INVALID_TYPE = 1
ERR_UNKNOWN_INSTRUCTION = 2
ERR_INVALID_LABEL = 3
ERR_INVALID_SYSCALL = 4

class interpreter:
    def __init__(self, code):
        """
        Main vela interpreter.
        ----------------------
        On here, you should put your organized code.
        """

        # some core setttings
        self.output = None
        self.name = "lance"

        # define the code
        self.code = code

        # error controller.
        self.status = 0
        self.error_str = None
        self.error_code = 0

        # pc: localizes where the code is on the label.
        self.pc = 0
        self.__skip_pc_increment = False
        
        # sp: localizes where the label is on the binary.
        # NOTE: we don't use this on the interpreter cuz'
        # we only interpreting data on this version.
        self.sp = 0
    
        # status: store the CMPR flags.
        self.equal_state    = False
        self.greater_state  = False
        
        # regs: general propose registers.
        self.regs = []

        # at_label: where the program is, since the
        # entire system is based in labels.
        # NOTE: always init in data section.
        self.at_label = 'data'
        self.call_stack = []

        # vars: since why not? variables makes easy for
        # develop simple scripts.
        self.vars = {}

        # if the machine is running.
        self.running = True

        # => flat code & prepare to execution <=
        self.__prepare()

        # => setup the syscalls <=
        self.__random_generator = random.Random()

        self.__setup_syscalls()
        self.__load_syscalls_utils()

        # => load the opcodes <=
        self.__load_opcodes()
    
    def __load_syscalls_utils(self):
        sysc_table = [
            "sysc_term_show",
            "sysc_term_input",
            "sysc_debug_regs",
            "sysc_debug_vars",
            "sysc_random_numbers",
            "sysc_set_seed"
        ]
        # => map all the syscalls <=
        for index in range(0,len(sysc_table)):
            self.set_var(sysc_table[index], index)

    def __setup_syscalls(self):
        # setup the syscalls
        self.syscalls = [
            # => show input & output <=
            self.__term_show,
            self.__term_get,

            # => debugging stuff <=
            self.__debug_regs,
            self.__debug_vars,

            # => random numbers <=
            self.__sysc_random_numbers,
            self.__sysc_set_seed
        ]
    
    def __load_opcodes(self):
        """load the opcodes!"""
        # setup the opcode table.
        self.op_dict = {

            # data initializers.
            'data': [2, self.perf_data],

            # data move and control.
            'move': [2, self.perf_move],

            # math operations.
            'add':  [2, self.perf_add],
            'sub':  [2, self.perf_sub],
            'mul':  [2, self.perf_mul],
            'div':  [2, self.perf_div],

            # system interaction.
            'sysc': [1, self.perf_sysc],

            # code direction selector.
            'jump': [1, self.perf_jump],
            'call': [1, self.perf_call],
            'retn': [0, self.perf_retn],

            # simple increment/decrement.
            'inc':  [1, self.perf_inc],
            'dec':  [1, self.perf_dec],

            # generic comparasions.
            'cmpr': [2, self.perf_cmpr],
            'je':   [1, self.perf_je],
            'jne':  [1, self.perf_jne],
            'ce':   [1, self.perf_ce],
            'cne':  [1, self.perf_cne],

            # string operations.
            'smgr': [2, self.perf_smgr],
            'spop': [2, self.perf_spop],
            'stin': [2, self.perf_stin],
            'sadd': [2, self.perf_sadd],
            'inst': [2, self.perf_inst]
        }
    
    def __exit_interpreter(self):
        self.code = self.regs[0]
        self.running = False
    
    def __sysc_set_seed(self, interpreter):
        seed = self.regs[0]
        if isinstance(seed, int):
            self.__random_generator(seed)

    def __sysc_random_numbers(self, interpreter):
        min_r   = self.regs[0]
        max_r   = self.regs[1]
        if isinstance(min_r, int) and isinstance(max_r, int):
            num_g = self.__random_generator.randint(min_r, max_r)
            self.regs[2] = num_g

    def __debug_regs(self, interpreter):
        """ print the registers! """
        if self.output:
            self.output.write("lance: [Registers -- r0 => r10]")
            for index in range(0, 10+1):
                # TODO: optimize this code.
                self.output.write("lance: [%d] type = %s: %s" % (
                    index,
                    str(type(self.regs[index])),
                    str(self.regs[index])
                ))
            self.output.write("lance: [end of the registers]")
    
    def __debug_vars(self, interpreter):
        """ print the vars! """
        if self.output:
            self.output.write("lance: [Vars: There are %d vars]" % len(self.vars.keys()))
            for key in self.vars.keys():
                self.output.write("lance: [%s] type = %s, value = %s" % (
                    key,
                    str(type(self.vars[key])),
                    str(self.vars[key])
                ))
            self.output.write("lance: [end of the vars]")
    
    def __term_show(self, interpreter):
        # show something on the screen.
        if self.output:
            self.output.write(str(self.regs[0]) if self.regs[0] != -10 else '\n')
    
    def __term_get(self, interpreter):
        self.regs[0] = input()

    def __prepare(self):
        """
        Adequate your organized code to the linear style of execution, also
        initializes the registers and the core variables.
        """
        # flat the code.
        flatten_code = {}
        for label in self.code.keys():
            flatten_code[label]={'code':[]}
            for code_stack in self.code[label]['code']:
                for token in code_stack:
                    flatten_code[label]['code'].append(token)
        self.code = flatten_code
        # setup the registers and vars.
        self.regs = [0 for index in range(0, 10+1)]
        self.vars = {}
        self.__setup_progvars()
    
    def __setup_progvars(self):
        self.set_var("VERSION", VERSION_STR)
        self.set_var("SCRIPT_NAME", '?')

    def set_var(self, var_name, value):
        """
        Quick set var function.
        """
        self.vars[var_name] = value
    
    def __get_value_quick(self, token: str):
        # => return the value from a source
        if self.vars.get(token) != None:
            return self.vars.get(token)
        elif token.replace('-','').isdigit():
            return int(token)
        elif token in ("pc", "sp") or token[0] == 'r':
            if      token == "pc": return self.pc
            elif    token == "sp": return self.sp
            elif    token[0] == 'r':
                r_number = token[1:len(token)]
                r_number = int(r_number)
                return self.regs[r_number]
        elif token[0] in ("'",'"'):
            return token[1:len(token)-1]
        else:
            return None
        
    def __set_value_quick(self, target: str, value):
        # => set the value to a target.
        if self.vars.get(target) != None:
            self.vars[target] = value
        elif target.replace('-','').isdigit():
            # TODO: you can't move int to int.
            # so make this a syntax error.
            return value
        elif target in ("pc", "sp") or target[0] == 'r':
            if      target == "pc": self.pc = value
            elif    target == "sp": self.sp = value
            elif    target[0] == 'r':
                r_number = target[1:len(target)]
                if not r_number.isdigit():
                    return self.error("invalid register %s" % target, ERR_INVALID_TYPE)
                r_number = int(r_number)
                self.regs[r_number] = value
                return value
        else:
            return self.error("unknown data %s?" % target, ERR_INVALID_TYPE)
    
    def error(self, err, code):
        # halt the machine here.
        self.error_str = err
        self.error_code = code
        self.running = False
    
    def __make_sure(self, eval, err, code):
        """ just a simple assert function actually... """
        if not eval:
            self.error(err, code)
            raise interpreter_err("%s" % err)

    def perf_sysc(self, args):
        invoke = args[0]
        invoke = self.__get_value_quick(invoke)
        self.__make_sure(
            (
                isinstance(invoke, int) and
                invoke < len(self.syscalls)
            ), 
            "invalid syscall %s!" % str(invoke), ERR_INVALID_SYSCALL
        )
        self.syscalls[invoke](self)
    
    def perf_spop(self, args):
        # => remove last char from a string.
        source = args[0]
        target = args[1]
        source_v = self.__get_value_quick(source)
        self.__set_value_quick(target, source_v[len(source_v)-1])
        self.__set_value_quick(source, source_v[0:len(source_v)-1])

    def perf_sadd(self, args):
        # => add a string...
        pass
    
    def perf_inst(self, args):
        # transform something into string
        # and move to the destination.
        source = args[0]
        source = str(self.__get_value_quick(source))

        target = args[1]
        self.__set_value_quick(target, source)

    def perf_stin(self, args):

        # set the source.
        source = args[0]
        source_v = self.__get_value_quick(source)

        # Attempt to transform to number.
        try:
            source_iv = int(source_v)
        except:
            # NOTE: case the transformation fails, then dump
            # on the r0 a 1 value.
            self.regs[0] = 1
            return

        # convert to number and store in target.
        target = args[1]
        self.__set_value_quick(target, source_iv)

    def perf_smgr(self, args):
        # merge a string together.
        source = args[0]
        target = args[1]

        source_v = self.__get_value_quick(source)
        target_v = self.__get_value_quick(target)
        final_mgr = target_v + source_v

        self.__set_value_quick(target, final_mgr)

    def perf_add(self, args):
        x = args[0]
        y = args[1]

        # y += x (cuz' x is source.)
        value_x = self.__get_value_quick(x)
        value_y = self.__get_value_quick(y)
        self.__set_value_quick(y, value_x + value_y)
    
    def perf_sub(self, args):
        x = args[0]
        y = args[1]

        # y -= x
        value_x = self.__get_value_quick(x)
        value_y = self.__get_value_quick(y)
        self.__set_value_quick(y, value_y - value_x)
    
    def perf_mul(self, args):
        x = args[0]
        y = args[1]

        # y *= x
        value_x = self.__get_value_quick(x)
        value_y = self.__get_value_quick(y)
        self.__set_value_quick(y, value_x * value_y)
    
    def perf_div(self, args):
        x = args[0]
        y = args[1]

        # y /= x
        value_x = self.__get_value_quick(x)
        value_y = self.__get_value_quick(y)
        self.__set_value_quick(y, value_y / value_x)

    def perf_cmpr(self, args):
        x = args[0]
        y = args[1]

        value_x = self.__get_value_quick(x)
        value_y = self.__get_value_quick(y)
        
        try:
            # TODO: prevent the strings of crashing the comparasion.
            self.greater_state  = (value_x > value_y)
        except: self.greater_state = False
        self.equal_state    = (value_x == value_y)

    def __perform_conditional_jump(self, condition, label, save_call=False):
        if condition:
            self.__make_sure(self.code.get(label)!=None,
                "label %s was not found." % label, ERR_INVALID_LABEL)
            if save_call:
                self.call_stack.append([self.at_label, self.pc + 2])
            self.at_label = label
            self.pc = 0
            self.__skip_pc_increment=True
        else:
            # TODO: do nothing.
            pass

    def perf_jne(self, args):
        self.__perform_conditional_jump(not self.equal_state, args[0])
        
    def perf_je(self, args):
        self.__perform_conditional_jump(self.equal_state, args[0])

    def perf_cne(self, args):
        self.__perform_conditional_jump(not self.equal_state, args[0], save_call=True)

    def perf_ce(self, args):
        self.__perform_conditional_jump(self.equal_state, args[0], save_call=True)
    
    def perf_call(self, args):
        self.__perform_conditional_jump(True, args[0], save_call=True)

    def perf_jump(self, args):
        # jump the target
        self.__perform_conditional_jump(True, args[0])

    def perf_retn(self, args):
        # FIXME: when multiple returns are called, the stack can be empty
        # anc crash the whole program execution.
        lastc = self.call_stack.pop()
        self.at_label   = lastc[0]
        self.pc         = lastc[1]
        self.__skip_pc_increment=True

    def perf_inc(self, args):
        inc_what = args[0]
        inc_value = self.__get_value_quick(inc_what)
        self.__set_value_quick(inc_what, inc_value + 1)
    
    def perf_dec(self, args):
        dec_what = args[0]
        dec_value = self.__get_value_quick(dec_what)
        self.__set_value_quick(dec_what, dec_value - 1)
    
    def perf_data(self, args):
        # insert data in the stack.
        vname = args[0]
        value = args[1]
        value = self.__get_value_quick(value)
        # set the value.
        self.vars[vname]=value
    
    def perf_move(self, args):
        # move the target
        source = args[0]
        target = args[1]

        source=self.__get_value_quick(source)
        self.__set_value_quick(target, source)
    

    def step(self):
        """
        Step will run your code until it reaches the end of a label.
        """
        # If there no code to run anymore, set running to false
        #print(self.vars)
        if not self.running:
            return self.running
        
        if self.pc + 1 > len(self.code[self.at_label]['code']): 
            self.running = False
            return self.running

        # If the code hasn't reached the end of the label, then keep executing.
        opcode = self.code[self.at_label]['code'][self.pc]
        index_o= self.op_dict.get(opcode)
        if index_o:
            args   = self.code[self.at_label]['code'][(self.pc+1):(self.pc+1)+(index_o[0])]
            invoke = index_o[1]
            if callable(invoke):
                invoke(args)
            # NOTE: case the opcode has request to skip the PC incrementation phase.
            if self.__skip_pc_increment:    self.__skip_pc_increment = False
            else:                           self.pc += (1 + index_o[0])
        else:
            return self.error("invalid opcode %s." % opcode, ERR_UNKNOWN_INSTRUCTION)
        return True

    def set_label(self, label):
        self.at_label = label
        self.pc = 0
    
    def new_label(self, name, code):
        """
        NOTE: the code should be already flatten and parsed!
        """
        self.code[name] = {'code': code}

def load_file(fname: str) -> interpreter:
    """load a file and return in the interpreter."""
    # load the file and remove the un-needed '\n' etc.
    f = open(fname, 'r')
    lines = [ line.replace('\t',' ').replace('\n','') for line in f ]
    f.close()

    # 1° begin to load the files by tokenizing them.
    tokenized_buffer = tokenize(lines)
    
    # 2° organize the code in sections.
    organized_code = organize_code(tokenized_buffer)
    
    # 3° init the interpreter
    interpreter_instance=interpreter(organized_code)

    # return the instance to execute.
    return interpreter_instance

def __act_as_app():
    # import the libraries.
    import sys              # => for sys.argv
    import os               # => for filesystem stuff.
    assert len(sys.argv) >= 2, "nothing to do."
    assert os.path.isfile(sys.argv[1]), "invalid file."

    # begin the execution.
    loaded_file = load_file(sys.argv[1])
    loaded_file.output = sys.stdout
    loaded_file.set_var("SCRIPT_NAME", sys.argv[1])

    # keep the loop.
    try:
        while loaded_file.step():
            pass
    except:
        pass

    # check for errors.
    if loaded_file.error_code != 0:
        print("E: Intepreter finished with error... %s" % loaded_file.error_code)
        print("E: %s" % str(loaded_file.error_str))

# determine when run as APP or as library.
if __name__ == '__main__':  __act_as_app()
else:   print("Vela Project, %s" % VERSION_STR)