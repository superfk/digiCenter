import csv
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

    df.to_excel('{}.xlsx'.format(lang), encoding='utf-8', index=True)

def writeAllToJson(lang_all_path):
    df = pd.read_excel(lang_all_path,engine='openpyxl', index_col=[0])
    print(df)
    df = df.set_index('name')
    print(df)
    lang_names = list(df)
    print(lang_names)
    for ln in lang_names:
        print(df[ln])
        jfile = '{}.json'.format(ln)
        df[ln].to_json(jfile,orient='index',indent=2)


if __name__ == '__main__':
    langset = ['en','de','zh_tw']
    # writeSingleToExcel('de')
    writeAllToJson('all.xlsx')