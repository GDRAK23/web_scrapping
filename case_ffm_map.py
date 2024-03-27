#Automação da extração das bases para o case FFM - visão frações
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

now = t.time()
# Página onde estão os dados
url = "https://gco.iarc.fr/causes/obesity/tools-map"

# Configurando o driver da web
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)
driver.get(url)

WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, "//div[@id='main-content']")))

#Obtenho a lista de opções disponíveis para cada filtro
ng_values = ['mContinent', 'mCancer', 'mSex', 'mScenario']
ng_dict={}

#Ajusto minhas opções de filtro para remover visões totais e por região anatômica
for val in ng_values:
    
    dropdown = driver.find_element(By.CSS_SELECTOR, f'select[ng-model="{val}"]')
    select = Select(dropdown)
    options = [option.text for option in select.options]
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
    if combination[2]=='Males':
        if combination[1] in ['Colon', 'Kidney', 'Oesophageal adenocarcinoma', 'Pancreas', 'Rectum']:
            valid_combinations.append(combination)
        else:        
            pass
    if combination[2]=='Females':        
        valid_combinations.append(combination)

#Obtidas as combinações de filtro válida, passamos à extração dos dados a partir do site

#Base para alocação dos dados
df= pd.DataFrame()

t.sleep(5)

for combination in valid_combinations:

    print ("Obtendo dados para:",combination)

    #Crio as váriaveis de filtro para serem usadas no seletor CSS da biblioteca Selenium 
    mContinent = combination[0]
    mCancer = combination[1]
    mSex = combination[2]
    mScenario = combination[3]

    #Continente
    dropdown_mMode = driver.find_element(By.CSS_SELECTOR, 'select[ng-model="mContinent"]')
    select_mMode = Select(dropdown_mMode)
    select_mMode.select_by_visible_text(mContinent)

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
    aux['Continente'] = [combination[0] for _ in range(len(aux))]
    aux['Região Anatômica'] = [combination[1] for _ in range(len(aux))]
    aux['Sexo'] = [combination[2] for _ in range(len(aux))]
    aux['Cenário'] = [combination[3] for _ in range(len(aux))]

    #Concatena os dados
    df= pd.concat([aux,df])

pd.to_numeric(df['Casos'].str.rstrip('%'), errors='coerce') / 100 

df.to_excel('saida_map.xlsx')

later = t.time()

print("Levou:" + str(round((later-now)/60)))  




