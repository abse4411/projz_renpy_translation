import logging
from typing import List

from config.config import default_config
from trans.base import translator
from util.misc import strip_tags, var_list, strip_breaks


class default_template(translator):
    def __init__(self, trans_impl:translator):
        self._trans_impl = trans_impl
        self.last_output_text = None

    def translate(self, raw_text:str):
        raw_line = raw_text
        if default_config.remove_tags:
            line = strip_tags(raw_text)
        else:
            line = raw_text
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

    def translate_batch(self, raw_texts:List[str]):
        vars_list, tmp_texts = [], []
        res = [t for t in raw_texts]

        # preparing
        should_strip_tags = default_config.remove_tags
        for i, t in enumerate(raw_texts):
            if t.strip() == '':
                logging.warning(f'Skip empty text: [{t}]')
                continue
            tmp_t = t
            if should_strip_tags:
                tmp_t = strip_tags(tmp_t)
            renpy_vars = var_list(tmp_t)
            tmp_vars = [f'T{i}' for i in range(len(renpy_vars))]
            for j in range(len(renpy_vars)):
                tmp_t = tmp_t.replace(renpy_vars[j], tmp_vars[j])
            vars_list.append((i, renpy_vars, tmp_vars))
            tmp_texts.append(tmp_t)
        # translating
        new_texts = self._trans_impl.translate(tmp_texts)
        assert len(new_texts) == len(tmp_texts), f'The size of text list is inconsistent after translating (before: {len(tmp_texts)}, after: {len(new_texts)})'
        for (i, raw_vars, tmp_vars), tmp_text, new_text in zip(vars_list, tmp_texts, new_texts):
            if new_text is None or new_text.strip() == '':
                res[i] = None
                logging.warning(f'Skip empty translated text: [{new_text}] with raw text: [{raw_texts[i]}]')
            # replacing vars
            done = True
            for rv, tv in zip(raw_vars, tmp_vars):
                tot_cnt = tmp_text.count(tv)
                found_cnt = new_text.count(tv)
                if tot_cnt != found_cnt:
                    logging.warning(f'Skip empty corrupted text: [{new_text}] for losing RenPy variables (total: {tot_cnt}, found:{found_cnt})')
                    done = False
                    break
                new_text = new_text.replace(tv, rv)
            if not done:
                res[i] = None
        return res

    def close(self):
        self._trans_impl.close()
