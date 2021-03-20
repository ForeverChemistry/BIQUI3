import pandas as pd
import numpy as np
from App_BIQUI.Soporte_BIQUI_1 import update_jobs
from App_BIQUI.Soporte_BIQUI_2 import transform_jobs_df,cv_matcher,dict_list
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib import cm
import tkinter
from tkinter import messagebox
from PIL import ImageTk
from PIL import Image as ImagePIL
import webbrowser
import os
from tkinter import *

#:::::::::::::::::::::::::::::::::::::::::::::
# Para ejecutar en la consola de Python copiar la direccion absoluta (ABS ,en Pyccharm con click derecho sobre BIQUI.py aca arriba
# e ir a copiar direccion/direccion absoluta) y ejecutar en la consola "%run ABS" (sin las " y sin el .py)




#:::::::::::::::::::::::::::::::::::::::::::::::

#----------------------------------------------
# Load main dataframe
#jobs_df = pd.read_excel(filepath_load,index_col=0)
jobs_df=pd.DataFrame()

def correct_dataframe(jobs_df):
    jobs_df=jobs_df[np.logical_and(jobs_df.content!='Blocked',jobs_df.content!='Discard')].drop_duplicates().reset_index(drop=True).fillna(0)
    jobs_df.drop(jobs_df.tail(1).index[0], axis=0, inplace=True)
    jobs_df.iloc[:,3:]=jobs_df.iloc[:,3:].apply(lambda y: y.apply(lambda x: True if x==1 else False if x==0 else x))
    jobs_df.iloc[:,1]= jobs_df.iloc[:,1].apply(lambda x: 'No tiene link' if x==0 else x)
    jobs_df.iloc[:,2] = jobs_df.iloc[:, 2].apply(lambda x: 'No tiene link' if x ==0 else x)
    return jobs_df

#jobs_df=correct_dataframe(jobs_df)

#----------------------------------------------
# Create user interface

# Tkinter window
window=tkinter.Tk()
window_length,window_width=640,450
window.geometry(str(window_length)+'x'+str(window_width))
window.title('BIQUI - Busquedas para Ingenieria Quimica')

# Left frame
left_width=100
left_frame= tkinter.Frame(master=window,width=left_width,height=100,bg='white')
left_frame.pack(fill=tkinter.Y,side=tkinter.LEFT)

# Right frame
right_frame= tkinter.Frame(master=window,width=window_length,height=100,bg='#F8F9FA')
right_frame.pack(fill=tkinter.BOTH,side=tkinter.LEFT,expand=True)

biqui_dir=r'{}\App_BIQUI\BIQUI2.png'.format(os.getcwd())
new_image=ImagePIL.open(biqui_dir)
new_image=new_image.resize((new_image.size[0] //2 , new_image.size[1] //2 ))
render_image = ImageTk.PhotoImage(new_image)
my_image = tkinter.Label(right_frame, image=render_image,bg='#F8F9FA')
my_image.grid(row=0,column=0)
window.resizable(0,0)
my_label = tkinter.Label(left_frame,text='BIQUI - Busquedas para Ingeneria Quimica',bg='#F8F9FA',fg='#6C757D',font=(None,11,'bold'),wraplength=250,borderwidth=10)
my_label.grid(row=7,column=0,pady=40)
# Scrollbar
scrollbar_1=tkinter.Scrollbar(master=window,width=20)



#----------------------------------------
# Add main application to the frames

# Create class
label_list=[]
label_list.append(my_label)
scrollbar_list=[]
class jobs_dataframe_manager():
    def __init__(self, *args, **kwargs):
        self.df=pd.DataFrame(*args, **kwargs)
        self.limit_imports = 50
        self.scrolling_pos=0
        self.number_jobs = 10
        self.cv_filepath=None

        self.ranking_index=False
        self.ranking_scores=False
        self.df2=None
        self.active_plot=False
        self.changed_index=False
        self.variable_list=False

        self.filepath_data=False
        self.filepath_load1=False
        self.filepath_load2 = False
        self.loaded_files = False

    def clear_labels(self):
        global label_list
        if label_list != []:
            for lab_idx in range(len(label_list) - 1, -1, -1):
                label_list[lab_idx].destroy()

    def clear_plot(self):
        if self.active_plot:
            global plot_list
            for plot_widget in plot_list:
                plot_widget.destroy()

            plot_list=[]
            self.active_plot=False

    def show_by_date(self):
        if self.loaded_files:
            self.ranking_index = False
            self.show_jobs()
        else:
            self.load_files()

    def load_files(self):
        self.clear_labels()
        self.clear_plot()

        title_config= {'bg': 'white', 'fg': 'black', 'borderwidth': 1}
        title_name='Direccion del archivo del chat de IQ en .txt'

        title_label=tkinter.Label(left_frame,wraplength=left_frame.winfo_width()-2,**title_config)
        title_label.grid(column=0,row=len(button_names)+2,padx=5,pady=5)
        label_list.append(title_label)
        title_label.config(text=title_name)

        self.filepath_data = tkinter.StringVar()
        button_entry = tkinter.Entry(left_frame, width=32, textvariable=self.filepath_data)

        button_entry.grid(column=0, row=len(button_names)+3, padx=5, pady=5)

        label_list.append(button_entry)
        label_list.append(title_label)

        confirm_button_config = {'bg': '#20639B', 'fg': 'white', 'width': 32, 'borderwidth': 1,'relief': tkinter.FLAT}
        confirm_entry = tkinter.Button(left_frame, text='Procesar direcciones', command=self.process_files,**confirm_button_config )
        confirm_entry.grid(column=0, row=len(button_names)+4, padx=5, pady=5)
        label_list.append(confirm_entry)


    def process_files(self):

        self.filepath_data=self.filepath_data.get()
        self.filepath_load1=r'{}\App_BIQUI\Excel_Principal_BIQUI.xlsx'.format(os.getcwd())
        self.filepath_load2 =r'{}\App_BIQUI\Excel_Secundario_BIQUI.xlsx'.format(os.getcwd())
        try:
            self.df= pd.read_excel(self.filepath_load1,index_col=0)
            self.df=correct_dataframe(self.df)
            if self.df.shape[1]>4:
                self.loaded_files=True
                self.clear_labels()
                window.resizable(True, True)
                my_image.destroy()

                scrollbar_1.pack(side=tkinter.RIGHT, fill=tkinter.Y)
                # Create instance
                scrollbar_links = my_scrollbar()
                scrollbar_1.config(command=scrollbar_links.scrolling)
                global scrollbar_list
                scrollbar_list.append(scrollbar_links)

        except:
            title_config = {'bg': 'white', 'fg': 'red', 'width': 32, 'borderwidth': 1}
            title_label = tkinter.Label(left_frame, **title_config)
            title_label.grid(column=0, row=len(button_names) + 11, padx=5, pady=5)
            title_label.config(text='Cargar direccion correcta')
            label_list.append(title_label)

    def show_jobs(self):
        self.clear_labels()
        self.clear_plot()

        color_palette = ['#012A4A', '#013A63', '#01497C', '#014F86', '#2A6F97', '#2C7DA0', '#468FAF', '#61A5C2',
                         '#89C2D9', '#A9D6E5']
        color_palette.reverse()

        if self.ranking_index != False:
            if self.number_jobs+self.scrolling_pos>self.df.shape[0]-1:
                index_labels = self.ranking_index[self.scrolling_pos:]
            else:
                index_labels= self.ranking_index[self.scrolling_pos:self.scrolling_pos+self.number_jobs]
            scrolling_df=self.df2

        else:
            index_labels=self.df.sort_index(ascending=False).index[self.scrolling_pos:self.scrolling_pos+self.number_jobs].to_list()
            scrolling_df = self.df

        split_idx_func = lambda x, L, n: min([t if np.linspace(0, L, n + 1)[t + 1] > x and np.linspace(0, L, n + 1)[t] < x else n - 1 for t in range(n)])
        text_color = lambda x: 'white' if x[1] < '6' else '#022B3A'

        n_row=0
        for idx_lab in range(len(index_labels)):
            location=index_labels[idx_lab]
            background_color=color_palette[split_idx_func(location,scrolling_df.shape[0],len(color_palette))]
            visuals={'bg':background_color,'fg':text_color(background_color)}
            label=tkinter.Label(right_frame,text=scrolling_df.content[location],justify=tkinter.LEFT,wraplength=right_frame.winfo_width()-30,**visuals)
            label.grid(column=1,row=n_row,pady=5)
            n_row+=1

            hyperlink_button=tkinter.Button(right_frame,text=scrolling_df.url[location],command=urls_opener(scrolling_df,location),justify=tkinter.LEFT,wraplength=right_frame.winfo_width()-30,bg='white',fg='black',relief=tkinter.FLAT)
            right_frame.update()
            hyperlink_button.grid(column=1,row=n_row,pady=0)
            n_row += 1

            label_list.append(label)
            label_list.append(hyperlink_button)

    def update_list(self):
        self.clear_labels()
        self.clear_plot()

        if self.loaded_files:
            waiting_label_visuals={'bg':'#3D5A80','fg':'white','width':100}
            waiting_label = tkinter.Label(right_frame, text='Actualizando enlaces...programa ocupado', justify=tkinter.RIGHT,
                                  wraplength=right_frame.winfo_width() - 30,**waiting_label_visuals)
            waiting_label.grid(column=1, row=1, padx=5, pady=5)
            label_list.append(waiting_label)
            right_frame.update()
            right_frame.after(3000)

            self.df=update_jobs(self.df,self.filepath_data,self.filepath_load2,self.limit_imports)
            self.transform_dataframe()
            self.show_jobs()
            waiting_label.destroy()
        else:
            self.load_files()

    def transform_dataframe(self):
        self.df=transform_jobs_df(self.df,self.filepath_load1)
        self.df=correct_dataframe(self.df)

    def full_plotting(self):
        self.clear_labels()
        self.clear_plot()

        if self.loaded_files:
            figsize=(right_frame.winfo_width() // 100 ,right_frame.winfo_height() // 100)
            full_plot(self.df,figsize,frame=right_frame)
        else:
            self.load_files()


    def load_cv(self):
        self.clear_labels()

        if self.loaded_files:
            cv_title_config = {'bg': 'white', 'fg': 'black', 'width': 32, 'borderwidth': 1}
            cv_title=tkinter.Label(left_frame,text='Insertar direccion del CV en formato .txt',**cv_title_config)
            cv_title.grid(column=0,row=len(button_names)+2,padx=5,pady=5)

            self.cv_filepath=tkinter.StringVar()
            cv_filepath_entry=tkinter.Entry(left_frame,width=32,textvariable=self.cv_filepath)
            cv_filepath_entry.grid(column=0, row=len(button_names)+3,padx=5,pady=5)

            preferred_jobs()

            confirm_button_config = {'bg': '#00A8E8', 'fg': 'white', 'width': 32, 'borderwidth': 1,'relief': tkinter.FLAT}
            confirm_cv_entry = tkinter.Button(left_frame, text='Procesar CV', command=my_manager.show_by_relevance,**confirm_button_config)
            confirm_cv_entry.grid(column=0, row=20, pady=5)
            label_list.append(confirm_cv_entry)
            label_list.append(cv_title)
            label_list.append(cv_filepath_entry)
        else:
            self.load_files()





    def process_cv(self):
        self.clear_labels()

        address_entry=self.cv_filepath.get()
        self.df2 = pd.read_excel(self.filepath_load1, index_col=0)
        self.df2.drop(self.df2.tail(1).index[0], axis=0, inplace=True)
        self.df2.iloc[:, 3:] = self.df2.iloc[:, 3:].astype('boolean')
        self.df2 = self.df2[np.logical_and(self.df2.content != 'Blocked', self.df2.content != 'Discard')].drop_duplicates().reset_index(drop=True)
        self.df2.loc[self.df2.url == 0, 'url'] = self.df2.loc[self.df2.url == 0, 'url'].replace(0, 'No tiene link')
        self.df2=self.df2[self.df2.IngQ].reset_index(drop=True)

        try:
            excluded_words()
            self.ranking_index,self.ranking_scores=cv_matcher(self.df2,address_entry,self.variable_list)
            self.ranking_index = list(self.ranking_index)
            self.changed_index=True


        except:
            self.changed_index=False
            wrong_entry_label = tkinter.Label(left_frame, text='Direccion incorrecta', fg="red", bg='white')
            wrong_entry_label.grid(row=10, column=0,padx=5,pady=5)
            label_list.append(wrong_entry_label)

    def show_by_relevance(self):
        self.process_cv()
        if self.changed_index:
            self.scrolling_pos=0
            self.show_jobs()

    def load_second_cv(self):
        self.clear_labels()
        if self.loaded_files:
            cv_title_config = {'bg': 'white', 'fg': 'black', 'width': 32, 'borderwidth': 1}
            cv_title=tkinter.Label(left_frame,**cv_title_config)
            cv_title.grid(column=0,row=len(button_names)+2,padx=5,pady=5)
            label_list.append(cv_title)

            if self.ranking_index!=False:
                cv_title.config(text='Insertar Segundo CV en formato .txt')
                self.cv_filepath = tkinter.StringVar()
                cv_filepath_entry = tkinter.Entry(left_frame, width=32, textvariable=self.cv_filepath)
                cv_filepath_entry.grid(column=0, row=len(button_names) + 3, padx=5, pady=5)

                preferred_jobs()

                confirm_button_config = {'bg': '#00A8E8', 'fg': 'white', 'width': 32, 'borderwidth': 1,'relief': tkinter.FLAT}
                confirm_cv_entry = tkinter.Button(left_frame, text='Procesar CV', command=my_manager.analize_cv_mod, **confirm_button_config)
                confirm_cv_entry.grid(column=0, row=20, pady=5)
                label_list.append(cv_filepath_entry)
                label_list.append(confirm_cv_entry)


            else:
                cv_title.config(text='Procesar primer CV primero',fg='red')

        else:
            self.load_files()



    def analize_cv_mod(self):
        scores1 = self.ranking_scores
        idx1=self.ranking_index
        self.process_cv()
        if self.changed_index:
            scores2 = self.ranking_scores
            idx2=self.ranking_index

            coupled_scores2={k:v for k,v in zip(idx2,scores2)}
            sorted_scores2=[coupled_scores2[t] for t in idx1]
            scores1=list(scores1)

            self.clear_labels()
            self.clear_plot()
            figsize = (right_frame.winfo_width() // 100, right_frame.winfo_height() // 100)
            analize_cv_modifications(scores1, sorted_scores2,right_frame,figsize)



def excluded_words():
    Excluded_words = ['clinicos', 'hisopad', 'alimentos']
    d_S = dict_list[3]
    d_P = dict_list[0]
    button_names = list(d_S.keys())
    Excluded_list = Excluded_words + d_P['Lic_BQ_IngAl'] + d_P['Operario']
    for idx in range(len(my_manager.variable_list)):
        if bool(my_manager.variable_list[idx].get()):
            Excluded_list = Excluded_list + d_S[button_names[idx]]

    my_manager.variable_list=Excluded_list

    
# Create instance
my_manager=jobs_dataframe_manager(jobs_df)

# Manage web browser
def urls_opener(df,location):
    def enter_urls():
        webbrowser.open_new(df.url[location])
    return enter_urls

def preferred_jobs():
    d_S = dict_list[3]

    button_names = list(d_S.keys())
    button_config = {'bg': '#DEE2E6', 'fg': '#343A40','selectcolor':'#0096C7','relief':tkinter.FLAT,'width': 30}


    label_button_confg = {'bg': 'white', 'fg': 'black', 'borderwidth': 1}
    label_button = tkinter.Label(left_frame, text='Dar preferencia a aquellos trabajos que no exijan',**label_button_confg)
    label_button.grid(column=0, row=9,sticky=E)
    label_list.append(label_button)

    my_manager.variable_list = []
    for idx in range(len(button_names)):
        check_bool = IntVar()
        check_button = tkinter.Checkbutton(left_frame, text=button_names[idx], variable=check_bool, onvalue=1,offvalue=0,**button_config)
        check_button.grid(row=10+idx, column=0,padx=0)
        my_manager.variable_list.append(check_bool)
        label_list.append(check_button)



#-------------------------------------------------------------------------------
# Modify scrollbar

# Add dynamic waiting label
scrollbar_lab = tkinter.Label(left_frame, fg="green",bg='white')
scrollbar_lab.grid(row=6,column=0)


# Create dynamic label manager
class my_scrollbar():
    def __init__(self):
        self.count=3
        self.scrolling_pos=0
        self.delayed_action=None
        self.total_length=my_manager.df.shape[0]

    def reset_countdown(self):
        scrollbar_lab.config(fg='green')
        self.count=3
        if self.delayed_action!=None:
            scrollbar_lab.after_cancel(self.delayed_action)
        self.countdown()

    def countdown(self):
        self.count-=1
        scrollbar_lab.config(text='Espere '+str(self.count)+' segundos')
        if self.count>=0:
            self.delayed_action=scrollbar_lab.after(500, self.countdown)
        else:
            self.count=3
            scrollbar_lab.config(fg='red')
            scrollbar_lab.config(text='Posicion '+str(self.scrolling_pos))

            my_manager.scrolling_pos=self.scrolling_pos
            my_manager.show_jobs()

    def scrolling(self, *args):
        self.reset_countdown()

        if len(args) == 2:
            relative_position = args[1]
            self.scrolling_pos = round(float(relative_position) * self.total_length)
            pass
        elif len(args) == 3:
            displacement = args[1]
            self.scrolling_pos += int(displacement)
            if self.scrolling_pos < 0:
                self.scrolling_pos = 0
            elif self.scrolling_pos > self.total_length- 1:
                self.scrolling_pos = self.total_length- 1
        else:
            pass

        scrollbar_1.set(self.scrolling_pos / self.total_length, (self.scrolling_pos +1) / self.total_length)



# Manage to close all events

def quit_program_X():
    try:
        global scrollbar_list
        sc = scrollbar_list[0]
        def quit_program(sc):
            for iteration in range(3):
                scrollbar_lab.after_cancel(sc.delayed_action)
                scrollbar_lab.destroy()

        if messagebox.askokcancel('Salir','Desea salir del programa ??'):
            if sc.delayed_action!=None:
                quit_program(sc)
            window.destroy()
    except:
            window.destroy()


window.protocol('WM_DELETE_WINDOW',quit_program_X)

#-------------------------------------------
# Add buttons to the app

# Configure buttons
visual_button_config={'bg':'#0096C7','fg':'white','width':32,'borderwidth':1,'relief':tkinter.FLAT}
button_names=['Actualizar trabajos','Resumen grafico','Mostrar trabajos por fecha','Mostrar trabajos por relevancia con CV','Comparar modificaciones del CV']
function_buttons=[my_manager.update_list,my_manager.full_plotting,my_manager.show_by_date,my_manager.load_cv,my_manager.load_second_cv]



# Create buttons
menu_button_list=[]
for idx,name,func in zip(range(1,len(button_names)+1),button_names,function_buttons):
    menu_button= tkinter.Button(left_frame,text=name,command=func,**visual_button_config)
    menu_button.grid(row=idx,padx=5,pady=5)
    menu_button_list.append(menu_button)

#-------------------------------------------------------------------------------
# Add plotting functions

# Create dataframe with plot data
def feat_for_plot(jobs_df,from_col='Office',until_col='None',from_lab='Ingeniero',until_lab='Otros'):
    plot_df,list_df=pd.DataFrame(),[]
    label_list = jobs_df.columns.to_list()
    if until_col == 'None':
        until_col = None
    if until_lab=='None':
        fr_idx=label_list.index(from_lab)
        labels = label_list[fr_idx:]
    else:
        fr_idx,unt_idx=label_list.index(from_lab),label_list.index(until_lab)
        labels=label_list[fr_idx:unt_idx+1]

    for i in labels:
        plot_df=(jobs_df[jobs_df[i]].loc[:,from_col:until_col].sum()/jobs_df.loc[:,from_col:until_col].sum()).rename(i)
        list_df.append(plot_df)
    plot_df= pd.concat(list_df,join='outer',axis=1).fillna(0).sort_values(by=labels[0],ascending=False)
    return plot_df

# Take plot data and show it
plot_list=[]
def full_plot(jobs_df,figsize=(6,4),manual_plot=True,frame=None):
    w = 0.07
    r, c = 3, 2
    mod_list = jobs_df.columns.to_list()
    for lab in mod_list:
        if lab == 'Otros':
            mod_list[mod_list.index(lab)] = 'LicQ_BQ_IngAli'
    jobs_df.columns = mod_list

    f_args = pd.DataFrame(np.empty([6, 4]))
    f_args.loc[0, :] = ('Postgrado', 'Operario', 'Office', 'CAD_otros')
    f_args.loc[1, :] = ('Postgrado', 'Operario', 'Control_calidad', 'Otras')
    f_args.loc[2, :] = ('Control_calidad', 'Otras', 'Office', 'CAD_otros')
    f_args.loc[3, :] = ('Control_calidad', 'Otras', 'proactiv', 'flexibil')
    f_args.loc[4, :] = ('proactiv', 'flexibil', 'Postgrado', 'Operario')
    f_args.loc[5, :] = ('Office', 'CAD_otros', 'proactiv', 'flexibil')


    fig = Figure(figsize=figsize,facecolor='#F8F9FA')
    plot_number = int(str(r) + str(c) + '1')

    fig.tight_layout(pad=7,h_pad=0.5,w_pad=0.5)

    for j in range(c):
        for i in range(r):
            coord = int(j * r + i)
            p_df = feat_for_plot(jobs_df, f_args.loc[coord, 0], f_args.loc[coord, 1], f_args.loc[coord, 2],
                                 f_args.loc[coord, 3])

            if coord==5:
                website_df=jobs_df.loc[:,['Postgrado','IngQ','Lic_BQ_IngAl','Tecnico','Operario']].join(pd.get_dummies(jobs_df.website).astype('boolean'))
                p_df= feat_for_plot(website_df,'Postgrado','Operario','No tiene link','None')

            idx_lab = p_df.index.to_list()
            col_lab = p_df.columns.to_list()
            x = np.arange(len(idx_lab))


            cur_ax = fig.add_subplot(plot_number)
            plot_number += 1

            color_list=cm.BuPu(np.linspace(0.2, 1, len(col_lab)+1))

            for k in range(len(col_lab)):
                y=p_df.loc[:, col_lab[k]]
                cur_ax.bar(x - w * (len(col_lab)) / 2 + w * k, y , 0.9 * w, label=col_lab[k] ,color=color_list[k])
                cur_ax.set_xticks(x)
                cur_ax.set_xticklabels(idx_lab, rotation=15, fontdict={'fontsize': 7})
                cur_ax.legend(col_lab, fontsize=6,framealpha=0.3,loc='upper right',bbox_to_anchor=(0.5,0.9,0.6,0.1))
                cur_ax.set_ylabel('Prop. de trabajos ',rotation=90, fontdict={'fontsize': 7})
                cur_ax.spines['top'].set_visible(False)
                cur_ax.spines['right'].set_visible(False)
                cur_ax.spines['left'].set_color(color_list[-1])
                cur_ax.spines['right'].set_color(color_list[-1])
                for tick in cur_ax.yaxis.get_majorticklabels():
                    tick.set_fontsize(7)

            cur_ax.grid()

    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.draw()
    plot_widget=canvas.get_tk_widget()
    plot_widget.grid(row=1, column=1, columnspan=3)

    global plot_list
    plot_list.append(plot_widget)
    my_manager.active_plot=True

def analize_cv_modifications(scores1,scores2,frame,figsize):
    m1,M1=min(scores1),max(scores1)
    norm_scores1=[(t-m1)/(M1-m1) for t in scores1]
    norm_scores2 =[(t - m1) /(M1-m1) for t in scores2]

    #hist_hier_dif=pd.Series([idxBase.index(t)-idxChanged.index(t) for t in idxBase])

    fig = Figure(figsize=figsize,facecolor='#F8F9FA')
    fig.tight_layout(pad=7, h_pad=0.5, w_pad=0.5)
    ax=fig.add_subplot(111)
    ax.hexbin(norm_scores1,norm_scores2,gridsize=25,cmap='Blues',alpha=0.5,marginals=True)
    ax.plot(norm_scores1,norm_scores1,color='#0096C7',linestyle='--',alpha=0.7)


    ax.set_ylabel('Puntajes trabajos CV 2 ',rotation=90, fontdict={'fontsize': 10})
    ax.set_xlabel('Puntajes trabajos CV 1 ',fontdict={'fontsize': 10})
    ax.set_title('Comparacion de puntajes normalizados')
    ax.set_xlim(left=0,right=1)
    ax.set_ylim(bottom=min(norm_scores2),top=max(norm_scores2))

    ax.spines['left'].set_color('#003459')
    ax.spines['bottom'].set_color('#003459')
    ax.spines['right'].set_color('#EAF4F4')
    ax.spines['top'].set_color('#EAF4F4')

    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.draw()
    plot_widget = canvas.get_tk_widget()
    plot_widget.grid(row=1, column=1, columnspan=3,padx=15,pady=5)

    global plot_list
    plot_list.append(plot_widget)
    my_manager.active_plot = True

#-------------------------------------------------------------------------------
window.mainloop()


