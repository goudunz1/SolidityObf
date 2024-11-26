import re

def obfuscate(source_code: str) -> str:
    # ע�͵�������ʽ
    single_line_pattern = r'//(.)*(\n)?'
    multi_line_pattern = r'/\*((.)|((\r)?\n))*?\*/'

    # ȥ������ע��
    source_code_no_single_line_comments = re.sub(single_line_pattern, '', source_code, flags=re.MULTILINE)

    # ��һ��ȥ������ע��
    source_code_no_comments = re.sub(multi_line_pattern, '', source_code_no_single_line_comments, flags=re.DOTALL)

    return source_code_no_comments.strip()