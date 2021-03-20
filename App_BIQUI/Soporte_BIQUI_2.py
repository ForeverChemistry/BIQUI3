import pandas as pd
import regex as re
import numpy as np
import spacy
from nltk import SnowballStemmer
from sklearn.feature_extraction.text import TfidfVectorizer
import os

# To run
'%run My_projects/IQ_project2'

#--------------------------------------------------------------
# PARAMETERS

# Filepath location
filepath_load=r'{}\App_BIQUI\Excel_Secundario_BIQUI.xlsx'.format(os.getcwd())
filepath_save=r'{}\App_BIQUI\Excel_Principal_BIQUI.xlsx'.format(os.getcwd())


# Saving parameters
save_file=True
jobs_df=pd.read_excel(filepath_load,index_col=0)


# Get Dataframe
jobs_df['content']=jobs_df.content.fillna('')
jobs_df.reset_index(drop=True,inplace=True)
processed_jobs= jobs_df.content


#----------------------------------------------------------------------------------
# Look for specific words to build categories


# Search list
Skill_dict={'Office':[' pc',' office',' excel ',' word',' planillas de calculo'],
           'Idiomas': ['ingles','english','aleman','portugues'],
           'ISO_otros':[' iso ',' ohsas',' 5s '],
           'BMP_leg':['bmp ','bpm ','gmp ',' legal'],
           'Other cert':['tpm ',' lean ','iatf',' chas ',' plp','pmp '],
           'SAP':[' sap ','base de datos'],
           'Cromat_Espectr':['hplc',' espectro',' cromatog',' gc ','shimadzu'],
           'Licencias_Matr':['licencia ','carnet ',' matricula','movilidad','vehiculo propio',' de conducir'],
           'HYSYS_otros':['simulac','hysys','matlab','dwsim','aspen','chemcad'],
           'CAD_otros':['cad ','autocad','solidworks','3d ','planos']}

Professions_dict={'Postgrado':['postgrado','postitulo','especializacion','doctor','maestria',' mba'],
                'IngQ':[' inge',' ing. ',' ing '],
                'Lic_BQ_IngAl':['bioq','biotec',' lic.',' lic ',' licenciad',' licenciatura','farmacia'],
                  'Tecnico':['tecnic','tecnicat'],
                  'Operario':['operario','operaria','operador','secundari'],
                  }
Area_dict={'Calidad':['calidad'],'Produccion':['produccion']}
Position_dict={'Control_calidad':['formulas','tecnico de laboratorio','ayudante de laboratorio','asistente de laboratorio','control de calidad','fisicoqu','fisico qu','prueba',' muestras ',' ensayo',' test','hplc','validacion','cromatog'],
                'Aseg_calidad':['asegura[\w+\W]{,15}calidad','sistema de gestion',' iso ','ohsas','hazop','auditoria','no conformidades'],
               'Operario_prod':['opera[\w+\W]{,15}produccion','operari','operador','secundario completo','elevador','maquina','efluentes'],
               'Supervisor':['lider de','coordinado','supervis','jefe'],
               'Otras':['asesor','consultor','venta','visit[\w+\W]{,15}clientes']}

Excluded_words=['clinicos','hisopad','alimentos']
Excluded_list=Excluded_words+Skill_dict['Licencias_Matr']+Skill_dict['Cromat_Espectr']+Skill_dict['CAD_otros']+Skill_dict['SAP']+Professions_dict['Lic_BQ_IngAl']+Professions_dict[ 'Operario']

Ss_list=[['manej[\w+\W]{,10} personal'],
['comunicacion'],
['resol[\w+\W]{,15} problemas','resolutiv'],
['dinamic'],
['joven profesional'],
['interpersonales'],
['integridad','integra '],
['liderazgo'],
['flexibilidad','flexib[\w+\W]{,10} cambios','adapt[\w+\W]{,10} al cambio'],
['trabaj[\w+\W]{,10} en equipo'],
['autonom'],
['aten[\w+\W]{,7} al detalle'],
['toma de riesgo'],
['manejo de resultados','gestion de resultados'],
['perfil comercial','orienta[\w+\W]{,7} al cliente',],
['proactiv'],
['perseveran','iniciativa'],
['persona analitica','habilidad analitica'],
['gestion del tiempo','manejo del tiempo'],
['orienta[\w+\W]{,7} a resultados']]



dict_list=[Professions_dict,Area_dict,Position_dict,Skill_dict]
#---------------------------------------------------

# Preprocessing and find strings
def clean_string(jobs):
    index=0
    while index in range(len(jobs)):

        # Any symbol out (replace with whitespace)
        if not jobs[index].isascii() and (jobs[index] not in 'áéíóúñÁÉÍ'):
            jobs = jobs[:index] + ' ' + jobs[index + 1:]
            index = index + 1

        # After lower nothing but lower, a comma or a stop.
        if index > 0 and index < len(jobs) and jobs[index - 1].islower() and not (
                jobs[index].islower() or jobs[index].isspace() or jobs[index] in ',.'):
            if jobs[index].isupper():
                jobs = jobs[:index] + ', ' + jobs[index:]
                index = index + 2
            else:
                jobs = jobs[:index] + ',' + jobs[index + 1:]
        # If all uppercase but not acronym , make it lowercase            e
        if jobs[index:index + 4].isupper() and jobs[index:index + 7].isalpha():
            i = 7
            while jobs[index:index + i].isupper() and jobs[index:index + i].isalpha() and index + i < len(jobs):
                i = i + 1
            jobs = jobs[:index] + jobs[index:index + i - 1].lower() + jobs[index + i - 1:]
        # Before upper, anything but whitespace
        if index > 0 and index < len(jobs) and jobs[index].isupper() and not (
                jobs[index - 1].isspace() or jobs[index - 1].isupper() or jobs[index - 1] in ',.('):
            if jobs[index - 1] in '(,.' and index > 1:
                jobs = jobs[:index - 1] + ', ' + jobs[index:]
                index = index + 1
            else:
                jobs = jobs[:index - 1] + ',' + jobs[index:]
        index = index + 1

    # removing remaining not alpahanumeric characters and lowecasing
    more_cleaned_string = ''.join([a.lower() for a in jobs if (a.isalnum() or a.isspace())])
    for c1, c2 in list(zip(['á', 'é', 'í', 'ó', 'ú'], ['a', 'e', 'i', 'o', 'u'])):
        more_cleaned_string = more_cleaned_string.replace(c1, c2)

    return more_cleaned_string

# Finds any of the words in a list in
def finder_par (list_of_words, list_of_strings):
    index_dict = {}
    for index in range(0,len(list_of_strings)):
        word_dict = {}
        string = list_of_strings[index]
        cleaned_string = clean_string(string)

        find_word = lambda pat: re.findall(pat, cleaned_string)
        for word in list_of_words:
            founded_words=[]
            for pattern in ['\w+'+word+'\w+', word+'\w+','\w+'+word,word]:
                if find_word(pattern) !=[]:
                    for word in find_word(pattern):
                        if word not in founded_words:
                            founded_words.append(word)
            if founded_words !=[]:

                word_dict[word] = founded_words
        index_dict[index] = word_dict
    return index_dict

#
def finder_ser(list_of_words,serie_of_strings):
    serie_of_strings_copy=serie_of_strings.copy()
    for word in list_of_words:
        if type(word) is not list:
            word=[word]
        founded=finder_par(word,serie_of_strings_copy)
        list_idx=[idx for idx in founded if founded[idx]!={}]
        for idx in range(len(serie_of_strings_copy)):
            if idx not in list_idx:
                serie_of_strings_copy.iloc[idx]=''
    return founded


# Text processing
def content_simplifier(list_of_jobs):
    jobs_list = []
    # Get unknown words
    nlp = spacy.load('es_core_news_sm')
    spanish_stemmer = SnowballStemmer('spanish')
    for job in list_of_jobs:
        try:
            cleaned_job = clean_string(job)
            ent_job = nlp(cleaned_job)
            # Eliminate punctuations and stopwords (normalizing) ,pronouns (lemmatization) and short words
            lexical_tokens = [t.orth_ for t in ent_job if not (t.is_punct or t.is_stop or t.is_space)]
            lemmat_and_stem_words = [spanish_stemmer.stem(t) for t in lexical_tokens if (len(t) > 1 and t.isalpha())]
            job_string = ' '.join(lemmat_and_stem_words)
            jobs_list.append(job_string)
        except:
            pass
    return jobs_list
def top_soft_skills(ss_list,df,old_ss,cut=0.88):
    counter_func=lambda x:len([v for k,v in finder_par(x,df.reset_index(drop=True)).items() if v!={}])
    top_ss_labels = content_simplifier([t[0] for t in ss_list])
    new_ss=dict([(top_ss_labels[x],counter_func(ss_list[x])) for x in range(len(ss_list))])
    total_ss={k: new_ss[k] + old_ss[k] if (k in new_ss and k in old_ss) else v for k, v in {**new_ss, **old_ss}.items()}
    total_ss_list=[(v,k) for k,v in total_ss.items()]
    total_ss_list.sort(reverse=True)
    l1,l2=zip(*total_ss_list)
    acum,i=0,0
    while acum<cut:
        acum+=l1[i]/sum(l1)
        i+=1
    count_trimmed,label_trimmed=l1[:i],l2[:i]
    return label_trimmed


# Categorize jobs
def add_categories(jobs_df,list_of_dicts,list_of_ss):

    df_out=pd.read_excel(filepath_save,index_col=0)
    if df_out.iloc[-1, 0] == 'TOTAL_SUM':
        old_ss = df_out.tail(1).loc[:, 'proactiv':].to_dict('list')
        old_ss={k:v[0] for k,v in old_ss.items()}
        df_out.drop(df_out.tail(1).index[0], axis=0, inplace=True)


    old_jobs = df_out[df_out.content.isin(jobs_df.content)]
    new_jobs = jobs_df[~jobs_df.content.isin(df_out.content)]

    # Group based on string match
    for dictionary in list_of_dicts:
        for k, v in dictionary.items():
            jobs_df.loc[~jobs_df.content.isin(df_out.content),k] = jobs_df.loc[~jobs_df.content.isin(df_out.content),'content'].apply(lambda x: True if finder_par(v, [x])[0] != {} else False)

    top_ss = top_soft_skills(list_of_ss, new_jobs.content,old_ss=old_ss)
    new_ss=list(set(top_ss).difference(old_ss))
    if len(new_ss) != 20:
        for soft_skill in new_ss:
            df_out.loc[df_out.content.isin(jobs_df.content),soft_skill] = df_out.loc[df_out.content.isin(jobs_df.content),'content'].apply(lambda x: True if finder_par([soft_skill], [x])[0] != {} else False)

    for soft_skill in top_ss:
        jobs_df.loc[~jobs_df.content.isin(df_out.content),soft_skill] = jobs_df.loc[~jobs_df.content.isin(df_out.content),'content'].apply(lambda x: True if finder_par([soft_skill], [x])[0] != {} else False)

    jobs_df.iloc[:, 3:] = jobs_df.iloc[:, 3:].astype('boolean')
    jobs_df=old_jobs.append(jobs_df.loc[~jobs_df.content.isin(df_out.content),:]).fillna(0)
    totals = jobs_df.sum()
    sum_df = pd.DataFrame(totals, columns=[jobs_df.shape[0]]).transpose()
    sum_df['content'] = 'TOTAL_SUM'
    jobs_df=jobs_df.append(sum_df)
    jobs_df.reset_index(drop=True,inplace=True)
    return jobs_df



def transform_jobs_df(jobs_df,filepath_save,feat1=dict_list,feat2=Ss_list):
    jobs_df=add_categories(jobs_df,feat1,feat2)
    jobs_df.loc[np.logical_and(jobs_df.content.apply(len) < 120, jobs_df.content != 'Blocked'), 'content'] = 'Discard'
    jobs_df.iloc[-1,0]='TOTAL_SUM'
    jobs_df.to_excel(filepath_save)
    return jobs_df



str_len = 100
string_separator = lambda x: '\n'.join([x[str_len * j:str_len * (j + 1)] for j in range(len(x) % str_len) if str_len * j <= len(x)])

base_cv=r"C:\Users\lucia\Desktop\CVMatch.txt"



def cv_matcher(df,cv_filepath,Excluded_list,penalty=1):
    processed_jobs=df.content
    with open(cv_filepath,'r',encoding='utf8') as f:
        text_undiv=f.read()

        nlp = spacy.load('es_core_news_sm')
        sent_list=nlp(text_undiv).sents
        cv_text=[]
        for sent in sent_list:
            text_sent_list=sent.text.splitlines()
            cv_text=cv_text+text_sent_list


    jobs_list=content_simplifier(processed_jobs)
    simple_cv=content_simplifier(cv_text)
    keywords_counter = TfidfVectorizer(max_df=0.9,ngram_range=(1,3))
    cv_match=keywords_counter.fit_transform(simple_cv)
    total_cv=cv_match.sum(axis=0).transpose()
    jobs_incv=keywords_counter.transform(jobs_list)
    similarity=jobs_incv.dot(total_cv)
    similarity=[t[0] for t in similarity.tolist()]


    excluded=content_simplifier(Excluded_list)
    neg_keywords_counter=TfidfVectorizer(ngram_range=(1,3))
    cv_neg_match=neg_keywords_counter.fit(excluded)
    jobs_incv_neg=neg_keywords_counter.transform(jobs_list)
    jobs_incv_neg_total=jobs_incv_neg.sum(axis=1)
    asimilarity=[t[0] for t in jobs_incv_neg_total.tolist()]

    total_score=[t[0]-penalty*t[1] for t in zip(similarity,asimilarity)]
    coupled_scores=list(zip(total_score,list(processed_jobs.index)))
    coupled_scores.sort(reverse=True)
    sc,top_matches_idx=zip(*coupled_scores)
    return top_matches_idx,sc

def vocab_ranking(jobs_df):
    jobs_list=content_simplifier(jobs_df.content)
    keywords_counter = TfidfVectorizer(min_df=0.05,max_df=0.9)
    jobs_counter=keywords_counter.fit_transform(jobs_list)
    list_keywords = keywords_counter.get_feature_names()

    vocab_ranking=list(zip(jobs_counter.sum(axis=0).tolist()[0],list_keywords))
    vocab_ranking.sort(reverse=True)
    return(vocab_ranking)
