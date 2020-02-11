import csv, os
import json
import pandas as pd


def writeSingleToExcel(lang):
    with open('{}.json'.format(lang), encoding='utf-8-sig') as f_input:
        data = json.load(f_input)
        
        dataset = []
        head = ''
        for k,v in data.items():
            if not k == 'display_name':
                d={}
                d['name'] = k
                d['text'] = v
                dataset.append(d)
            else:
                head = v

        df = pd.DataFrame(dataset)
        df = df.rename(columns={'text': head})
        print(df)

    df.to_excel('{}.xlsx'.format(lang), encoding='utf-8-sig', index=True)

def writeAllToJson(source):
    df = pd.read_excel(source,engine='openpyxl', index_col=[0])
    print(df)
    df = df.set_index('name')
    print(df)
    lang_names = list(df)
    print(lang_names)
    for ln in lang_names:
        print(df[ln])
        jfile = '{}.json'.format(ln)
        with open(jfile, 'w', encoding='utf-8-sig') as file:
            df[ln].to_json(file, force_ascii=False, orient='index',indent=2)

def load_json_lang_from_xlsx(source, langID='en'):
    df = pd.read_excel(source,engine='openpyxl', index_col=[0])
    df = df.set_index('name')
    lang_names = list(df)
    data = None
    for ln in lang_names:
        if ln == langID:
            jfile = '{}.json'.format(ln)
            print('read lang file={}'.format(jfile))
            data = df[ln].to_json(force_ascii=False, orient='index',indent=2)
            break
    return data

def load_json_lang_from_json(lang_folder, langID='en'):
    path = os.path.join(lang_folder, langID+".json")
    with open(path, 'r', encoding='utf-8-sig') as f:
        data = json.load(f)
    return data

if __name__ == '__main__':
    langset = ['en','de','zh_tw']
    # writeSingleToExcel('de')
    writeAllToJson(source='all.xlsx')
    data = load_json_lang_from_json('','de')
    print(data)
    # data = load_json_lang_from_xlsx('all.xlsx', 'en')