import re

def obfuscate(source_code: str) -> str:
    # 注释的正则表达式
    single_line_pattern = r'//(.)*(\n)?'
    multi_line_pattern = r'/\*((.)|((\r)?\n))*?\*/'

    # 去除单行注释
    source_code_no_single_line_comments = re.sub(single_line_pattern, '', source_code, flags=re.MULTILINE)

    # 进一步去除多行注释
    source_code_no_comments = re.sub(multi_line_pattern, '', source_code_no_single_line_comments, flags=re.DOTALL)

    return source_code_no_comments.strip()