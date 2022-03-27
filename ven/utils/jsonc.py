"""
jsonc: Json but with a simple commentary parsing tool.
"""

import os, json
def jsonLoad(file):
    """ 
    JSONC: json with comments, since petquest has some demos,
    it need comments to explain some of json code, so, this
    function will remove the comments, line by line and parse
    it using the JSON library on python.
    """
    # NOTE: __strip will remove all the comments from the json line.
    # FIXME: this function may break with MULTILINE comments.
    def __Strip(string):
        char_index, string_length=0,len(string)-1
        inside_comment, acc=False,""
        while char_index <= string_length:
            char        = (string[char_index])
            next_char   = (string[char_index] if char_index + 1 <= string_length else ' ')
            if      char == '/' and next_char == '*':   inside_comment = True        ; char_index += 1
            elif    char == '*' and next_char == '/':   inside_comment = False       ; char_index += 2
            if      char == '/' and next_char == '/':   break
            if      not inside_comment: acc += string[char_index]    ; char_index += 1
            else    : char_index +=1
        return acc
    def __flat(lines):
        """ flat is just a quick function to... flat array into strings. """
        acc = ""
        for line in lines: 
            acc += line
        return acc
    # test if file works.
    if not os.path.isfile(file):
        return None
    file_pointer = open(file,'r')    ; to_decode = file_pointer.readlines()
    file_pointer.close()             ; decoded = [ __Strip(Line) for Line in to_decode ]
    # NOTE: this function can crash at here.
    return json.JSONDecoder().decode(__flat(decoded))