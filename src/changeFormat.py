import re

def formatting(code: str) -> str:
    # 提取SPDX行
    spdx_line_match = re.search(r'//SPDX-License-Identifier:.*?\n', code)

    # 如果包含SPDX行
    if spdx_line_match:
        spdx_line = spdx_line_match.group(0)
    else:
        spdx_line = ""

    # 移除SPDX行
    code_without_spdx = re.sub(r'//SPDX-License-Identifier:.*?\n', '', code)

    # 去掉代码中的多余空白
    cleaned_code = re.sub(r'[ \t]+', ' ', code_without_spdx)  # 替换多个空格和制表符为一个空格
    cleaned_code = re.sub(r'\n+', ' ', cleaned_code)  # 替换多个换行符为空格
    cleaned_code = cleaned_code.strip()  # 去掉首尾空白

    # 将处理好的SPDX行放在代码的第一行，并确保后面有空格
    if spdx_line:
        cleaned_code = f"{spdx_line}{cleaned_code}"

    return cleaned_code