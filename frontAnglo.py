import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
import matplotlib.pyplot as plt
import io
import openpyxl
import matplotlib.dates as mdates
from wordcloud import WordCloud
import plotly.graph_objs as go


# Função para calcular status automaticamente
def calcular_status(inicio_real, fim_real, inicio_plan, fim_plan, inicio_repro=None, fim_repro=None):
    hoje = pd.to_datetime(datetime.now().date())

    # Certifique-se de que as entradas sejam do tipo Timestamp
    inicio_plan = pd.to_datetime(inicio_plan) if pd.notna(inicio_plan) else pd.NaT
    fim_plan = pd.to_datetime(fim_plan) if pd.notna(fim_plan) else pd.NaT
    inicio_real = pd.to_datetime(inicio_real) if pd.notna(inicio_real) else pd.NaT
    fim_real = pd.to_datetime(fim_real) if pd.notna(fim_real) else pd.NaT
    inicio_repro = pd.to_datetime(inicio_repro) if pd.notna(inicio_repro) else pd.NaT
    fim_repro = pd.to_datetime(fim_repro) if pd.notna(fim_repro) else pd.NaT

    # Verifica se o campo de início planejado está vazio
    if pd.isna(inicio_plan):
        return "_"
    # Atrasada: Início planejado é menor que hoje e fim planejado está vazio
    if pd.isna(fim_plan) and inicio_plan < hoje:
        return "Atrasada"
    # Programada: Início planejado é maior que hoje
    elif pd.isna(fim_plan) and inicio_plan > hoje:
        return "Programada" 
    # Concluída: Fim real não está vazio
    elif not pd.isna(fim_real):
        return "Concluída"
    # Em andamento: Fim real não está vazio e início real é menor que hoje
    elif not pd.isna(fim_real) and inicio_real <= hoje:
        return "Em andamento"
    # Atrasada: Se o início real estiver vazio e a data final planejada estiver no passado
    elif pd.isna(fim_real) and fim_plan < hoje:
        return "Atrasada"
    # Em andamento: Qualquer outro caso
    return "Em andamento"


# Função para garantir que uma coluna é do tipo datetime
def converter_para_datetime(coluna):
    return pd.to_datetime(coluna, errors='coerce')

# Função para carregar e salvar o mapeamento Área-Responsável
def carregar_mapeamento_area_responsavel():
    try:
        df_map = pd.read_csv('area_responsavel.csv')
        mapeamento = dict(zip(df_map['Área'], df_map['Responsável']))
    except FileNotFoundError:
        mapeamento = {
            'Transporte': 'Renan Tales',
            'Infraestrutura': 'Jayr Rodrigues',
            'Desenvolvimento': 'Felipe Zanela',
            'Ventilação': 'Geraldo Duarte',
            'Backlog': 'Osman Pereira',
            'Caldeiraria': 'Darley',
            'ObraCivil': 'Darley',
            'Mec.Rochas': 'Jeferson Lage'
        }
        salvar_mapeamento_area_responsavel(mapeamento)
    return mapeamento

def salvar_mapeamento_area_responsavel(mapeamento):
    df_map = pd.DataFrame(list(mapeamento.items()), columns=['Área', 'Responsável'])
    df_map.to_csv('area_responsavel.csv', index=False)

# Carregar dados
def carregar_dados():
    required_columns = [
        'Area', 'Local', 'Acao', 'Impacto', 'Responsavel', 'Dias', 'Inicio Plan',
        'Fim Plan', 'Inicio Real', 'Fim Real', 'Status', 'Observações', 'Nota de Trabalho',
        'O resultado esperado foi alcançado?', 'Se não, o que será feito?', 'Classificação Impacto', 'Alerta',
        'Corpo', 'Nível', 'Inicio(REPRO)', 'Fim(REPRO)'  # Novas colunas adicionadas
    ]
    try:
        df = pd.read_excel('dados_projeto.xlsx')
        for col in required_columns:
            if col not in df.columns:
                df[col] = None
    except FileNotFoundError:
        df = pd.DataFrame(columns=required_columns)
    
    # Verifica se a coluna 'Area' existe; caso contrário, tenta ajustar ou criar com valor padrão
    if 'Area' not in df.columns:
        if 'Área' in df.columns:  # Verifica se a coluna está com acento
            df.rename(columns={'Área': 'Area'}, inplace=True)
        else:
            st.warning("A coluna 'Area' ou 'Área' não foi encontrada. Uma coluna padrão será criada.")
            df['Area'] = 'Área Padrão'  # Cria uma coluna 'Area' com valor padrão se não existir

    return df

def salvar_dados(df):
    df.to_excel('dados_projeto.xlsx', index=False)

# Inicializando a chave 'dados_formulario' no session_state
if 'dados_formulario' not in st.session_state:
    st.session_state['dados_formulario'] = []

# Inicializando a chave 'corpos' no session_state
if 'corpos' not in st.session_state:
    st.session_state['corpos'] = ['BAL', 'CGA', 'FGS', 'GAL', 'SER']  # Valores padrão

# Carregar o mapeamento de áreas e responsáveis
area_responsavel = carregar_mapeamento_area_responsavel()

df = carregar_dados()

# Convertendo colunas para datetime
df['Inicio Plan'] = converter_para_datetime(df['Inicio Plan'])
df['Fim Plan'] = converter_para_datetime(df['Fim Plan'])
df['Inicio Real'] = converter_para_datetime(df['Inicio Real'])
df['Fim Real'] = converter_para_datetime(df['Fim Real'])
df['Inicio(REPRO)'] = converter_para_datetime(df['Inicio(REPRO)'])  # Nova coluna
df['Fim(REPRO)'] = converter_para_datetime(df['Fim(REPRO)'])  # Nova coluna


st.title('Sistema de Gestão - Plano de Ação')

tab1, tab2, tab3, tab4 = st.tabs(["CADASTRO", "TABELAS", "GRÁFICOS", "CONFIGURAÇÕES"])

with tab1:
    st.subheader("Cadastro de Ação")
    with st.form("formulario_acao"):
        col1, col2, col3 = st.columns(3)
        
        # Mapeamento de Área e Responsável
        area_responsavel_map = {
            'Transporte': 'Renan Tales',
            'Infraestrutura': 'Jayr Rodrigues',
            'Desenvolvimento': 'Felipe Zanela',
            'Ventilação': 'Geraldo Duarte',
            'Backlog': 'Osman Pereira',
            'Caldeiraria': 'Darley',
            'ObraCivil': 'Darley',
            'Mec.Rochas': 'Jeferson Lage'
        }

        with col1:
            area = st.selectbox("Área", options=list(area_responsavel_map.keys()))  # Usando selectbox para Área
        with col2:
            local = st.text_input("Local")
        with col3:
            acao = st.text_input("Ação (O que)")

        # Adicionando um campo para o Status com opção vazia
        status_opcoes = [''] + ['Concluída', 'Atrasada', 'Em andamento', 'Programada', '-']  # Opção vazia adicionada

        col4, col5 = st.columns(2)
        with col4:
            novo_corpo = st.text_input("Adicionar Corpo (deixe vazio para manter o existente)")
        with col5:
            status_preenchido = st.selectbox("Status", options=status_opcoes)  # Opção vazia adicionada

        col6, col7, col8 = st.columns(3)
        with col6:
            corpo = st.selectbox("Corpo", options=st.session_state['corpos'])
        with col7:
            nivel = st.selectbox("Nível", options=[f'N{n}' for n in range(1, 51)])
        with col8:
            impacto = st.text_input("Impacto")

        # Responsável é preenchido automaticamente com base na área selecionada
        responsavel = area_responsavel_map[area]  # Obtém o responsável com base na área selecionada

        col9, col10, col11 = st.columns(3)
        with col9:
            st.text_input("Responsável", value=responsavel, disabled=True)  # Campo de responsável preenchido e desabilitado
        with col10:
            inicio_planejado = st.date_input("Início Planejado", value=None, format="DD/MM/YYYY")
        with col11:
            fim_planejado = st.date_input("Fim Planejado", value=None, format="DD/MM/YYYY")

        col12, col13 = st.columns(2)
        with col12:
            inicio_real = st.date_input("Início Real", value=None, format="DD/MM/YYYY")
        with col13:
            fim_real = st.date_input("Fim Real", value=None, format="DD/MM/YYYY")

        # Novos campos para Inicio(REPRO) e Fim(REPRO)
        col14, col15, col16 = st.columns(3)
        with col14:
            inicio_repro = st.date_input("Início(REPRO)", value=None, format="DD/MM/YYYY")
        with col15:
            fim_repro = st.date_input("Fim(REPRO)", value=None, format="DD/MM/YYYY")

        with col16:
            nota_trabalho = st.text_input("Nota de Trabalho")

        observacoes = st.text_area("Observações", height=150)
        resultado_esperado = st.text_area("O resultado esperado foi alcançado?", height=150)
        se_nao_o_que_fazer = st.text_area("Se não, o que será feito?", height=150)
        
        submit = st.form_submit_button("Gravar")

        if submit:
            corpo_final = novo_corpo if novo_corpo else corpo  # Usa o novo corpo se fornecido, caso contrário, usa o corpo selecionado
            
            # Se um novo corpo for fornecido, adiciona à lista de corpos
            if novo_corpo and novo_corpo not in st.session_state['corpos']:
                st.session_state['corpos'].append(novo_corpo)

            # Se o status estiver preenchido, usa esse valor; caso contrário, calcula usando a lógica existente
            if status_preenchido:  # Se não for vazio
                status = status_preenchido  # O usuário preencheu o status
            else:
                status = calcular_status(
                    pd.to_datetime(inicio_real) if pd.notna(inicio_real) else pd.NaT,
                    pd.to_datetime(fim_real) if pd.notna(fim_real) else pd.NaT,
                    pd.to_datetime(inicio_planejado) if pd.notna(inicio_planejado) else pd.NaT,
                    pd.to_datetime(fim_planejado) if pd.notna(fim_planejado) else pd.NaT,
                    pd.to_datetime(inicio_repro) if pd.notna(inicio_repro) else pd.NaT,
                    pd.to_datetime(fim_repro) if pd.notna(fim_repro) else pd.NaT
                )

            novo_dado = {
                'Area': area,
                'Local': local,
                'Acao': acao,
                'Corpo': corpo_final,  # Usa o corpo final
                'Nível': nivel,
                'Impacto': impacto,
                'Responsavel': responsavel,
                'Inicio Plan': inicio_planejado,
                'Fim Plan': fim_planejado,
                'Inicio Real': inicio_real,
                'Fim Real': fim_real,
                'Inicio(REPRO)': inicio_repro,
                'Fim(REPRO)': fim_repro,
                'Observações': observacoes,
                'Nota de Trabalho': nota_trabalho,
                'O resultado esperado foi alcançado?': resultado_esperado,
                'Se não, o que será feito?': se_nao_o_que_fazer,
                'Status': status  # Armazenando o status aqui
            }
            
            # Adiciona o novo registro na tabela de dados
            st.session_state['dados_formulario'].append(novo_dado)
            st.success("Informações enviadas com sucesso!")

# Aba 2: TABELAS
with tab2:
    st.subheader("Tabela de Acompanhamento")
    
    # Exibe os dados cadastrados
    if 'dados_formulario' in st.session_state and st.session_state['dados_formulario']:
        df = pd.DataFrame(st.session_state['dados_formulario'])

        # Certifique-se de que as colunas de data estão no formato datetime
        df['Inicio Plan'] = converter_para_datetime(df['Inicio Plan'])
        df['Inicio Real'] = converter_para_datetime(df['Inicio Real'])
        df['Fim Plan'] = converter_para_datetime(df['Fim Plan'])
        df['Fim Real'] = converter_para_datetime(df['Fim Real'])

        df['Status'] = df.apply(lambda row: calcular_status(
        pd.to_datetime(row['Inicio Real']) if pd.notna(row['Inicio Real']) else pd.NaT,
        pd.to_datetime(row['Fim Real']) if pd.notna(row['Fim Real']) else pd.NaT,
        pd.to_datetime(row['Inicio Plan']) if pd.notna(row['Inicio Plan']) else pd.NaT,
        pd.to_datetime(row['Fim Plan']) if pd.notna(row['Fim Plan']) else pd.NaT
        ), axis=1)

        df['Status'] = df.apply(lambda row: calcular_status(
            row['Inicio Real'], 
            row['Fim Real'], 
            row['Inicio Plan'],  # Passa o valor de Inicio Plan
            row['Fim Plan']      # Passa o valor de Fim Plan
        ), axis=1)

        # Adicionar a coluna 'Semana do Ano' baseada na coluna 'Inicio Plan'
        df['Semana do Ano'] = df['Inicio Plan'].dt.isocalendar().week

        # Filtro de área
        area_filtro = st.selectbox("Filtrar por Área", options=['Todas'] + list(area_responsavel.keys()))
        
        if area_filtro != 'Todas':
            df = df[df['Area'] == area_filtro]

        # Exibe a tabela com cabeçalho vermelho
        st.markdown("<style>th {color: red;}</style>", unsafe_allow_html=True)
        st.dataframe(df)

        # Calcular a última e a próxima semana
        hoje = datetime.now()
        ultima_semana = hoje.isocalendar()[1] - 1  # Última semana do ano
        proxima_semana = hoje.isocalendar()[1] + 1  # Próxima semana do ano
        
        # Filtrando apenas os dados da última semana passada
        df_ultima_semana = df[df['Semana do Ano'] == ultima_semana]

        # Exibe a tabela da última semana
        #st.markdown("<style>th {color: red;}</style>", unsafe_allow_html=True)
        #st.subheader("Tabela da Última Semana Passada")
        #st.dataframe(df_ultima_semana)

        # Filtrando apenas os dados da próxima semana
        df_proxima_semana = df[df['Semana do Ano'] == proxima_semana]

        # Exibe a tabela da próxima semana
        #st.subheader("Tabela da Próxima Semana")
        #st.dataframe(df_proxima_semana)
    else:
        st.write("Nenhum dado cadastrado ainda.")

    # Edição de Registros Existentes
    with st.expander("Editar Registros Existentes", expanded=False):
        st.subheader("Editar Registros Existentes")

        if 'dados_formulario' in st.session_state and st.session_state['dados_formulario']:
            indices_disponiveis = list(range(len(st.session_state['dados_formulario'])))
            registro_selecionado = st.selectbox("Selecione o número do registro para editar", indices_disponiveis, key='registro_editar')
            st.subheader(f"Editando registro #{registro_selecionado}")

            # Obter dados do registro selecionado
            registro_data = st.session_state['dados_formulario'][registro_selecionado]

            area_options = list(area_responsavel.keys())
            area_value = registro_data['Area']
            area_index = area_options.index(area_value) if area_value in area_options else 0

            area_edit = st.selectbox('Área', options=area_options, index=area_index)
            responsavel_edit = st.text_input("Responsável", value=registro_data['Responsavel'])
            local_edit = st.text_input('Local', value=registro_data['Local'])
            acao_edit = st.text_input('Ação (O que)', value=registro_data['Acao'])
            impacto_edit = st.text_area('Impacto', value=registro_data['Impacto'])
            inicio_plan_edit = st.date_input('Início Planejado', value=registro_data['Inicio Plan'], key='inicio_plan_edit')
            fim_plan_edit = st.date_input('Fim Planejado', value=registro_data['Fim Plan'], key='fim_plan_edit')
            inicio_real_edit = st.date_input('Início Real (opcional)', value=registro_data['Inicio Real'] if pd.notna(registro_data['Inicio Real']) else None, key='inicio_real_edit')
            fim_real_edit = st.date_input('Fim Real (opcional)', value=registro_data['Fim Real'] if pd.notna(registro_data['Fim Real']) else None, key='fim_real_edit')

            # Novos campos para editar
            inicio_repro_edit = st.date_input('Início(REPRO)', value=registro_data['Inicio(REPRO)'] if pd.notna(registro_data['Inicio(REPRO)']) else None, key='inicio_repro_edit')
            fim_repro_edit = st.date_input('Fim(REPRO)', value=registro_data['Fim(REPRO)'] if pd.notna(registro_data['Fim(REPRO)']) else None, key='fim_repro_edit')

            nivel_edit = st.selectbox('Nível', options=[f'N{n}' for n in range(1, 51)], index=int(registro_data['Nível'][1:]))
            
            # Selectbox para alterar o status manualmente
            status_opcoes = [''] + ['Concluída', 'Atrasada', 'Em andamento', 'Programada', '-']  # Opção vazia adicionada
            status_preenchido = st.selectbox("Status", options=status_opcoes)  # O padrão é um campo vazio

            observacoes_edit = st.text_area("Observações", value=registro_data['Observações'] if pd.notna(registro_data['Observações']) else '')
            nota_trabalho_edit = st.text_area("Nota de Trabalho", value=registro_data['Nota de Trabalho'] if pd.notna(registro_data['Nota de Trabalho']) else '')

            resultado_esperado = registro_data['O resultado esperado foi alcançado?'] if pd.notna(registro_data['O resultado esperado foi alcançado?']) else 'Sim'  # Valor padrão
            opcoes_resultado = ['Sim', 'Não', 'Parcialmente']

            if resultado_esperado not in opcoes_resultado:
                resultado_esperado = 'Sim'  # Ou qualquer valor padrão que você desejar

            index = opcoes_resultado.index(resultado_esperado)

            opcoes_resultado = ['SIM', 'NÃO']
            resultado_esperado_alcancado_edit = st.selectbox(
                "O resultado esperado foi alcançado?",
                opcoes_resultado,
                index=0  # Definindo "SIM" como padrão
            )

            if st.button("Atualizar Registro"):
                # Validação das datas
                if inicio_plan_edit and fim_plan_edit and inicio_plan_edit > fim_plan_edit:
                    st.error("A data de início planejado não pode ser após a data de fim planejado.")
                elif inicio_real_edit and fim_real_edit and inicio_real_edit > fim_real_edit:
                    st.error("A data de início real não pode ser após a data de fim real.")
                elif not responsavel_edit:
                    st.error("O campo de responsável não pode estar vazio.")
                else:
                    # Atualiza os dados no DataFrame original
                    st.session_state['dados_formulario'][registro_selecionado]['Area'] = area_edit
                    st.session_state['dados_formulario'][registro_selecionado]['Responsavel'] = responsavel_edit
                    st.session_state['dados_formulario'][registro_selecionado]['Local'] = local_edit
                    st.session_state['dados_formulario'][registro_selecionado]['Acao'] = acao_edit
                    st.session_state['dados_formulario'][registro_selecionado]['Impacto'] = impacto_edit
                    st.session_state['dados_formulario'][registro_selecionado]['Inicio Plan'] = inicio_plan_edit
                    st.session_state['dados_formulario'][registro_selecionado]['Fim Plan'] = fim_plan_edit
                    st.session_state['dados_formulario'][registro_selecionado]['Inicio Real'] = inicio_real_edit
                    st.session_state['dados_formulario'][registro_selecionado]['Fim Real'] = fim_real_edit
                    st.session_state['dados_formulario'][registro_selecionado]['Inicio(REPRO)'] = inicio_repro_edit  # Atualiza o novo campo
                    st.session_state['dados_formulario'][registro_selecionado]['Fim(REPRO)'] = fim_repro_edit  # Atualiza o novo campo
                    st.session_state['dados_formulario'][registro_selecionado]['Observações'] = observacoes_edit
                    st.session_state['dados_formulario'][registro_selecionado]['Nota de Trabalho'] = nota_trabalho_edit
                    st.session_state['dados_formulario'][registro_selecionado]['Nível'] = nivel_edit  # Atualiza o campo Nível
                    st.session_state['dados_formulario'][registro_selecionado]['O resultado esperado foi alcançado?'] = resultado_esperado_alcancado_edit

                    # Atualiza o status com base no selectbox
                    if status_preenchido:  # Se o usuário selecionou um status
                        st.session_state['dados_formulario'][registro_selecionado]['Status'] = status_preenchido
                    else:  # Caso contrário, calcula o status
                        st.session_state['dados_formulario'][registro_selecionado]['Status'] = calcular_status(
                            st.session_state['dados_formulario'][registro_selecionado]['Inicio Real'],
                            st.session_state['dados_formulario'][registro_selecionado]['Fim Real'],
                            st.session_state['dados_formulario'][registro_selecionado]['Inicio Plan'],
                            st.session_state['dados_formulario'][registro_selecionado]['Fim Plan'],
                            st.session_state['dados_formulario'][registro_selecionado]['Inicio(REPRO)'],
                            st.session_state['dados_formulario'][registro_selecionado]['Fim(REPRO)']
                        )

                    # Salva as alterações no arquivo
                    salvar_dados(pd.DataFrame(st.session_state['dados_formulario']))
                    st.success("Registro atualizado com sucesso!")
        else:
            st.info("Não há registros para editar.")



# Gráficos
with tab3:
    st.subheader("Gráficos")

    if 'dados_formulario' in st.session_state and st.session_state['dados_formulario']:
        df = pd.DataFrame(st.session_state['dados_formulario'])
        
        # Convertendo as colunas de data para datetime
        df['Inicio Plan'] = pd.to_datetime(df['Inicio Plan'], errors='coerce')
        df['Fim Plan'] = pd.to_datetime(df['Fim Plan'], errors='coerce')
        df['Fim Real'] = pd.to_datetime(df['Fim Real'], errors='coerce')
        df['Fim(REPRO)'] = pd.to_datetime(df['Fim(REPRO)'], errors='coerce')

        data_inicio = df['Inicio Plan'].dropna().min()
        data_fim = df['Fim Plan'].dropna().max()

        if pd.isna(data_inicio) or pd.isna(data_fim):
            st.warning("As datas de início ou fim planejadas não estão disponíveis. Os gráficos não podem ser criados.")
        else:
            datas = pd.date_range(start=data_inicio, end=data_fim)

    if not df.empty:
        data_inicio = df['Inicio Plan'].min()
        data_fim = df['Fim Plan'].max()

        if pd.isna(data_inicio) or pd.isna(data_fim):
            st.warning("As datas de início ou fim planejadas não estão disponíveis. Os gráficos não podem ser criados.")
        else:
            datas = pd.date_range(start=data_inicio, end=data_fim)

            progresso_planejado = [
                df[df['Fim Plan'].notna() & (df['Fim Plan'] <= data)].shape[0] for data in datas
            ]
            progresso_real = [
                df[df['Fim Real'].notna() & (df['Fim Real'] <= data)].shape[0] for data in datas
            ]
            progresso_reprogramado = [
                df[df['Fim(REPRO)'].notna() & (df['Fim(REPRO)'] <= data)].shape[0] for data in datas
            ]

            fig_s = go.Figure()

            # Adicionando as linhas planejadas
            fig_s.add_trace(go.Scatter(
                x=datas, 
                y=progresso_planejado, 
                mode='lines+markers', 
                name='Planejado', 
                line=dict(color='black'),
                marker=dict(symbol='circle', size=6)
            ))

            # Adicionando as linhas reais
            fig_s.add_trace(go.Scatter(
                x=datas, 
                y=progresso_real, 
                mode='lines+markers', 
                name='Real', 
                line=dict(color='orange'),
                marker=dict(symbol='circle', size=6)
            ))

            # Adicionando a linha reprogramada
            fig_s.add_trace(go.Scatter(
                x=datas, 
                y=progresso_reprogramado, 
                mode='lines+markers', 
                name='Reprogramado', 
                line=dict(color='red'),
                marker=dict(symbol='circle', size=6)
            ))

            # Adicionando a linha vertical para "Hoje"

            # Verificando se há valores em progresso_planejado, progresso_real e progresso_reprogramado
            y_max = max(
                max(progresso_planejado) if progresso_planejado else 0,
                max(progresso_real) if progresso_real else 0,
                max(progresso_reprogramado) if progresso_reprogramado else 0
            )

            hoje = pd.Timestamp(datetime.now().date())

            # Calcular o progresso até hoje
            progresso_hoje = [
                df[df['Fim Plan'].notna() & (df['Fim Plan'] <= hoje)].shape[0],
                df[df['Fim Real'].notna() & (df['Fim Real'] <= hoje)].shape[0],
                df[df['Fim(REPRO)'].notna() & (df['Fim(REPRO)'] <= hoje)].shape[0]
            ]

            # Adicionando a linha "Hoje" ao gráfico
            fig_s.add_trace(go.Scatter(
                x=[hoje], 
                y=[progresso_hoje[0]],  # Para o status "Planejado"
                mode='markers', 
                name='Hoje', 
                marker=dict(color='grey', size=6)  # Escolha uma cor para destacar
            ))

            # Configurando o layout do gráfico de Curva S
            fig_s.update_layout(
                title="Curva S - Progresso Cumulativo (Planejado vs Real vs Reprogramado)",
                xaxis_title="Data",
                yaxis_title="Progresso (%)",
                xaxis=dict(tickformat='%d/%m/%Y'),
                legend=dict(x=0, y=1, bgcolor='rgba(0,0,0,0)'),
                hovermode="x unified"
            )

            fig_s.update_yaxes(range=[0, 100])
            st.plotly_chart(fig_s)
            

            df['Status'] = df.apply(lambda row: calcular_status(
                pd.to_datetime(row['Inicio Real']) if pd.notna(row['Inicio Real']) else pd.NaT,
                pd.to_datetime(row['Fim Real']) if pd.notna(row['Fim Real']) else pd.NaT,
                pd.to_datetime(row['Inicio Plan']) if pd.notna(row['Inicio Plan']) else pd.NaT,
                pd.to_datetime(row['Fim Plan']) if pd.notna(row['Fim Plan']) else pd.NaT
            ), axis=1)

            # Criação de um DataFrame para contagem de registros por status e área
            df_status_area = df.groupby(['Area', 'Status']).size().reset_index(name='Count')

            # Definindo cores para cada área
            cores_area = {
                'Transporte': '#A4450C',  
                'Infraestrutura': '#F66A6B',  
                'Desenvolvimento': '#FF4F72',  
                'Ventilação': '#FBBC00',  
                'Backlog': '#FF6D01',  
                'Caldeiraria': '#ED6B3C',  
                'ObraCivil': '#FF00FF',  
                'Mec.Rochas': '#943134'   
            }

            df_status_area['Color'] = df_status_area['Area'].map(cores_area)

            fig_bar = go.Figure()

            df_soma_area = df_status_area.groupby('Area')['Count'].sum().reset_index()
            soma_area_dict = dict(zip(df_soma_area['Area'], df_soma_area['Count']))

            for area in df_status_area['Area'].unique():
                filtered_df = df_status_area[df_status_area['Area'] == area]
                fig_bar.add_trace(go.Bar(
                    x=filtered_df['Area'],  
                    y=filtered_df['Count'],
                    name=area,  
                    marker_color=cores_area[area],  
                    width=0.4,
                    #hovertemplate=f'Staus: {status}<br>Total: {soma_area_dict[area]}<extra></extra>'
                ))

            fig_bar.update_layout(
                title="Status das Ações (total) - Gráfico Empilhado",
                xaxis_title="Status",
                yaxis_title="Quantidade de Cadastros",
                barmode='stack',
                legend_title_text="Área",
                height=600,
                legend=dict(
                    x=1,  # Mover a legenda para fora do gráfico à direita
                    y=1,  # Posicionar no topo do gráfico
                    traceorder='normal',
                    orientation='v'  # Orientação vertical
                )
            )
            st.plotly_chart(fig_bar)
        
            if 'Status' not in df.columns:
                df['Status'] = df.apply(lambda row: calcular_status(
                    pd.to_datetime(row['Inicio Real']) if pd.notna(row['Inicio Real']) else pd.NaT,
                    pd.to_datetime(row['Fim Real']) if pd.notna(row['Fim Real']) else pd.NaT,
                    pd.to_datetime(row['Inicio Plan']) if pd.notna(row['Inicio Plan']) else pd.NaT,
                    pd.to_datetime(row['Fim Plan']) if pd.notna(row['Fim Plan']) else pd.NaT
                ), axis=1)

            status_counts = df['Status'].value_counts()

            # Contando a quantidade de cada status, excluindo o status "-"
            status_counts = status_counts[status_counts.index != '_']

            # Dicionário de cores padrão para os status
            cores_status = {
                'Concluída': '#FBBC00',  # Azul
                'Atrasada': '#943134',   # Vermelho
                'Em andamento': '#FF6D01', # Laranja
                'Programada': '#ED6B3C'   # Verde
            }

            # Criando o gráfico de pizza
            fig_pizza = go.Figure(data=[go.Pie(
                labels=status_counts.index, 
                values=status_counts.values, 
                marker=dict(colors=[cores_status[status] for status in status_counts.index])
            )])

            # Atualizando o layout do gráfico
            fig_pizza.update_layout(
                title="Distribuição Percentual dos Status das Ações",
                legend_title="Status",
                height=400,
                showlegend=True
            )

            # Exibindo o gráfico
            st.plotly_chart(fig_pizza)

                    # Tabela de últimos 10 registros atrasados
            st.subheader("Últimos 10 Registros Atrasados")

            # Filtrando registros atrasados
            registros_atrasados = df[df['Status'] == 'Atrasada']

            # Ordenar pelos mais atrasados
            registros_atrasados = registros_atrasados.sort_values(by='Fim Plan', ascending=True)

            # Selecionar os últimos 10
            ultimos_10_atrasados = registros_atrasados.head(10)

                    # Adicionar a coluna 'Semana do Ano' baseada na coluna 'Inicio Plan'
            df['Semana do Ano'] = df['Inicio Plan'].dt.isocalendar().week

            # Exibir a tabela se houver registros atrasados
            if not ultimos_10_atrasados.empty:
                st.dataframe(ultimos_10_atrasados)
            else:
                st.write("Não há registros atrasados.")

            # Calcular a última e a próxima semana
            hoje = datetime.now()
            ultima_semana = hoje.isocalendar()[1] - 1  # Última semana do ano
            proxima_semana = hoje.isocalendar()[1] + 1  # Próxima semana do ano
            
            # Filtrando apenas os dados da última semana passada
            df_ultima_semana = df[df['Semana do Ano'] == ultima_semana]

            # Exibe a tabela da última semana
            st.markdown("<style>th {color: red;}</style>", unsafe_allow_html=True)
            st.subheader("Tabela da Última Semana Passada")
            st.dataframe(df_ultima_semana)

            # Filtrando apenas os dados da próxima semana
            df_proxima_semana = df[df['Semana do Ano'] == proxima_semana]

            # Exibe a tabela da próxima semana
            st.subheader("Tabela da Próxima Semana")
            st.dataframe(df_proxima_semana)

            # Função para exibir as porcentagens de atividades e de impacto em cartões aprimorados
            def exibir_resumo_atividades(df):
                total_atividades = df.shape[0]
                
                # Calcula o total de atividades concluídas
                atividades_concluidas = df[df['Status'] == 'Concluída'].shape[0]
                
                # Verifica se não há atividades concluídas
                if total_atividades == 0:
                    porcentagem_planejada = 0.0
                    porcentagem_concluida = 0.0
                elif atividades_concluidas == 0:
                    porcentagem_planejada = 100.0  # Se nenhuma atividade for concluída, 100% planejadas
                    porcentagem_concluida = 0.0
                else:
                    # Se houver atividades concluídas, calcula as porcentagens
                    porcentagem_planejada = 100.0  # Mantém 100% planejada
                    porcentagem_concluida = (atividades_concluidas / total_atividades * 100)

                # Cálculo de atividades com e sem impacto
                atividades_com_impacto = df[df['Impacto'].notna() & (df['Impacto'] != '')].shape[0]
                atividades_sem_impacto = total_atividades - atividades_com_impacto

                if total_atividades > 0:
                    porcentagem_impacto = (atividades_com_impacto / total_atividades * 100)
                    porcentagem_sem_impacto = (atividades_sem_impacto / total_atividades * 100)
                else:
                    porcentagem_impacto = porcentagem_sem_impacto = 0.0

                # Criando os cartões com st.columns() para distribuir o layout com cores
                col1, col2, col3 = st.columns(3)

                # Cartão para atividades planejadas (com cor)
                col1, col2, col3 = st.columns(3)

                # Cartão para atividades planejadas (com cor)
                with col1:
                    st.markdown(
                        """
                        <div style="background-color:#E8F8F5;padding:10px;border-radius:10px;text-align:center;margin-bottom:15px">
                            <h3 style="color:#1ABC9C">Planejadas</h3>
                            <h1 style="color:#1ABC9C">{:.0f}%</h1>
                        </div>
                        """.format(porcentagem_planejada), unsafe_allow_html=True
                    )

                # Cartão para atividades concluídas (com cor)
                with col2:
                    st.markdown(
                        """
                        <div style="background-color:#FCF3CF;padding:10px;border-radius:10px;text-align:center;margin-bottom:15px">
                            <h3 style="color:#F39C12">Concluídas</h3>
                            <h1 style="color:#F39C12">{:.0f}%</h1>
                        </div>
                        """.format(porcentagem_concluida), unsafe_allow_html=True
                    )

                # Cartão para atividades com impacto (com cor)
                with col3:
                    st.markdown(
                        """
                        <div style="background-color:#FDEDEC;padding:10px;border-radius:10px;text-align:center;margin-bottom:15px">
                            <h3 style="color:#E74C3C">Com Impacto</h3>
                            <h1 style="color:#E74C3C">{:.0f}%</h1>
                        </div>
                        """.format(porcentagem_impacto), unsafe_allow_html=True
                    )

                # Cartões para atividades sem impacto e total de atividades
                col4, col5 = st.columns(2)

                with col4:
                    st.markdown(
                        """
                        <div style="background-color:#F6F6F6;padding:10px;border-radius:10px;text-align:center;margin-bottom:15px">
                            <h3 style="color:#7F8C8D">Sem Impacto</h3>
                            <h1 style="color:#7F8C8D">{:.0f}%</h1>
                        </div>
                        """.format(porcentagem_sem_impacto), unsafe_allow_html=True
                    )

                with col5:
                    st.markdown(
                        """
                        <div style="background-color:#D5DBDB;padding:10px;border-radius:10px;text-align:center;margin-bottom:15px">
                            <h3 style="color:#566573">Total de Atividades</h3>
                            <h1 style="color:#566573">{}</h1>
                        </div>
                        """.format(total_atividades), unsafe_allow_html=True
                    )


            # Chamar a função para exibir os cartões estilizados
            exibir_resumo_atividades(df)

# Função para carregar os responsáveis de um arquivo ou criar lista padrão
def carregar_responsaveis():
    try:
        with open('responsaveis.txt', 'r') as file:
            responsaveis = file.read().splitlines()
    except FileNotFoundError:
        # Caso o arquivo não exista, cria uma lista padrão de responsáveis
        responsaveis = ['Renan Tales', 'Felipe Zanela', 'Jayr Rodrigues', 'Geraldo Duarte', 'Osman Pereira', 'Darley', 'Jeferson Lage']
    return responsaveis

def salvar_responsaveis(responsaveis):
    with open('responsaveis.txt', 'w') as file:
        for responsavel in responsaveis:
            file.write(f"{responsavel}\n")

# Inicializando a lista de responsáveis
responsaveis = carregar_responsaveis()

# Aba 4: CONFIGURAÇÕES
with tab4:
    st.subheader("Configurações")
    st.write("Gerenciar configurações, áreas e responsáveis.")
    with st.expander("Gerenciar Áreas e Responsáveis"):
        st.write("Mapeamento Atual:")
        df_mapeamento = pd.DataFrame(list(area_responsavel.items()), columns=['Área', 'Responsável'])
        st.table(df_mapeamento)

        nova_area = st.text_input("Nova Área")
        novo_responsavel = st.selectbox("Responsável", options=responsaveis)  # Usar 'responsaveis'
        if st.button("Adicionar Mapeamento"):
            if nova_area and novo_responsavel:
                if nova_area not in area_responsavel:
                    area_responsavel[nova_area] = novo_responsavel
                    salvar_mapeamento_area_responsavel(area_responsavel)
                    st.success(f"Mapeamento '{nova_area}' -> '{novo_responsavel}' adicionado!")
                else:
                    st.error(f"A área '{nova_area}' já existe.")
            else:
                st.error("Preencha todos os campos.")

    st.write("**Editar Mapeamento Existente**")
    area_para_editar = st.selectbox("Selecione a Área para editar", options=list(area_responsavel.keys()), key='area_editar_mapeamento')
    if area_para_editar:
        responsavel_atual = area_responsavel[area_para_editar]

        # Verifica se o responsável atual está na lista de responsáveis e define o índice correto
        if responsavel_atual in responsaveis:
            responsavel_index = responsaveis.index(responsavel_atual)
        else:
            responsavel_index = 0  # Usa o primeiro índice se o responsável atual não for encontrado

        # Cria o selectbox com o índice padrão ou o índice encontrado
        novo_responsavel_editar = st.selectbox(
            "Novo Responsável", options=responsaveis, index=responsavel_index, key='novo_responsavel_editar_mapeamento'
        )

        if st.button("Atualizar Mapeamento"):
            area_responsavel[area_para_editar] = novo_responsavel_editar
            salvar_mapeamento_area_responsavel(area_responsavel)
            st.success(f"Mapeamento '{area_para_editar}' atualizado para Responsável '{novo_responsavel_editar}'.")

    st.write("**Excluir Mapeamento**")
    area_para_excluir = st.selectbox("Selecione a Área para excluir o mapeamento", options=list(area_responsavel.keys()), key='area_excluir_mapeamento')
    if st.button("Excluir Mapeamento"):
        if area_para_excluir:
            del area_responsavel[area_para_excluir]
            salvar_mapeamento_area_responsavel(area_responsavel)
            st.success(f"Mapeamento da Área '{area_para_excluir}' excluído com sucesso!")
        else:
            st.error("Selecione uma Área válida para excluir.")


buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
    df.to_excel(writer, index=False)

st.download_button(
    label="Baixar dados em Excel",
    data=buffer.getvalue(),
    file_name="dados_projeto.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)