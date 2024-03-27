#Automação da extração das bases para o case FFM - visão totais
#Guilherme Augusto Martins
#Bibliotecas necessárias para a execução, incluindo a Selenium que faz navegação e extração de dados na web

import pandas as pd
from selenium.webdriver.chrome.service import Service as Service
from selenium import webdriver as webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager
import time as t
from itertools import product
import re
from matplotlib import pyplot as plt

now = t.time()
# Página onde estão os dados
url = "https://gco.iarc.fr/causes/obesity/tools-bars"

# Configurando o driver da web
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)
driver.get(url)

WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//div[@id='main-content']")))

#Obtenho a lista de opções disponíveis para cada filtro
ng_values = ['mMode', 'mRegion', 'mCancer', 'mSex', 'mScenario']
ng_dict={}

#Ajusto minhas opções de filtro para remover visões totais e por região anatômica
for val in ng_values:
    
    dropdown = driver.find_element(By.CSS_SELECTOR, f'select[ng-model="{val}"]')
    select = Select(dropdown)
    options = [option.text for option in select.options]
    if 'Anatomical site' in options: 
        options.remove('Anatomical site')
    if 'Both' in options: 
        options.remove('Both')
    if 'All sites' in options: 
        options.remove('All sites')
    if 'All regions' in options: 
        options.remove('All regions')
    if 'The world' in options: 
        options.remove('The world')
    ng_dict.update({val: options})

#Crio uma lista de todas as possíveis combinações de filtro e elimino as inválidas. eg: Câncer de ovário em homens (feito conforme os filtros ficavam indisponíveis no site)
combinations = list(product(*ng_dict.values()))

valid_combinations=[]

for combination in combinations:
    if combination[3]=='Males':
        if combination[2] in ['Colon', 'Kidney', 'Oesophageal adenocarcinoma', 'Pancreas', 'Rectum']:
            valid_combinations.append(combination)
        else:        
            pass
    if combination[3]=='Females':        
        valid_combinations.append(combination)

#Obtidas as combinações de filtro válida, passamos à extração dos dados a partir do site

#Base para alocação dos dados
df= pd.DataFrame()

t.sleep(5)

for combination in valid_combinations:

    print ("Obtendo dados para:",combination)

    #Crio as váriaveis de filtro para serem usadas no seletor CSS da biblioteca Selenium 
    mMode = combination[0]
    mRegion = combination[1]
    mCancer = combination[2]
    mSex = combination[3]
    mScenario = combination[4]

    #Região/Continente
    dropdown_mMode = driver.find_element(By.CSS_SELECTOR, 'select[ng-model="mMode"]')
    select_mMode = Select(dropdown_mMode)
    select_mMode.select_by_visible_text(mMode)

    #População
    dropdown_mRegion = driver.find_element(By.CSS_SELECTOR, 'select[ng-model="mRegion"]')
    select_mRegion = Select(dropdown_mRegion)
    select_mRegion.select_by_visible_text(mRegion)

    #Região Anatômica
    dropdown_mCancer = driver.find_element(By.CSS_SELECTOR, 'select[ng-model="mCancer"]')
    select_mCancer = Select(dropdown_mCancer)
    select_mCancer.select_by_visible_text(mCancer)

    #Sexo
    dropdown_mSex = driver.find_element(By.CSS_SELECTOR, 'select[ng-model="mSex"]')
    select_mSex = Select(dropdown_mSex)
    select_mSex.select_by_visible_text(mSex)

    #Cenário
    dropdown_mScenario = driver.find_element(By.CSS_SELECTOR, 'select[ng-model="mScenario"]')
    select_mScenario = Select(dropdown_mScenario)
    select_mScenario.select_by_visible_text(mScenario)

    #Pausa para carregar os dados
    t.sleep(2)

    #Extrai os dados carregados
    data_element = driver.find_element(By.XPATH, "//div[@id='data-table']")
    data = data_element.text
  
    #Aloca os dados em uma lista
    lines = data.split('\n')
    lines = lines[1:]

    #Separa os dados por país
    country = []
    cases = []

    for line in lines:  

        line=line[re.search(r'[a-zA-Z]', line).start():]
        country.append(line[:re.search(r'\d', line).start()-1])
        cases.append(line[re.search(r'\d', line).start():])

    #Cria o datafrme auxiliar
    aux = pd.DataFrame({
        'País': country,
        'Casos': cases,
    })

    #Cria colunas auxiliares
    aux['Região/Continente'] = [combination[1] for _ in range(len(aux))]
    aux['Região Anatômica'] = [combination[2] for _ in range(len(aux))]
    aux['Sexo'] = [combination[3] for _ in range(len(aux))]
    aux['Cenário'] = [combination[4] for _ in range(len(aux))]

    #Concatena os dados
    df= pd.concat([aux,df])

df['Casos'] = df['Casos'].apply(lambda x :x.replace(' ',''))

df['Casos'] = df['Casos'].apply(lambda x :float(x))

later = t.time()

df.to_excel('saida_bars.xlsx')

print("Levou:" + str(round((later-now)/60)))  

df= pd.read_excel('/home/guigo23/Área de Trabalho/saida_bars.xlsx')

continentes=['The Americas','Oceania','Europe','Asia','Africa']

df['continente'] =  df['Região/Continente'].apply(lambda x: 1 if x in continentes else 0)

df_con = df[df.continente==1]

df_con[(df_con['Região/Continente']=='Europe') & (df_con['Região Anatômica']=='Colon')].Casos.hist()
plt.title("Distribuição na Ásia Câncer de Mama")
plt.show()