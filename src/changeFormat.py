import re

def formatting(code: str) -> str:
    # ��ȡSPDX��
    spdx_line_match = re.search(r'//SPDX-License-Identifier:.*?\n', code)

    # �������SPDX��
    if spdx_line_match:
        spdx_line = spdx_line_match.group(0)
    else:
        spdx_line = ""

    # �Ƴ�SPDX��
    code_without_spdx = re.sub(r'//SPDX-License-Identifier:.*?\n', '', code)

    # ȥ�������еĶ���հ�
    cleaned_code = re.sub(r'[ \t]+', ' ', code_without_spdx)  # �滻����ո���Ʊ��Ϊһ���ո�
    cleaned_code = re.sub(r'\n+', ' ', cleaned_code)  # �滻������з�Ϊ�ո�
    cleaned_code = cleaned_code.strip()  # ȥ����β�հ�

    # ������õ�SPDX�з��ڴ���ĵ�һ�У���ȷ�������пո�
    if spdx_line:
        cleaned_code = f"{spdx_line}{cleaned_code}"

    return cleaned_code