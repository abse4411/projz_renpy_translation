import logging

from trans.base import translator
from util.misc import strip_tags, var_list, strip_breaks


class default_template(translator):
    def __init__(self, trans_impl:translator):
        self._trans_impl = trans_impl
        self.last_output_text = None

    def translate(self, rawtext):
        raw_line = rawtext
        line = strip_tags(rawtext)
        renpy_vars = var_list(line)
        # replace the var by another name
        tvar_list = [f'T{i}' for i in range(len(renpy_vars))]
        t_line = line
        for i in range(len(tvar_list)):
            t_line = t_line.replace(renpy_vars[i], tvar_list[i])
        new_text = self._trans_impl.translate(t_line)
        if new_text is None or new_text.strip() == '':
            logging.warning(f'Error in translating [{raw_line}], it will ignored!')
            return None
        if new_text == self.last_output_text:
            logging.warning(
                f'Error in translating [{raw_line}] (The translated text ({new_text}) is the same as the last translated text), it will ignored!')
            return None
        self.last_output_text = new_text
        new_text = strip_breaks(new_text)
        # convert the var back
        for i in range(len(tvar_list)):
            new_text = new_text.replace(tvar_list[i], renpy_vars[i])

        return new_text

    def close(self):
        self._trans_impl.close()
