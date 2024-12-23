import argparse
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import csv
from datetime import timedelta, datetime 
import plotly.graph_objects as go

# ------------------------------Fonctions------------------------------

# Fonction pour pré-traiter les données
def create_dataframe(category, file_path, date_column, sex_column, id_column):
    if file_path.endswith('.xlsx'):
        try:
            dataframe = pd.read_excel(file_path)
        except FileNotFoundError:
            raise FileNotFoundError(f"Excel file '{file_path}' not found.")
    elif file_path.endswith('.csv'): 
        try:
            dataframe = pd.read_csv(file_path)
        except FileNotFoundError:
            raise FileNotFoundError(f"CSV file '{file_path}' not found.")

    # Check if the specified columns exist in the dataframe
    if date_column not in dataframe.columns:
        raise ValueError(f"Column '{date_column}' not found in the file.")
    if sex_column not in dataframe.columns:
        raise ValueError(f"Column '{sex_column}' not found in the file.")
    if id_column not in dataframe.columns:
        raise ValueError(f"Column '{id_column}' not found in the file.")

    dataframe[date_column] = pd.to_datetime(dataframe[date_column], errors='coerce')
    
    final_dataframe = pd.DataFrame({
        'Category': [category] * len(dataframe[date_column]),
        'Date' : dataframe[date_column],
        'Sex' : dataframe[sex_column],
        'ID' : dataframe[id_column]
    })

    return final_dataframe
# Fonction pour créer des csv
def create_csv(csv_name, frame):
    with open(csv_name, 'w', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
     # Writing each row from the frame
        for row in frame:
            csv_writer.writerow(row)

    print(f'CSV file "{csv_name}" created successfully.') 

# Fonction de tri 
def filter_data(dataframe, comparison_date, sign):
    if sign == '+':
        filtered_dataframe = dataframe[(dataframe['Date'] <= comparison_date + timedelta(days = args.max_date))
                                      & (dataframe['Date'] >= comparison_date + timedelta(days = args.min_date))]
    if sign == '-':
        filtered_dataframe = dataframe[(dataframe['Date'] <= comparison_date - timedelta(days = args.min_date)) 
                                      & (dataframe['Date'] >= comparison_date - timedelta(days = args.max_date))]
    
    return filtered_dataframe

# Fonction pour extraire les données
def get_matching_data(fist_dataframe, second_dataframe, second_dataframe_filter_sign, final_dataset):

    for _, row in fist_dataframe.iterrows():
        
        first_dataframe_id = row['ID']
        first_dataframe_sex = row['Sex']
        first_dataframe_date = row['Date']

        # Création d'un tableau filtré en fonction des dates du premier tableau
        filtered_second_dataframe = filter_data(second_dataframe, first_dataframe_date, second_dataframe_filter_sign)

        # Création d'un tableau final contenant les ID correspondants à chaque association de dates, et indiquant la meilleure
        if not filtered_second_dataframe.empty: 
            for _, df_row in filtered_second_dataframe.iterrows() :
                second_dataframe_id = df_row['ID']
                second_dataframe_date = df_row['Date']
                second_dataframe_sex = df_row['Sex']

                score = 1-(second_dataframe_date - first_dataframe_date).days/args.max_date

                if (first_dataframe_id != second_dataframe_id and
                    all(entry[2] != second_dataframe_id and entry[3] != first_dataframe_id for entry in final_dataset) and
                    first_dataframe_sex == second_dataframe_sex or first_dataframe_sex is None or second_dataframe_sex is None):
                    if any(entry[0] == first_dataframe_date and 
                        entry[1] > second_dataframe_date
                        for entry in final_dataset):
                        final_dataset.append((first_dataframe_date, second_dataframe_date, first_dataframe_id, second_dataframe_id,score,'Best bet'))
                    else: 
                        final_dataset.append((first_dataframe_date, second_dataframe_date, first_dataframe_id, second_dataframe_id,score,''))       

    return sorted(final_dataset)


# Ajout de tracé
def add_matching_data_trace(category1, category2, fig, data, color, dash):
    for date1, date2, _, _, _, bet in data:
        if bet == 'Best bet':
            fig.add_trace(go.Scatter(x=[date1, date2],
                                    y=[category1, category2],
                                    mode='lines',
                                    line=dict(color=color),
                                    showlegend=False))
        else : 
            fig.add_trace(go.Scatter(x=[date1, date2],
                                    y=[category1, category2],
                                    mode='lines',
                                    line=dict(color=color, dash=dash),
                                    showlegend=False))

#------------------------------Collecte des données------------------------------

# Collecte des paramètres nécessaire
parser = argparse.ArgumentParser(description='Process some data files and columns.')
parser.add_argument('-min','--min_date', type=int, default=3, help='Minimum date difference for connections')
parser.add_argument('-max','--max_date', type=int, default=6, help='Maximum date difference for connections')
parser.add_argument('-d','--death_file', type=str, help='Path for deaths file')
parser.add_argument('-i','--inhumation_file', type=str, help='Path for inhumations file')
parser.add_argument('-n','--necropsy_file', type=str, help='Path for necropsies file')

args = parser.parse_args()

required_args = ['min_date', 'max_date', 'death_file', 'inhumation_file', 'necropsy_file']
missing_args = [arg for arg in required_args if not getattr(args, arg)]

if missing_args:
    parser.error(f"The following required arguments are missing: {', '.join(missing_args)}")

# Création des dataframes
death_dataframe = create_dataframe('Death', args.death_file, 'FECHA_MUERTE', 'SEXO', 'ID_CNI')
necropsy_dataframe = create_dataframe('Necropsy', args.necropsy_file, 'FECHA NECROPSIA', 'SEXO', 'ID_CNI')
inhumation_dataframe = create_dataframe('Inhumation', args.inhumation_file, 'FECHA_INHUMACION', 'SEXO', 'ID_CEMENTERIO')

#------------------------------Fonction principale------------------------------

def main():
    
    matching_death_necropsy_data = get_matching_data(death_dataframe, necropsy_dataframe, '+', [])
    matching_necropsy_inhumation_data = get_matching_data(necropsy_dataframe, inhumation_dataframe, '+', [])

    #------------------------------Extraction des données------------------------------
                    
    create_csv('matching_death_necropsy_data.csv', matching_death_necropsy_data)
    create_csv('matching_necropsy_inhumation_data.csv', matching_necropsy_inhumation_data)
    
    #------------------------------Création du tracé------------------------------
    
    fig = go.Figure()

    fig.add_trace(go.Scatter(x = death_dataframe['Date'], y = death_dataframe['Category'], 
                             mode = 'markers', name = 'Death', text = death_dataframe['ID']))
    fig.add_trace(go.Scatter(x = necropsy_dataframe['Date'], y = necropsy_dataframe['Category'],
                             mode = 'markers', name = 'Necropsy', text = necropsy_dataframe['ID']))
    fig.add_trace(go.Scatter(x = inhumation_dataframe['Date'], y = inhumation_dataframe['Category'], 
                             mode = 'markers', name = 'Inhumation', text = inhumation_dataframe['ID']))

    add_matching_data_trace('Necropsy', 'Inhumation', fig, matching_necropsy_inhumation_data, 'blue', 'dot')
    add_matching_data_trace('Death','Necropsy', fig, matching_death_necropsy_data, 'red', 'dot')
        
    fig.update_xaxes(rangeslider_visible=True)
    fig.update_layout(
            title='Dot Plot with Death, Inhumation, and Necropsy Dates',
            yaxis=dict(title='Event Category', showticklabels=True),
            xaxis=dict(title='Date'))
    fig.write_html('dates_analysis.html', auto_open=True)

#-------------------------------------------------------------------------------

if __name__ == "__main__":
    main()
