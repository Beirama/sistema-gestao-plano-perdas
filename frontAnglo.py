import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
import matplotlib.pyplot as plt
import io
import openpyxl
import matplotlib.dates as mdates
from wordcloud import WordCloud
import plotly.graph_objs as go

st.markdown(
    """
    <style>
    th {
        color: red !important;
    }
    </style>
    """, unsafe_allow_html=True
)

# Função para calcular status automaticamente
def calcular_status(inicio_real, fim_real, data_fim_plan):
    hoje = datetime.now().date()

    if isinstance(data_fim_plan, datetime):
        data_fim_plan = data_fim_plan.date()

    if inicio_real and isinstance(inicio_real, datetime):
        inicio_real = inicio_real.date()
    if fim_real and isinstance(fim_real, datetime):
        fim_real = fim_real.date()

    if pd.isna(inicio_real) and data_fim_plan < hoje:
        return "Atrasada"
    elif pd.isna(inicio_real) and data_fim_plan >= hoje:
        return "Programada"
    elif not pd.isna(fim_real):
        return "Concluída"
    elif inicio_real <= hoje and pd.isna(fim_real):
        return "Em andamento"
    else:
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
        'Corpo', 'Nível'
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

# Carregar o mapeamento de áreas e responsáveis
area_responsavel = carregar_mapeamento_area_responsavel()

df = carregar_dados()

# Convertendo colunas para datetime
df['Inicio Plan'] = converter_para_datetime(df['Inicio Plan'])
df['Fim Plan'] = converter_para_datetime(df['Fim Plan'])
df['Inicio Real'] = converter_para_datetime(df['Inicio Real'])
df['Fim Real'] = converter_para_datetime(df['Fim Real'])

st.title('Sistema de Gestão - Plano de Ação')

tab1, tab2, tab3, tab4 = st.tabs(["CADASTRO", "TABELAS", "GRÁFICOS", "CONFIGURAÇÕES"])

# Aba 1: CADASTRO
with tab1:
    st.subheader("Cadastro de Ação")
    with st.form("formulario_acao"):
        col1, col2, col3 = st.columns(3)
        with col1:
            area = st.text_input("Área")  # Usar text_input aqui
        with col2:
            local = st.text_input("Local")
        with col3:
            acao = st.text_input("Ação (O que)")

        col4, col5, col6 = st.columns(3)
        with col4:
            corpo = st.selectbox("Corpo", options=['BAL', 'CGA', 'FGS', 'GAL', 'SER'])
        with col5:
            nivel = st.selectbox("Nível", options=[f'N{n}' for n in range(1, 51)])
        with col6:
            impacto = st.text_input("Impacto")

        col7, col8, col9 = st.columns(3)
        with col7:
            responsavel = st.text_input("Responsável")
        with col8:
            inicio_planejado = st.date_input("Início Planejado", value=datetime.now(), format="DD/MM/YYYY")
        with col9:
            fim_planejado = st.date_input("Fim Planejado", value=datetime.now(), format="DD/MM/YYYY")

        col10, col11, col12 = st.columns(3)
        with col10:
            inicio_real = st.date_input("Início Real", value=datetime.now(), format="DD/MM/YYYY")
        with col11:
            fim_real = st.date_input("Fim Real", value=datetime.now(), format="DD/MM/YYYY")
        with col12:
            nota_trabalho = st.text_input("Nota de Trabalho")

        observacoes = st.text_area("Observações", height=150)
        resultado_esperado = st.text_area("O resultado esperado foi alcançado?", height=150)
        proximos_passos = st.text_area("Se não, o que será feito?", height=150)
        submit = st.form_submit_button("Gravar")

        if submit:
            novo_dado = {
                'Area': area, 'Local': local, 'Acao': acao, 'Corpo': corpo, 'Nível': nivel,
                'Impacto': impacto, 'Responsavel': responsavel, 'Inicio Plan': inicio_planejado,
                'Fim Plan': fim_planejado, 'Inicio Real': inicio_real, 'Fim Real': fim_real,
                'Observações': observacoes, 'Nota de Trabalho': nota_trabalho,
                'O resultado esperado foi alcançado?': resultado_esperado, 'Se não, o que será feito?': proximos_passos
            }
            st.session_state['dados_formulario'].append(novo_dado)
            st.success("Informações enviadas com sucesso!")

# Aba 2: TABELAS
with tab2:
    st.subheader("Tabela de Acompanhamento")
    
    # Exibe os dados cadastrados
    if 'dados_formulario' in st.session_state and st.session_state['dados_formulario']:
        df = pd.DataFrame(st.session_state['dados_formulario'])
        st.dataframe(df)

        # Exibe os registros dos últimos 7 dias
        st.subheader("Registros dos Últimos 7 Dias")
        hoje = datetime.now().date()
        ultima_semana = hoje - timedelta(days=7)

        # Filtra os registros com base na data de Fim Real
        registros_ultimos_7_dias = df[
            (df['Fim Real'] >= ultima_semana) & 
            (df['Fim Real'] <= hoje)
        ]

        if not registros_ultimos_7_dias.empty:
            st.dataframe(registros_ultimos_7_dias)
        else:
            st.info("Nenhum registro foi encontrado nos últimos 7 dias.")
    
    else:
        st.write("Nenhum dado cadastrado ainda.")

# Filtros para visualização
    st.sidebar.subheader("Filtros")
    # Verifique se a coluna 'Status' existe; se não, cria ela
    if 'Status' not in df.columns:
        df['Status'] = df.apply(lambda row: calcular_status(row['Inicio Real'], row['Fim Real'], row['Fim Plan']), axis=1)

    areas_disponiveis = df['Area'].unique()
    filtro_areas = st.sidebar.selectbox("Filtrar por Área", options=areas_disponiveis, key='filtro_areas')
    responsaveis_disponiveis = df[df['Area'] == filtro_areas]['Responsavel'].unique() if filtro_areas else df['Responsavel'].unique()
    filtro_responsaveis = st.sidebar.multiselect("Filtrar por Responsável", options=responsaveis_disponiveis, default=responsaveis_disponiveis, key='filtro_responsaveis')
    status_disponiveis = df['Status'].unique()
    filtro_status = st.sidebar.multiselect("Filtrar por Status", options=status_disponiveis, default=status_disponiveis, key='filtro_status')

    # Aplicar os filtros ao dataframe
    df_filtrado = df[
        (df['Area'] == filtro_areas) &
        (df['Responsavel'].isin(filtro_responsaveis)) &
        (df['Status'].isin(filtro_status))
    ]

    # Verificação de alertas
    def verificar_alerta(row):
        hoje = datetime.now().date()
        if row['Status'] == 'Atrasada':
            return 'Atrasada'
        elif row['Status'] != 'Concluída' and (row['Fim Plan'].date() - hoje).days <= 3:
            return 'Próxima do Vencimento'
        else:
            return ''

    # Verifique se a coluna 'Alerta' existe e, se não existir, crie-a
    if 'Alerta' not in df.columns:
        df['Alerta'] = df.apply(verificar_alerta, axis=1)

    st.subheader("Alertas")
    if not df[df['Alerta'] == 'Atrasada'].empty:
        st.error("Existem ações atrasadas!")
    if not df[df['Alerta'] == 'Próxima do Vencimento'].empty:
        st.warning("Existem ações próximas do vencimento!")

    acoes_alerta = df[df['Alerta'].isin(['Atrasada', 'Próxima do Vencimento'])]
    if not acoes_alerta.empty:
        acoes_alerta_display = acoes_alerta.copy()
        for col in ['Fim Plan']:
            acoes_alerta_display[col] = acoes_alerta_display[col].dt.strftime('%d/%m/%Y')
        st.table(acoes_alerta_display[['Area', 'Acao', 'Responsavel', 'Fim Plan', 'Status', 'Alerta', 'Semana']])
        
    df_filtrado_display = df_filtrado.copy()
    for col in ['Inicio Plan', 'Fim Plan', 'Inicio Real', 'Fim Real']:
        df[col] = pd.to_datetime(df[col], errors='coerce')

    def estilo_status(val):
        cor = ''
        if val == 'Concluída':
            cor = 'background-color: green; color: white;'
        elif val == 'Em andamento':
            cor = 'background-color: orange; color: white;'
        elif val == 'Programada':
            cor = 'background-color: blue; color: white;'
        elif val == 'Atrasada':
            cor = 'background-color: red; color: white;'
        return cor

    df_estilizado = df_filtrado_display.style.applymap(estilo_status, subset=['Status'])
    if not df_filtrado.empty:
        st.dataframe(df_estilizado)
    else:
        st.info("Não há dados para exibir.")

# Edição de Registros Existentes
with st.expander("Editar Registros Existentes"):
    st.subheader("Editar Registros Existentes")

    if not df.empty:
        indices_disponiveis = df.index.tolist()
        registro_selecionado = st.selectbox("Selecione o número do registro para editar", indices_disponiveis, key='registro_editar')
        st.subheader(f"Editando registro #{registro_selecionado}")
        
        area_options = list(area_responsavel.keys())
        area_value = df.loc[registro_selecionado, 'Area']
        if area_value in area_options:
            area_index = area_options.index(area_value)
        else:
            area_index = 0

        area_edit = st.selectbox('Área', options=area_options, index=area_index)

        # Definir o responsável atual e verificar se está na lista de responsáveis
        responsavel_atual = df.loc[registro_selecionado, 'Responsavel']
        
        # Usar uma caixa de texto para entrada de múltiplos responsáveis
        responsaveis_input = st.text_input(
            "Responsável", 
            value=responsavel_atual  # Coloca o responsável atual como valor padrão
        )

        # Processar a entrada para criar uma lista
        responsavel_edit = [r.strip() for r in responsaveis_input.split(',')]  # Remove espaços em branco

        local_edit = st.text_input('Local', df.loc[registro_selecionado, 'Local'])
        acao_edit = st.text_input('Ação (O que)', df.loc[registro_selecionado, 'Acao'])
        impacto_edit = st.text_area('Impacto', df.loc[registro_selecionado, 'Impacto'])
        inicio_plan_edit = st.date_input('Início Planejado', df.loc[registro_selecionado, 'Inicio Plan'])
        fim_plan_edit = st.date_input('Fim Planejado', df.loc[registro_selecionado, 'Fim Plan'])
        inicio_real_edit = st.date_input('Início Real (opcional)', df.loc[registro_selecionado, 'Inicio Real'] if pd.notna(df.loc[registro_selecionado, 'Inicio Real']) else None)
        fim_real_edit = st.date_input('Fim Real (opcional)', df.loc[registro_selecionado, 'Fim Real'] if pd.notna(df.loc[registro_selecionado, 'Fim Real']) else None)

        observacoes_edit = st.text_area("Observações", df.loc[registro_selecionado, 'Observações'] if pd.notna(df.loc[registro_selecionado, 'Observações']) else '')
        nota_trabalho_edit = st.text_area("Nota de Trabalho", df.loc[registro_selecionado, 'Nota de Trabalho'] if pd.notna(df.loc[registro_selecionado, 'Nota de Trabalho']) else '')
        resultado_esperado_alcancado_edit = st.selectbox(
            "O resultado esperado foi alcançado?",
            ['Sim', 'Não', 'Parcialmente'],
            index=['Sim', 'Não', 'Parcialmente'].index(df.loc[registro_selecionado, 'O resultado esperado foi alcançado?']) 
            if pd.notna(df.loc[registro_selecionado, 'O resultado esperado foi alcançado?']) 
            and df.loc[registro_selecionado, 'O resultado esperado foi alcançado?'] in ['Sim', 'Não', 'Parcialmente']
            else 0  # Caso contrário, usar o índice 0 (Sim)
        )

        se_nao_o_que_fazer_edit = st.text_area(
            "Se não, o que será feito?",
            df.loc[registro_selecionado, 'Se não, o que será feito?'] if pd.notna(df.loc[registro_selecionado, 'Se não, o que será feito?']) else ''
        )

        if st.button("Atualizar Registro"):
            # Validação das datas e lógica de atualização
            if inicio_plan_edit > fim_plan_edit:
                st.error("A data de início planejado não pode ser após a data de fim planejado.")
            elif inicio_real_edit and fim_real_edit and inicio_real_edit > fim_real_edit:
                st.error("A data de início real não pode ser após a data de fim real.")
            else:
                # Atualiza os dados no DataFrame original
                df.at[registro_selecionado, 'Area'] = area_edit
                df.at[registro_selecionado, 'Responsavel'] = responsavel_edit
                df.at[registro_selecionado, 'Local'] = local_edit
                df.at[registro_selecionado, 'Acao'] = acao_edit
                df.at[registro_selecionado, 'Impacto'] = impacto_edit
                df.at[registro_selecionado, 'Inicio Plan'] = inicio_plan_edit
                df.at[registro_selecionado, 'Fim Plan'] = fim_plan_edit
                df.at[registro_selecionado, 'Inicio Real'] = inicio_real_edit
                df.at[registro_selecionado, 'Fim Real'] = fim_real_edit
                df.at[registro_selecionado, 'Observações'] = observacoes_edit
                df.at[registro_selecionado, 'Nota de Trabalho'] = nota_trabalho_edit
                df.at[registro_selecionado, 'O resultado esperado foi alcançado?'] = resultado_esperado_alcancado_edit
                df.at[registro_selecionado, 'Se não, o que será feito?'] = se_nao_o_que_fazer_edit

                salvar_dados(df)  # Salva as alterações no arquivo
                st.success("Registro atualizado com sucesso!")
    else:
        st.info("Não há registros para editar.")

with tab3:
    st.subheader("Gráficos")
    if 'dados_formulario' in st.session_state and st.session_state['dados_formulario']:
        df = pd.DataFrame(st.session_state['dados_formulario'])

        # Verifique se a coluna 'Status' existe; se não, cria ela
        if 'Status' not in df.columns:
            df['Status'] = df.apply(lambda row: calcular_status(row['Inicio Real'], row['Fim Real'], row['Fim Plan']), axis=1)

        # Gráfico de porcentagem dos status
        st.subheader("Distribuição dos Status")

        # Contando a quantidade de cada status
        status_counts = df['Status'].value_counts()

        # Calculando as porcentagens
        status_percentages = (status_counts / status_counts.sum()) * 100

        # Cores personalizadas para os status
        cores_status = {
            'Programada': '#FFA500',  # Laranja
            'Em andamento': '#D43F00',  # Vermelho
            'Concluída': '#E8C639',  # Amarelo
            'Atrasada': '#E96D39',  # Roxo
        }

        # Criando o gráfico de pizza com porcentagens
        fig_status = go.Figure(data=[go.Pie(labels=status_counts.index, values=status_counts.values, 
                                            textinfo='label+percent',  # Mostra o rótulo e a porcentagem
                                            hole=.3, 
                                            marker=dict(colors=[cores_status.get(label, 'grey') for label in status_counts.index]))])

        # Configurando o layout do gráfico
        fig_status.update_layout(
            title_text='Distribuição de Status das Ações',
            annotations=[dict(text='Status', x=0.5, y=0.5, font_size=20, showarrow=False)]
        )

        # Renderizando o gráfico de pizza
        st.plotly_chart(fig_status)


        # Continuar com os outros gráficos...
        st.subheader("Curva S - Progresso Cumulativo")
        df_plan = df.copy()
        df_plan['Valor'] = 1
        data_inicio = df_plan['Inicio Plan'].min()
        data_fim = df_plan['Fim Plan'].max()
        datas = pd.date_range(start=data_inicio, end=data_fim)

        # Converter 'Fim Plan' para datetime.date para comparação
        df_plan['Fim Plan'] = df_plan['Fim Plan'].apply(lambda x: x if isinstance(x, date) else x.date() if isinstance(x, datetime) else None)

        progresso_planejado = [df_plan[df_plan['Fim Plan'] <= data.date()].Valor.sum() for data in datas]
        progresso_real = [df_plan[df_plan['Fim Real'].apply(lambda x: pd.Timestamp(x) if pd.notnull(x) else None) <= pd.Timestamp(data)].Valor.sum() for data in datas]

        # Criando o gráfico de Curva S com Plotly
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

        # Configurando o layout do gráfico de Curva S
        fig_s.update_layout(
            title="Curva S - Progresso Cumulativo (Planejado vs Real)",
            xaxis_title="Data",
            yaxis_title="Progresso (%)",
            xaxis=dict(tickformat='%d/%m/%Y'),
            legend=dict(x=0, y=1, bgcolor='rgba(0,0,0,0)'),
            hovermode="x unified"
        )

        # Renderizando o gráfico de Curva S
        st.plotly_chart(fig_s)

        # Gráfico de Barras: Quantidade de Cadastro por Área
        st.subheader("Quantidade de Cadastro por Área")
        
        # Contagem de registros por área
        df['Area'] = df['Area'].str.strip().str.lower()
        area_count = df['Area'].value_counts()

        # Criando o gráfico de barras com Plotly
        fig_bar = go.Figure([go.Bar(x=area_count.index, y=area_count.values, marker_color='#E8C639', width = 0.4)])

        # Configurando o layout do gráfico de barras
        fig_bar.update_layout(
            title="Quantidade de Cadastro por Área",
            xaxis_title="Área",
            yaxis_title="Quantidade de Cadastros",
            xaxis_tickangle=-45
        )

        # Renderizando o gráfico de barras
        st.plotly_chart(fig_bar)

    else:
        st.write("Nenhum dado disponível para gerar gráficos.")

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