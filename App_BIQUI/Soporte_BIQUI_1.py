import pandas as pd
import regex as re
from requests_html import HTMLSession
from bs4 import BeautifulSoup
import numpy as np
import time
import json
import scrapy
import os
# To run

#--------------------------------------------------------------
# PARAMETERS

# Filepath location
filepath_load= r'{}\App_BIQUI\Excel_Secundario_BIQUI.xlsx'.format(os.getcwd())
filepath_save= r'{}\App_BIQUI\Excel_Secundario_BIQUI.xlsx'.format(os.getcwd())
filepath_data = r'{}\App_BIQUI\Chat_Data.txt'.format(os.getcwd())


# Patterns
date_pattern = '\d+[/]\d+[/]\d+'
link_pattern = 'http\w+\S+\w+'
website_pattern = "http\w+\W+\w+[.]\w+[.]\w+\W+\w+"
job_pattern = 'usca'

# Import parameters
new_file = True
limit_imports=5
waiting_time = 5
Pages_extra_links=3


# List of attributes and classes
web_list = [('https://www.linkedin.com/posts', "p","class", "share-update-card__update-text"),
            ('https://www.linkedin.com/jobs', "div","class", "show-more-less-html__markup show-more-less-html__markup--clamp-after-5"),
            ('https://candidato.computrabajo.com.ar', "section","class", "boxWhite fl w_100 detail_of mb20 bWord"),
            ('https://www.computrabajo.com.ar', "section","class", "boxWhite fl w_100 detail_of mb20 bWord"),
            ('https://www.zonajobs.com.ar', "div","class", "aviso_description"),
            ('https://www.empleos.clarin.com', "div","class", "col-md-8 col-sm-12 col-xs-12"),
            ('https://www.randstad.com.ar',"div","id","js_description"),
            ('https://mpar.csod.com/ux',"script","type","application/ld+json"),
            ('https://www.opcionempleo.com.ar',"script","type","application/ld+json"),
            ('https://neuvoo.com.ar/view',"div","class","view-job-description"),
            ('https://ar.jobrapido.com/jobpreview', "div","class", "jpp-advert__description")]


web_dic = {}
prop_list=['attr','key','key_val']
for web, attr,key,key_val in web_list:
    web_dic[web] = {prop_list[0]: attr, prop_list[1]: key , prop_list[2]: key_val}

# Algorithm
'''- Get chat lines
    - Extract the jobs without link and with link
    - Get the link content using requests and beautiful soup
    - Store the data as Dataframe and save it in Excel file '''

#--------------------------------------------------------------------------------------
# ALGORITHM

# Extract lines from chat: takes every line in the Chat txt file and splits in a list of sentences
def get_chat_lines(filename2):
    file = open(filename2, 'r', encoding='utf-8')
    chat = file.read()
    content = chat.splitlines()
    return content

# Extract chat content wihout link

def get_jobs_without_link(chat_lines):
        content=chat_lines.copy()
        index=0
        jobs_without_link=[]
        while index < len(content):
            founded=re.findall(date_pattern,content[index])
            root=index-1
            while len(founded)==0:
                content[root]=content[root]+' '+content[index]
                content.remove(content[index])
                founded=re.findall(date_pattern, content[index])
                if len(founded) > 0:
                    index=index-1
                    jobs_without_link.append(content[root])
            index=index+1

        jobs_without_link = [files for files in jobs_without_link if
                             (re.findall(job_pattern, files) != [] and re.findall(link_pattern, files) == [])]
        return jobs_without_link
comput_corr = lambda x: x.replace('/Candidate/', '/').replace('candidato','www') if x.find('candidato.computrabajo')>0 else x

# Extract chat data based on web pattern
def get_jobs_with_link(content):
        # Jobs with link
        jobs_l=[re.findall(link_pattern,files)[0] for files in content if re.findall(link_pattern,files)!=[]]
        jobs_with_link=pd.Series(jobs_l).drop_duplicates().reset_index(drop=True).apply(comput_corr)
        return jobs_with_link


rand_page= lambda n:np.random.randint(1,2*n,n).tolist()
rand_links= lambda x:np.random.permutation(x)[:(len (x) // 2)]


# Extract links from websites
def get_soup(url):
    time.sleep(waiting_time)
    session = HTMLSession()
    html_doc = session.get(url).text
    soup = BeautifulSoup(html_doc, 'html.parser')
    return soup
def opcionempleo_linkextractor(idx_pages=[1,2,3]):
    base_url='https://www.opcionempleo.com.ar'
    menu_url='/empleo-quimico.html?radius=0&p='
    web_list=[]

    print('Extrayendo enlaces de Opcionempleo...')
    for page in idx_pages:
        try:
            soup=get_soup(base_url+menu_url+str(page))
            webs=scrapy.Selector(text=soup.decode()).xpath('//header/h2/a/@href').extract()
            web_list+=webs
        except:
            pass
    web_list=[base_url+w for w in web_list]
    return web_list
def nuevoo_linkextractor(idx_pages=[1,2,3]):
    base_url = 'https://neuvoo.com.ar'
    menu_url = lambda x:'/trabajos/?k=quimic&l=&p='+str(x)+'&date=&field=&company=&source_type=&radius=&from=&test=&iam=&is_category=no'
    start_link,end_link = '/view/?','&action=emailAlert'
    web_list = []

    print('Extrayendo enlaces de Neuvoo...')
    for page in idx_pages:
        try:
            soup = get_soup(base_url + menu_url(page))
            webs = soup.find_all('a',{'class':"card__job-link gojob"})
            webs = [t.attrs['href'] for t in webs]
            web_list+= webs

        except:
            pass
    web_list= [ base_url+ start_link + t[10:].replace('&amp;', '&').replace('ss', 'splitab') + end_link  for t in web_list]
    return web_list

# Get extracting parameters
def get_scrapping_params(list_links):
    to_website=lambda x: re.findall(website_pattern, x)[0] if re.findall(website_pattern, x) !=[] else x
    web_prop = lambda x, y: [v[y] for k, v in web_dic.items() if re.findall(k, x) != []]

    w_df=pd.DataFrame(list_links,columns=['links'])
    w_df['website']=w_df['links'].apply(to_website)
    for prop in prop_list:
        w_df[prop]=w_df.website.apply(lambda x: web_prop(x,prop)[0] if web_prop(x,prop)!=[] else None)

    return w_df
def max_spacing_sort(w_df):
    web_serie=w_df.website
    counting=web_serie.value_counts()
    min_spacing= counting.sum() // counting[0]

    empty_df=pd.DataFrame(['empty'] *counting.sum(), columns=['links'])
    idx_df=empty_df.copy()
    pos=0
    for webs_idx in range(len(counting)):
        while empty_df.iloc[pos,0]!='empty':
            pos+=1

        links=web_serie[web_serie==counting.index[webs_idx]]
        links = links[np.random.permutation(links.index)]
        links_res=links.reset_index(drop=True)

        for n_link in range(len(links_res)):
            empty_df.iloc[pos+min_spacing*n_link,0]=links_res[n_link]
            idx_df.iloc[pos + min_spacing * n_link, 0] = links.index[n_link]
        pos=0
    w_df=w_df.iloc[idx_df['links'].tolist(),:]
    w_df.reset_index(drop=True,inplace=True)
    return w_df


# Extract content
def opcionempleo_scrapper(res_HTML):
    try:
        content = json.loads(res_HTML.contents[0])['description']
        try:
            content=' '.join(content.splitlines())
        except:
            pass
    except:
        pass
    return content
def nuevoo_scrapper(res_HTML):
    try:
        content = res_HTML.text
        content = ' '.join(content.splitlines())
    except:
        pass
    return content
def manpower_scrapper(res_HTML):
    try:
        dict_content = json.loads(res_HTML.contents[0])
        content_unfiltered = scrapy.Selector(text=dict_content['Description']).xpath('/html/body/p/text()').extract()
        content = ' '.join(' '.join(content_unfiltered).splitlines())
    except:
        pass
    return content
def get_content(df):
    job_desc = {}
    for row in range(df.shape[0]):
        if df.loc[row,'attr'] is not None:
            webs=df.loc[row,'website']
            url= df.loc[row,'links']
            soup = get_soup(url)
            try:
                content_HTML = soup.find(web_dic[webs]['attr'], {web_dic[webs]['key']: web_dic[webs]['key_val']})

                if url.find('mpar.') != -1:
                    job_content=manpower_scrapper(content_HTML)
                elif url.find('nuevoo') != -1:
                    job_content=nuevoo_scrapper(content_HTML)
                elif url.find('opcionempleo') != -1:
                    job_content = opcionempleo_scrapper(content_HTML)
                else:
                    job_content = content_HTML.text
            except:
                job_content = 'Blocked'

            job_desc[row] = {'content': job_content, 'url': url, 'website': webs}


        print('Faltan ', df.shape[0] - row,' enlaces para terminar')
    return job_desc



# Add to existing dataframe
def jobs_to_df(content_jobs_with_link, jobs_without_link):
    # Convert to Dataframe
    df = pd.DataFrame(content_jobs_with_link).transpose()
    df['content'] = df.content.str.replace(pat='\s+', repl=' ')
    df_wout_links = pd.DataFrame(jobs_without_link, columns=['content'])
    df_mod_wout_links = df_wout_links.content.str.replace(pat=date_pattern + '\W+\d+' * 7 + '\W+', repl=' ')
    final_df = pd.merge(df,df_mod_wout_links,how='outer').reset_index(drop=True).fillna(np.nan)

    return final_df


# Correct modified database
def reverse_correction(jobs_df):
    if len(jobs_df.columns)>3:
        jobs_df.drop(list(jobs_df.columns)[3:],axis=1,inplace=True)
        jobs_df.iloc[:, 1] = jobs_df.iloc[:, 1].apply(lambda x: np.nan if x=='No tiene link' or x==0 else x)
        jobs_df.iloc[:, 2] = jobs_df.iloc[:, 2].apply(lambda x: np.nan if x=='No tiene link' or x==0 else x)
        return jobs_df

# revert max_space_sort back to date-based sorting
def invert_sorting(jobs_df,total_urls):
    total_urls_mod=total_urls.to_list()
    print(total_urls)
    print(jobs_df.head())
    jobs_df['old_index'] = jobs_df.url.apply(lambda x: jobs_df.shape[0] if pd.isna(x) else jobs_df.index[jobs_df.url == x] if x not in total_urls_mod else total_urls_mod.index(x))
    jobs_df.sort_values(by='old_index',inplace=True)
    jobs_df.drop('old_index',axis=1,inplace=True)
    return jobs_df

#---------------------------------------

# Read old file to append
jobs_df = pd.read_excel(filepath_load, index_col=0)

# Update if new file=True
def update_jobs(jobs_df,filepath_data,filepath_save,limit_imports):
    # Correct dataframe
    jobs_df = reverse_correction(jobs_df)

    # Get chat lines
    chat_lines = get_chat_lines(filepath_data)

    # Get the urls in the file and ones already loaded
    total_urls=get_jobs_with_link(chat_lines)
    current_urls=jobs_df[jobs_df.url.notna()].url

    # Get other urls from search engines
    opcionempleo_links = opcionempleo_linkextractor(rand_page(Pages_extra_links))
    nuevoo_links = nuevoo_linkextractor(rand_page(Pages_extra_links))

    # Filter duplicates
    complete_urls_list=total_urls.to_list()+opcionempleo_links+nuevoo_links
    urls_to_update = [urls for urls in complete_urls_list if urls not in current_urls.values]

    # Get parameters to scrap
    update_df=get_scrapping_params(urls_to_update)
    update_df=max_spacing_sort(update_df).iloc[:limit_imports,:]

    # Get the posting job description
    content_jobs_with_link=get_content(update_df)

    # Get the posting job description for jobs without link
    new_posts=pd.Series(get_jobs_without_link(chat_lines)).str.replace(pat=date_pattern + '\W+\d+' * 7 + '\W+', repl=' ')
    post_list=jobs_df[jobs_df.url.isna()].reset_index(drop=True).content
    posts_to_update=[post for post in new_posts if post not in post_list]

    # Add to database
    jobs_to_append=jobs_to_df(content_jobs_with_link,posts_to_update)

    jobs_df=jobs_df.append(jobs_to_append).reset_index(drop=True)

    # Sort by date and save
    jobs_df=invert_sorting(jobs_df,total_urls)
    jobs_df.to_excel(filepath_save)
    return jobs_df


#----------------------------------------