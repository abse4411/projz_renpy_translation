import glob
import  os.path as osp

from util.file import mkdir, file_name

old_dir = r'./old'
output_new = r'./old_tmp'
mkdir(old_dir)
mkdir(output_new)
old_rpy_files = sorted(glob.glob(osp.join(old_dir, "*.rpy")))

for i, rpy_file in enumerate(old_rpy_files):
    print(f'current file: {i + 1}/{len(old_rpy_files)}：{rpy_file}')
    with open(rpy_file, 'r', encoding='utf-8') as f:
        temp_data = f.readlines()
    with open(osp.join(output_new, file_name(rpy_file)), 'w', encoding='utf-8', newline='\r\n') as f:
        for i, line in enumerate(temp_data, 1):
            update_text = line
            text = line.strip()
            if text:
                first_quote = text.find("\"")
                last_quote = text.rfind("\"")
                if first_quote != -1 and first_quote == last_quote:
                    old_pos = text.find("old ")
                    shape_pos = text.find("# ")
                    if (old_pos != -1 and old_pos < first_quote) or (shape_pos != -1 and shape_pos < first_quote):
                        break_pos = line.rfind('\r')
                        if break_pos == -1:
                            break_pos = line.rfind('\n')
                        update_text = line[:break_pos] + " \"" + line[break_pos:]
            f.write(update_text)