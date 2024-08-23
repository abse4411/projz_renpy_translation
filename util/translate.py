from typing import List

import tqdm

from config.base import ProjzConfig
from trans import Translator


class BatchTranslator(Translator):
    def __init__(self, translator: Translator, batch_separator:str, batch_max_textlen:int, batch_size:int, show_bar: bool = True):
        self._translator = translator
        self._show_bar = show_bar
        self._separator = batch_separator
        self._max_len = batch_max_textlen
        self.batch_size = batch_size
        assert self.batch_size > 0, f'batch_size: {self.batch_size} should >0!'
        self._separator = self._separator.strip()
        assert self._separator != '', f'separator should not be empty!'
        print(f'Using BatchTranslator with batch_size: {self.batch_size}, separator: {self._separator}, max text len: {self._max_len}')

    def translate(self, text: str) -> str:
        return self._translator.translate(text)

    class _tqdm_proxy:
        def __init__(self, total: int = None, desc: str = None):
            if total is not None:
                self._bar = tqdm.tqdm(total=total, desc=desc)
            else:
                self._bar = None

        def __enter__(self):
            if self._bar is not None:
                return self._bar
            return self

        def update(self, n):
            if self._bar is not None:
                self._bar.update(n)

        def __exit__(self, exc_type, exc_val, exc_tb):
            if self._bar is not None:
                self._bar.close()

    def translate_batch(self, texts: List[str]) -> List[str]:
        new_texts = []
        with BatchTranslator._tqdm_proxy(total=len(texts) if self._show_bar else None, desc='Translating...') as bar:
            for i in range(0, len(texts), self.batch_size):
                batch_text = texts[i:min(len(texts), i + self.batch_size)]
                final_text = f'\n\n {self._separator} \n\n'.join(batch_text)
                # if reaching the limit of max text len
                if len(final_text) > self._max_len:
                    new_texts.extend(self._translator.translate_batch(batch_text))
                    bar.update(len(batch_text))
                    continue
                res = self.translate(final_text)
                new_batch_text = res.split(self._separator)
                # if we cannot split it with its size equaling original one
                if len(new_batch_text) != len(batch_text):
                    new_texts.extend(self._translator.translate_batch(batch_text))
                    bar.update(len(batch_text))
                    continue
                new_batch_text = [j.strip() for j in new_batch_text]
                new_texts.extend(new_batch_text)
                bar.update(len(batch_text))
            return new_texts
