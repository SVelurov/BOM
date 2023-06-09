# -*- coding: utf-8 -*-
"""BOM.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1osg05gbpNJVDOlCtkD3AaCZoOkuC8yRC

**Выгрузка списка запчастей из BOM**
"""

import pandas as pd
pd.options.mode.chained_assignment = None
import zipfile
import os      
import re

import warnings
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

from google.colab import drive
drive.mount('/content/drive')

# каталоги проекта
PROJECT_PATH = '/content/drive/MyDrive/KIVI'
BOM_LIST = '/content/drive/MyDrive/KIVI/SKD'

# распаковываем zip-архив в каталог с названием архива
for filename in os.listdir(PROJECT_PATH):
  if filename.endswith('.zip'):
    with zipfile.ZipFile(PROJECT_PATH + '/' + filename, 'r') as zip_ref:
        zip_ref.extractall(PROJECT_PATH)
    zip_ref.close()

# заменим пробелы в названиях файлов на подчеркивания
for filename in os.listdir(BOM_LIST):
  file_oldname = os.path.join(BOM_LIST + '/', filename)
  #file_newname = os.path.join(BOM_LIST + '/', re.sub("[^A-Za-z0-9.|_]\\.\\_", "", '_'.join(filename.split())))
  file_newname = os.path.join(BOM_LIST + '/', '_'.join(filename.split()))
  os.rename(file_oldname, file_newname)

# уберем китайские иероглифы
def replace_chinese_characters(text):
    return re.sub(r'[\u4e00-\u9fff]|[\n]', '', str(text))

# уберем двойные пробелы
def replace_multiple_spaces(text):
  return re.sub(r"\s(\s)", '\\1', str(text))

# ищем расположение Brend столбец
def Brend_col(brend, row_english):
  brend_col = []
  for column_number in range(bom.shape[1]):
    for i in bom.iloc[:row_english,column_number]:
      for z in range(len(i)):
        if i[z:z+len(brend)] == brend:
          brend_col.append(column_number)
          break      
    
  return(brend_col[0])

# ищем название Model         
def Model_no(brend, fixed_brend_col):
  kivi_row = []  
  for row_number in range(bom.shape[0]):
    i = bom.iloc[row_number, fixed_brend_col]
    for z in range(len(i)):
      if i[z:z+len(brend)] == brend:
        kivi_row.append(row_number)
        break

  return(bom.iloc[kivi_row[0]+1,fixed_brend_col])    

# ищем SAP номер         
def SAP_no(brend, fixed_brend_col):
  for row_number in range(bom.shape[0]):
    i = bom.iloc[row_number, fixed_brend_col]
    for z in range(len(i)):
      if i[z:z+len(brend)] == brend:
        row_model = row_number
        break

  return(bom.iloc[row_model-1,fixed_brend_col][:10])     
  
# ищем расположение Specification столбец
def specs_loc_col():
    pattern1 = 'Specification'
    pattern2 = 'Chinese Name'
    for column_number in range(bom.shape[1]):
      for i in bom.iloc[:,column_number]:
        for z in range(len(i)):
          if i[z:z+len(pattern1)] == pattern1:
            column_specs = column_number
          elif i[z:z+len(pattern2)] == pattern2:
            column_specs = column_number
            break

    return(column_specs)

# ищем расположение English столбец
def english_loc_col():
  pattern1 = 'English'
  pattern2 = 'English Name'
  column_english = []
  for column_number in range(bom.shape[1]):
    for i in bom.iloc[:,column_number]:
      for z in range(len(i)):
        if i[z:z+len(pattern1)] == pattern1:
          column_english = column_number
        elif i[z:z+len(pattern2)] == pattern2:
          column_english = column_number          
          break
  
  return(column_english)

# ищем расположение English
def english_loc():  
  pattern = 'English'
  interim = []
  for row_number in range(bom.shape[0]):
    i = bom.iloc[row_number,english_loc_col()]
    for z in range(len(i)):
      if i[z:z+len(pattern)] == pattern:
        interim.append(row_number)

  return(interim[0], interim[-1])

# выводим полный список парткодов по всем BOM в каталоге

brend = 'KIVI'

filenames = [file for file in os.listdir(BOM_LIST) if file.endswith(('.xlsx', '.xls'))]

bom_list = pd.DataFrame(columns=['Model', 'SAP number', 'Part number', 
                  'Description'])
for bom_file in filenames:
  bom = pd.read_excel(BOM_LIST + '/' + bom_file, header=None)
  print(bom_file)

  # убираем китайские иероглифы и лишние пробелы в каждой ячейки
  bom = bom.applymap(replace_chinese_characters)
  bom = bom.applymap(replace_multiple_spaces)
    
  # найдем подожение столбца English
  row_english_first, row_english_last = english_loc()
  column_english = english_loc_col()
  
  # блок для новых линеек ТВ
  if row_english_first > 0:

    # переименовываем столбцы
    bom.columns = list(range(len(bom.columns)))

    row_english = english_loc()[0]-1
    fixed_brend_col = Brend_col(brend, row_english)
    column_specs = specs_loc_col()
  
    new_col_name = bom.iloc[row_english_first].tolist()
    new_col_name[0] = 'Model'
    new_col_name[column_english - 2] = 'Component number'
    new_col_name[column_english - 1] = 'Part number'
    new_col_name[column_english] = 'English name'
    new_col_name[column_english + 1] = 'Description'
    new_col_name[-1] = 'SAP number'
    bom.columns = new_col_name

    # внесем в первые столбцы название модели и SAP номер
    fixed_SAP_no = SAP_no(brend, fixed_brend_col)
    bom['SAP number'] = fixed_SAP_no
    fixed_Model_no = Model_no(brend, fixed_brend_col)
    bom['Model'] = fixed_Model_no

    # уберем ненужные столбцы
    new_col_name = ['Model', 'SAP number', 'Component number', 'Part number', 
                    'English name', 'Description']
    bom = bom.loc[:,new_col_name]
      
    # обрежем нижние ненужные поля
    bom.drop(bom.index[row_english_last-1:], inplace=True)

    # обрежем верхние ненужные поля
    bom.drop(bom.index[:row_english_first+1], inplace=True)

   # блок для старых линеек ТВ
  else:

    column_specs = specs_loc_col()

    # добавляем колонку для Description
    if column_specs - column_english < 2:
      bom.insert(loc = column_english+1,
          column = 'Description',
          value = '')
       
    # переименовываем столбцы
    new_col_name = bom.iloc[row_english_first].tolist()
    new_col_name[0] = 'Model'
    new_col_name[column_english - 2] = 'Component number'
    new_col_name[column_english - 1] = 'Part number'
    new_col_name[column_english] = 'English name'
    new_col_name[column_english + 1] = 'Description'
    new_col_name[-1] = 'SAP number'
    bom.columns = new_col_name
    bom.drop(index=[0], inplace = True)

    # внесем в первые столбцы название модели и SAP номер
    bom['SAP number'] = ''
    bom['Model'] = ''

    # уберем ненужные столбцы
    new_col_name = ['Model', 'SAP number', 'Component number', 'Part number', 
                    'English name', 'Description']
    bom = bom.loc[:,new_col_name]

  # заменить все nan на пусто
  bom.where(bom != 'nan', other = '', inplace=True)

  # уберем ненужные строки
  empty_rows = []
  for i in range(len(bom.index)):
    if (len(bom['Component number'].iloc[i]) < 2) & (len(bom['Part number'].iloc[i]) < 2):
      empty_rows.append(i)
  bom.drop(bom.index[empty_rows], inplace=True)

  # восстановим нумерацию
  bom = bom.reset_index(drop = True)

  # убираем спецификации если отсутствует описание партномеров
  if column_specs - column_english < 2:
    bom['Description'] = ''

  # заполним отсутствующие описания партномеров
  for i in range(len(bom.index)):
    if (len(bom['Description'].iloc[i]) < 2):
      bom['Description'].iloc[i] = bom['English name'].iloc[i]

  # уберем букву J, K, P и N и пробел в парткоде 
  bom['Part number'] = bom['Part number'].map(lambda x: x.lstrip('JKNP '))
  bom['Component number'] = bom['Component number'].map(lambda x: x.lstrip('JKNP '))

  # дополняем описание парткодов
  check_list = ['504Q', '511Q', '4031Q', '504MTC', '209', '207', '4043', '124Q', '1250', 
                '107Q', '123Q', '3044', '3042', '601P', '3043', '217', '540Y', '3045', '322',
                '2551', '523C', '4032Q', '1251', '4022Q', '4034Q', '205Q', '4035Q', '4021Q',
                '2161', '4024Q', '4023Q', '4033Q', '1254', '506Q', '215A', '221Q', '3291',
                '204Q', '511G']

  replace_list = ['Remote', 'IR Board Assembly', 'Instruction manual', 'Speaker',
                  'Screw', 'Hex Wrench', 'PE Bag(user manual)', 'Plastic parts', 'Plastic parts', 
                  'IR Board Assembly parts', 'IR Board Assembly parts', 
                  'Connector wire', 'IR Board Assembly parts', 
                  'IR Board Assembly parts', 'AV signal line', 'Sponge cushion', 
                  'Bluetooth module', 'Power Cord', 'Battery', 'Buffer tape', 
                  'Power switch line assembly', 'Instruction manual', 
                  'Plastic parts', 'Energy consumption sticker', 'Instruction manual',
                  'Tail bracket', 'Warranty card', 'Energy consumption sticker', 
                  'Heat Shrinkable Tubing', 'Energy consumption sticker', 
                  'Energy consumption sticker', 'Warranty card', 'Shading film', 
                  'Voice structure material components', 'Plugging silicone pad',
                  'Insulation sheet', 'Cable tie', 'Base bracket ', 
                  'Button remote control board assembly']

  for i in range(len(bom.index)):
    for j in range(len(check_list)):
      if (len(bom['Description'].iloc[i]) < 2) & \
        (bom['Part number'].iloc[i][:len(check_list[j])] == check_list[j]):
        bom['Description'].iloc[i] = replace_list[j]                                                         

  # разделим компоненты и партномера
  bom_component = bom.drop(columns = ['Part number', 'Description'])
  bom_component.columns = ['Model', 'SAP number', 'Part number', 'Description']
  bom_part = bom.drop(columns = ['Component number', 'English name'])   

  # обьеденим компоненты и запчасти
  bom = pd.concat([bom_part, bom_component], axis = 0, ignore_index = True)

  # уберем ненужные строки
  empty_rows = []
  for i in range(len(bom.index)):
    if (len(bom['Part number'].iloc[i]) < 2):
      empty_rows.append(i)
  bom.drop(bom.index[empty_rows], inplace=True)

  # убираем дубликаты парткодов
  bom = bom.drop_duplicates(subset=['Part number'], ignore_index=False, keep='first')
  
  # восстановим нумерацию
  bom = bom.reset_index(drop = True)
  
  # уберем ненужные первые пробелы в описании
  bom['Description'] = bom['Description'].map(lambda x: x.lstrip(' '))

  # поставим заглавную букву в описании
  bom['Description'] = list(map(lambda e: e[:1].upper() + e[1:], bom['Description']))

  # добавим букву K в каждый парткод
  bom['Part number'] = list(map(lambda e: 'K' + e if e[:1] != 'K ' else e, bom['Part number']))

  # добавляем название модели
  if len(bom_file) < 22:
    model_name = bom_file[0:8]
  else:
    model_name = bom_file[11:19]
  bom['Model'] = list(map(lambda e: model_name if len(e) < 2 else e, bom['Model']))

    # добавляем SAP номер
  if len(bom_file) > 20:
    SAP_name = bom_file[0:10]
  else:
    SAP_name = ''
  bom['SAP number'] = list(map(lambda e: SAP_name if len(e) < 2 else e, bom['SAP number']))

  # обьединяем все BOM в один файл 
  bom_list = pd.concat([bom_list, bom], axis=0, ignore_index=True)

# Сохраняем предобработанные данные
bom_list.to_excel(PROJECT_PATH +'/' + 'bom_list.xlsx', index=False)