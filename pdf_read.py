# Copyright (c) OpenMMLab. All rights reserved.
import hashlib
import os

import pymupdf as fitz
import pandas as pd
# import textract
from bs4 import BeautifulSoup
from loguru import logger

class FileOperation:
    """Encapsulate all file reading operations."""

    def __init__(self):
        self.image_suffix = ['.jpg', '.jpeg', '.png', '.bmp']
        self.md_suffix = '.md'
        self.text_suffix = ['.txt', '.text']
        self.excel_suffix = ['.xlsx', '.xls', '.csv']
        self.pdf_suffix = '.pdf'
        self.ppt_suffix = '.pptx'
        self.html_suffix = ['.html', '.htm', '.shtml', '.xhtml']
        self.word_suffix = ['.docx', '.doc']
        self.normal_suffix = [self.md_suffix
                              ] + self.text_suffix + self.excel_suffix + [
                                  self.pdf_suffix
                              ] + self.word_suffix + [self.ppt_suffix
                                                      ] + self.html_suffix

    def get_type(self, filepath: str):
        filepath = filepath.lower()
        if filepath.endswith(self.pdf_suffix):
            return 'pdf'

        if filepath.endswith(self.md_suffix):
            return 'md'

        if filepath.endswith(self.ppt_suffix):
            return 'ppt'

        for suffix in self.image_suffix:
            if filepath.endswith(suffix):
                return 'image'

        for suffix in self.text_suffix:
            if filepath.endswith(suffix):
                return 'text'

        for suffix in self.word_suffix:
            if filepath.endswith(suffix):
                return 'word'

        for suffix in self.excel_suffix:
            if filepath.endswith(suffix):
                return 'excel'

        for suffix in self.html_suffix:
            if filepath.endswith(suffix):
                return 'html'
        return None

    def md5(self, filepath: str):
        hash_object = hashlib.sha256()
        with open(filepath, 'rb') as file:
            chunk_size = 8192
            while chunk := file.read(chunk_size):
                hash_object.update(chunk)

        return hash_object.hexdigest()[0:8]

    def summarize(self, files: list):
        success = 0
        skip = 0
        failed = 0

        for file in files:
            if file.state:
                success += 1
            elif file.reason == 'skip':
                skip += 1
            else:
                logger.info('{} {}'.format(file.origin, file.reason))
                failed += 1

            logger.info('{} {}'.format(file.reason, file.copypath))
        logger.info('累计{}文件，成功{}个，跳过{}个，异常{}个'.format(len(files), success,
                                                      skip, failed))

    def scan_dir(self, repo_dir: str):
        files = []
        for root, _, filenames in os.walk(repo_dir):
            for filename in filenames:
                _type = self.get_type(filename)
                if _type is not None:
                    files.append(
                        FileName(root=root, filename=filename, _type=_type))
        return files

    def read_pdf(self, filepath: str):
        # load pdf and serialize table

        text = ''
        with fitz.open(filepath) as pages:
            for page in pages:
                text += page.get_text()
                tables = page.find_tables()
                for table in tables:
                    tablename = '_'.join(
                        filter(lambda x: x is not None and 'Col' not in x,
                               table.header.names))
                    pan = table.to_pandas()
                    json_text = pan.dropna(axis=1).to_json(force_ascii=False)
                    text += tablename
                    text += '\n'
                    text += json_text
                    text += '\n'
        return text

    def read_excel(self, filepath: str):
        table = None
        if filepath.endswith('.csv'):
            table = pd.read_csv(filepath)
        else:
            table = pd.read_excel(filepath)
        if table is None:
            return ''
        json_text = table.dropna(axis=1).to_json(force_ascii=False)
        return json_text

    def read(self, filepath: str):
        file_type = self.get_type(filepath)

        text = ''

        if not os.path.exists(filepath):
            return text, None

        try:

            if file_type == 'md' or file_type == 'text':
                with open(filepath) as f:
                    text = f.read()

            elif file_type == 'pdf':
                text += self.read_pdf(filepath)

            elif file_type == 'excel':
                text += self.read_excel(filepath)

            elif file_type == 'word' or file_type == 'ppt':
                # https://stackoverflow.com/questions/36001482/read-doc-file-with-python
                # https://textract.readthedocs.io/en/latest/installation.html
                text = textract.process(filepath).decode('utf8')
                if file_type == 'ppt':
                    text = text.replace('\n', ' ')

            elif file_type == 'html':
                with open(filepath) as f:
                    soup = BeautifulSoup(f.read(), 'html.parser')
                    text += soup.text

        except Exception as e:
            logger.error((filepath, str(e)))
            return '', e
        text = text.replace('\n\n', '\n')
        text = text.replace('\n\n', '\n')
        text = text.replace('\n\n', '\n')
        text = text.replace('  ', ' ')
        text = text.replace('  ', ' ')
        text = text.replace('  ', ' ')
        return text, None

# file_opr = FileOperation()
# text, error = file_opr.read('/root/huixiangdou/data_/事故报告文本版定.pdf')
# print(len(text))
# print(text[:100])