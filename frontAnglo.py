import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import openpyxl
import io  # Biblioteca para trabalhar com buffer de memória
import matplotlib.dates as mdates
from wordcloud import WordCloud

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

# Função para classificar o impacto
def classificar_impacto(texto):
    if pd.isnull(texto):
        return 'Indeterminado'
    texto = str(texto).lower()
    if any(palavra in texto for palavra in ['crítico', 'urgente', 'imediato', 'parada']):
        return 'Alto'
    elif any(palavra in texto for palavra in ['significativo', 'moderado', 'atenção']):
        return 'Médio'
    elif any(palavra in texto for palavra in ['mínimo', 'pequeno', 'baixo', 'rotina']):
        return 'Baixo'
    else:
        return 'Indeterminado'

# Funções para carregar e salvar o mapeamento Área-Responsável
def carregar_mapeamento_area_responsavel():
    try:
        df_map = pd.read_csv('area_responsavel.csv')
        mapeamento = dict(zip(df_map['Área'], df_map['Responsável']))
    except FileNotFoundError:
        # Inicializa com o mapeamento padrão
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

# Função para carregar os dados existentes ou criar novos
def carregar_dados():
    required_columns = [
        'Area', 'Local', 'Acao', 'Impacto', 'Responsavel', 'Dias', 'Inicio Plan',
        'Fim Plan', 'Inicio Real', 'Fim Real', 'Status', 'Observações', 'Nota de Trabalho',
        'O resultado esperado foi alcançado?', 'Se não, o que será feito?', 'Classificação Impacto', 'Alerta',
        'Corpo', 'Nível'  # Novas colunas adicionadas
    ]
    try:
        df = pd.read_excel('dados_projeto.xlsx')
        # Garantir que todas as colunas necessárias estejam presentes
        for col in required_columns:
            if col not in df.columns:
                df[col] = None  # ou qualquer valor padrão que faça sentido
    except FileNotFoundError:
        df = pd.DataFrame(columns=required_columns)
    return df

# Função para salvar os dados no Excel
def salvar_dados(df):
    df.to_excel('dados_projeto.xlsx', index=False)

# Carregar lista de responsáveis
def carregar_responsaveis():
    try:
        with open('responsaveis.txt', 'r') as file:
            responsaveis = file.read().splitlines()
    except FileNotFoundError:
        responsaveis = ['Renan Tales', 'Felipe Zanela', 'Jayr Rodrigues', 'Geraldo Duarte',
                        'Osman Pereira', 'Darley', 'Jeferson Lage']
        salvar_responsaveis(responsaveis)
    return responsaveis

# Salvar lista de responsáveis
def salvar_responsaveis(responsaveis):
    with open('responsaveis.txt', 'w') as file:
        for responsavel in responsaveis:
            file.write(f"{responsavel}\n")

# Carregar dados existentes
df = carregar_dados()

# Carregar mapeamento Área-Responsável
area_responsavel = carregar_mapeamento_area_responsavel()

# Carregar responsáveis existentes ou padrão
responsaveis = carregar_responsaveis()

# Converter colunas de data para datetime64[ns]
for col in ['Inicio Plan', 'Fim Plan', 'Inicio Real', 'Fim Real']:
    df[col] = pd.to_datetime(df[col])

# Aplicar a classificação do impacto
if not df.empty:
    if 'Impacto' not in df.columns:
        df['Impacto'] = ''  # ou outro valor padrão
    df['Classificação Impacto'] = df['Impacto'].apply(classificar_impacto)
else:
    df['Classificação Impacto'] = []

# Adicionar coluna 'Semana' baseada na 'Inicio Plan'
df['Semana'] = df['Inicio Plan'].dt.isocalendar().week

# Título do sistema
st.title('Sistema de Gestão - Plano de Ação')

# 1. Colocar "Adicionar Novo Plano de Ação" logo após o título
st.subheader("Adicionar Novo Plano de Ação")

with st.form("formulario"):
    area_options = list(area_responsavel.keys())
    area_default_index = 0
    area = st.selectbox('Área', options=area_options, index=area_default_index)

    # Obter o responsável padrão com base na área selecionada
    default_responsavel = area_responsavel.get(area, '')
    if default_responsavel in responsaveis:
        responsavel_index = responsaveis.index(default_responsavel)
    else:
        responsavel_index = 0

    local = st.text_input('Local', '')
    acao = st.text_input('Ação (O que)', '')
    impacto = st.text_area('Impacto', '')
    responsavel = st.selectbox("Responsável", options=responsaveis, index=responsavel_index)
    inicio_plan = st.date_input('Início Planejado', datetime.now())
    fim_plan = st.date_input('Fim Planejado', datetime.now())
    inicio_real = st.date_input('Início Real (opcional)', value=None)
    fim_real = st.date_input('Fim Real (opcional)', value=None)

    # Novos campos adicionados
    corpos_opcoes = ['BAL', 'CGA', 'FGS', 'GAL', 'SER']
    corpo = st.selectbox('Corpo', options=corpos_opcoes)

    niveis_opcoes = [f'N{n}' for n in range(1, 51)]
    nivel = st.selectbox('Nível', options=niveis_opcoes)

    observacoes = st.text_area("Observações", '')
    nota_trabalho = st.text_area("Nota de Trabalho", '')
    resultado_esperado_alcancado = st.selectbox("O resultado esperado foi alcançado?", ['Sim', 'Não', 'Parcialmente'])
    se_nao_o_que_fazer = st.text_area("Se não, o que será feito?", '')

    submit = st.form_submit_button("Gravar")

if submit:
    # Validação das datas
    if inicio_plan > fim_plan:
        st.error("A data de início planejado não pode ser após a data de fim planejado.")
    elif inicio_real and fim_real and inicio_real > fim_real:
        st.error("A data de início real não pode ser após a data de fim real.")
    elif inicio_real and inicio_real < inicio_plan:
        st.error("A data de início real não pode ser anterior à data de início planejado.")
    elif fim_real and inicio_real and fim_real < inicio_real:
        st.error("A data de fim real não pode ser anterior à data de início real.")
    else:
        # Calcula os dias e status
        dias = (fim_plan - inicio_plan).days + 1
        status = calcular_status(inicio_real, fim_real, fim_plan)
        # Cria nova linha e salva
        nova_linha = pd.DataFrame({
            'Area': [area],
            'Local': [local],
            'Acao': [acao],
            'Impacto': [impacto],
            'Responsavel': [responsavel],
            'Dias': [dias],
            'Inicio Plan': [inicio_plan],
            'Fim Plan': [fim_plan],
            'Inicio Real': [inicio_real],
            'Fim Real': [fim_real],
            'Status': [status],
            'Observações': [observacoes],
            'Nota de Trabalho': [nota_trabalho],
            'O resultado esperado foi alcançado?': [resultado_esperado_alcancado],
            'Se não, o que será feito?': [se_nao_o_que_fazer],
            'Corpo': [corpo],
            'Nível': [nivel],
            'Classificação Impacto': [classificar_impacto(impacto)],
            'Alerta': ['']
        })
        for col in ['Inicio Plan', 'Fim Plan', 'Inicio Real', 'Fim Real']:
            nova_linha[col] = pd.to_datetime(nova_linha[col])
        nova_linha['Semana'] = nova_linha['Inicio Plan'].dt.isocalendar().week
        df = pd.concat([df, nova_linha], ignore_index=True)
        salvar_dados(df)
        st.success("Dados gravados com sucesso!")

# 2. Envolver as seções de mapeamento em expansores para economizar espaço

with st.expander("Gerenciar Áreas e Responsáveis"):
    st.subheader("Gerenciar Áreas e Responsáveis")
    st.write("**Mapeamento Atual:**")
    df_mapeamento = pd.DataFrame(list(area_responsavel.items()), columns=['Área', 'Responsável'])
    st.table(df_mapeamento)

    st.write("**Adicionar Novo Mapeamento Área-Responsável**")
    with st.form("adicionar_mapeamento"):
        nova_area = st.text_input("Nova Área", "")
        novo_responsavel = st.selectbox("Responsável", options=responsaveis, key='novo_responsavel_mapeamento')
        submit_mapeamento = st.form_submit_button("Adicionar Mapeamento")
    if submit_mapeamento:
        if nova_area and novo_responsavel:
            if nova_area in area_responsavel:
                st.error(f"A Área '{nova_area}' já existe no mapeamento.")
            else:
                area_responsavel[nova_area] = novo_responsavel
                salvar_mapeamento_area_responsavel(area_responsavel)
                st.success(f"Mapeamento '{nova_area}' -> '{novo_responsavel}' adicionado com sucesso!")
        else:
            st.error("Por favor, preencha todos os campos para adicionar um novo mapeamento.")

    st.write("**Editar Mapeamento Existente**")
    area_para_editar = st.selectbox("Selecione a Área para editar", options=list(area_responsavel.keys()), key='area_editar_mapeamento')
    if area_para_editar:
        responsavel_atual = area_responsavel[area_para_editar]
        novo_responsavel_editar = st.selectbox("Novo Responsável", options=responsaveis, index=responsaveis.index(responsavel_atual), key='novo_responsavel_editar_mapeamento')
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

with st.expander("Gerenciar Responsáveis"):
    st.subheader("Gerenciar Responsáveis")
    novo_responsavel = st.text_input("Adicionar novo responsável", key='novo_responsavel')
    if st.button("Adicionar Responsável", key='botao_adicionar_responsavel'):
        if novo_responsavel:
            if novo_responsavel in responsaveis:
                st.error(f"O responsável '{novo_responsavel}' já existe.")
            else:
                responsaveis.append(novo_responsavel)
                salvar_responsaveis(responsaveis)
                st.success(f"Responsável '{novo_responsavel}' adicionado com sucesso!")
        else:
            st.error("Por favor, insira um nome válido para o novo responsável.")

    responsavel_selecionado = st.selectbox("Selecione o responsável para editar ou excluir", responsaveis, key='responsavel_selecionado')

    novo_nome_responsavel = st.text_input("Editar nome do responsável", value=responsavel_selecionado, key='novo_nome_responsavel')
    if st.button("Editar Responsável", key='botao_editar_responsavel'):
        if novo_nome_responsavel:
            if novo_nome_responsavel in responsaveis:
                st.error(f"O nome '{novo_nome_responsavel}' já está em uso.")
            else:
                index = responsaveis.index(responsavel_selecionado)
                responsaveis[index] = novo_nome_responsavel
                salvar_responsaveis(responsaveis)
                for area, resp in area_responsavel.items():
                    if resp == responsavel_selecionado:
                        area_responsavel[area] = novo_nome_responsavel
                salvar_mapeamento_area_responsavel(area_responsavel)
                st.success(f"Responsável '{responsavel_selecionado}' atualizado para '{novo_nome_responsavel}'!")
        else:
            st.error("Por favor, insira um nome válido para o responsável.")

    if st.button("Excluir Responsável", key='botao_excluir_responsavel'):
        if responsavel_selecionado:
            responsaveis.remove(responsavel_selecionado)
            salvar_responsaveis(responsaveis)
            areas_para_remover = [area for area, resp in area_responsavel.items() if resp == responsavel_selecionado]
            for area in areas_para_remover:
                del area_responsavel[area]
            salvar_mapeamento_area_responsavel(area_responsavel)
            st.success(f"Responsável '{responsavel_selecionado}' excluído com sucesso!")
        else:
            st.error("Selecione um responsável válido para excluir.")

# Função para verificar alertas
def verificar_alerta(row):
    hoje = datetime.now().date()
    if row['Status'] == 'Atrasada':
        return 'Atrasada'
    elif row['Status'] != 'Concluída' and (row['Fim Plan'].date() - hoje).days <= 3:
        return 'Próxima do Vencimento'
    else:
        return ''

# Adicionar coluna 'Alerta' ao DataFrame
if not df.empty:
    df['Alerta'] = df.apply(verificar_alerta, axis=1)
else:
    df['Alerta'] = []

# Filtros para visualização
st.sidebar.subheader("Filtros")
areas_disponiveis = df['Area'].unique()
filtro_areas = st.sidebar.selectbox("Filtrar por Área", options=areas_disponiveis)
responsaveis_disponiveis = df[df['Area'] == filtro_areas]['Responsavel'].unique()
filtro_responsaveis = st.sidebar.multiselect("Filtrar por Responsável", options=responsaveis_disponiveis, default=responsaveis_disponiveis)
status_disponiveis = df['Status'].unique()
filtro_status = st.sidebar.multiselect("Filtrar por Status", options=status_disponiveis, default=status_disponiveis)

df_filtrado = df[
    (df['Area'] == filtro_areas) &
    (df['Responsavel'].isin(filtro_responsaveis)) &
    (df['Status'].isin(filtro_status))
]

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

st.subheader("Dados do Plano de Ação")
df_filtrado_display = df_filtrado.copy()
for col in ['Inicio Plan', 'Fim Plan', 'Inicio Real', 'Fim Real']:
    df_filtrado_display[col] = df_filtrado_display[col].dt.strftime('%d/%m/%Y')

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
        registro_selecionado = st.selectbox("Selecione o número do registro para editar", indices_disponiveis)
        st.subheader(f"Editando registro #{registro_selecionado}")
        
        area_options = list(area_responsavel.keys())
        area_value = df.loc[registro_selecionado, 'Area']
        if area_value in area_options:
            area_index = area_options.index(area_value)
        else:
            area_index = 0

        area_edit = st.selectbox('Área', options=area_options, index=area_index)

        default_responsavel = area_responsavel.get(area_edit, '')
        if default_responsavel in responsaveis:
            responsavel_index = responsaveis.index(default_responsavel)
        else:
            responsavel_index = 0

        local_edit = st.text_input('Local', df.loc[registro_selecionado, 'Local'])
        acao_edit = st.text_input('Ação (O que)', df.loc[registro_selecionado, 'Acao'])
        impacto_edit = st.text_area('Impacto', df.loc[registro_selecionado, 'Impacto'])
        responsavel_edit = st.selectbox("Responsável", options=responsaveis, index=responsaveis.index(df.loc[registro_selecionado, 'Responsavel']))
        inicio_plan_edit = st.date_input('Início Planejado', df.loc[registro_selecionado, 'Inicio Plan'])
        fim_plan_edit = st.date_input('Fim Planejado', df.loc[registro_selecionado, 'Fim Plan'])
        inicio_real_edit = st.date_input('Início Real (opcional)', df.loc[registro_selecionado, 'Inicio Real'] if pd.notna(df.loc[registro_selecionado, 'Inicio Real']) else None)
        fim_real_edit = st.date_input('Fim Real (opcional)', df.loc[registro_selecionado, 'Fim Real'] if pd.notna(df.loc[registro_selecionado, 'Fim Real']) else None)

        observacoes_edit = st.text_area("Observações", df.loc[registro_selecionado, 'Observações'] if pd.notna(df.loc[registro_selecionado, 'Observações']) else '')
        nota_trabalho_edit = st.text_area("Nota de Trabalho", df.loc[registro_selecionado, 'Nota de Trabalho'] if pd.notna(df.loc[registro_selecionado, 'Nota de Trabalho']) else '')
        resultado_esperado_alcancado_edit = st.selectbox(
            "O resultado esperado foi alcançado?",
            ['Sim', 'Não', 'Parcialmente'],
            index=['Sim', 'Não', 'Parcialmente'].index(df.loc[registro_selecionado, 'O resultado esperado foi alcançado?']) if pd.notna(df.loc[registro_selecionado, 'O resultado esperado foi alcançado?']) else 0
        )
        se_nao_o_que_fazer_edit = st.text_area(
            "Se não, o que será feito?",
            df.loc[registro_selecionado, 'Se não, o que será feito?'] if pd.notna(df.loc[registro_selecionado, 'Se não, o que será feito?']) else ''
        )

        corpo_edit = st.selectbox(
            'Corpo',
            options=corpos_opcoes,
            index=corpos_opcoes.index(df.loc[registro_selecionado, 'Corpo']) if pd.notna(df.loc[registro_selecionado, 'Corpo']) else 0
        )
        nivel_edit = st.selectbox(
            'Nível',
            options=niveis_opcoes,
            index=niveis_opcoes.index(df.loc[registro_selecionado, 'Nível']) if pd.notna(df.loc[registro_selecionado, 'Nível']) else 0
        )

        if st.button("Atualizar Registro"):
            if inicio_plan_edit > fim_plan_edit:
                st.error("A data de início planejado não pode ser após a data de fim planejado.")
            elif inicio_real_edit and fim_real_edit and inicio_real_edit > fim_real_edit:
                st.error("A data de início real não pode ser após a data de fim real.")
            elif inicio_real_edit and inicio_real_edit < inicio_plan_edit:
                st.error("A data de início real não pode ser anterior à data de início planejado.")
            elif fim_real_edit and inicio_real_edit and fim_real_edit < inicio_real_edit:
                st.error("A data de fim real não pode ser anterior à data de início real.")
            else:
                df.at[registro_selecionado, 'Area'] = area_edit
                df.at[registro_selecionado, 'Local'] = local_edit
                df.at[registro_selecionado, 'Acao'] = acao_edit
                df.at[registro_selecionado, 'Impacto'] = impacto_edit
                df.at[registro_selecionado, 'Responsavel'] = responsavel_edit
                df.at[registro_selecionado, 'Inicio Plan'] = inicio_plan_edit
                df.at[registro_selecionado, 'Fim Plan'] = fim_plan_edit
                df.at[registro_selecionado, 'Inicio Real'] = inicio_real_edit
                df.at[registro_selecionado, 'Fim Real'] = fim_real_edit
                df.at[registro_selecionado, 'Dias'] = (fim_plan_edit - inicio_plan_edit).days + 1
                df.at[registro_selecionado, 'Status'] = calcular_status(inicio_real_edit, fim_real_edit, fim_plan_edit)
                df.at[registro_selecionado, 'Observações'] = observacoes_edit
                df.at[registro_selecionado, 'Nota de Trabalho'] = nota_trabalho_edit
                df.at[registro_selecionado, 'O resultado esperado foi alcançado?'] = resultado_esperado_alcancado_edit
                df.at[registro_selecionado, 'Se não, o que será feito?'] = se_nao_o_que_fazer_edit
                df.at[registro_selecionado, 'Corpo'] = corpo_edit
                df.at[registro_selecionado, 'Nível'] = nivel_edit
                df.at[registro_selecionado, 'Classificação Impacto'] = classificar_impacto(impacto_edit)
                df.at[registro_selecionado, 'Semana'] = inicio_plan_edit.isocalendar().week
                salvar_dados(df)
                st.success("Registro atualizado com sucesso!")
    else:
        st.info("Não há registros para editar.")

buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
    df.to_excel(writer, index=False)

st.download_button(
    label="Baixar dados em Excel",
    data=buffer.getvalue(),
    file_name="dados_projeto.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

st.subheader("Ações Executadas nos Últimos 7 Dias")
hoje = datetime.now().date()
hoje = datetime.now()
ultima_semana = hoje - timedelta(days=7)
acoes_ultima_semana = df[
    (df['Fim Real'] >= ultima_semana) &
    (df['Fim Real'] <= hoje)
]
if not acoes_ultima_semana.empty:
    st.dataframe(acoes_ultima_semana)
else:
    st.info("Nenhuma ação foi executada nos últimos 7 dias.")

st.subheader("Distribuição da Classificação do Impacto")
st.markdown("""
Este gráfico mostra a quantidade de atividades por nível de impacto. Permite identificar quais níveis de impacto estão mais presentes nas atividades planejadas.
""")
if not df_filtrado.empty:
    impacto_counts = df_filtrado['Classificação Impacto'].value_counts()
    fig1, ax1 = plt.subplots()
    colors = ['red' if x == 'Alto' else 'orange' if x == 'Médio' else 'green' if x == 'Baixo' else 'grey' for x in impacto_counts.index]
    ax1.bar(impacto_counts.index, impacto_counts.values, color=colors)
    ax1.set_xlabel('Classificação do Impacto')
    ax1.set_ylabel('Quantidade de Atividades')
    ax1.set_title('Distribuição da Classificação do Impacto')
    st.pyplot(fig1)
else:
    st.info("Não há dados para exibir o gráfico de distribuição do impacto.")

st.subheader("Nuvem de Palavras dos Impactos")
st.markdown("""
Esta nuvem de palavras destaca as palavras mais frequentes nas descrições de impacto das atividades. Quanto maior a palavra, mais frequentemente ela aparece nas descrições.
""")
texto_impacto = ' '.join(df_filtrado['Impacto'].dropna().tolist())
if texto_impacto.strip():
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(texto_impacto)
    fig2, ax2 = plt.subplots(figsize=(10, 5))
    ax2.imshow(wordcloud, interpolation='bilinear')
    ax2.axis('off')
    st.pyplot(fig2)
else:
    st.info("Não há descrições de impacto para gerar a nuvem de palavras.")

st.subheader("Curva S - Progresso Cumulativo (Planejado vs Real)")
st.markdown("""
Este gráfico mostra o progresso cumulativo planejado e real ao longo do tempo, permitindo comparar o andamento real do projeto em relação ao planejado.
""")
if not df_filtrado.empty:
    df_plan = df_filtrado.copy()
    df_plan['Valor'] = 1
    data_inicio = df_plan['Inicio Plan'].min()
    data_fim = df_plan['Fim Plan'].max()
    datas = pd.date_range(start=data_inicio, end=data_fim)

    progresso_planejado = []
    for data in datas:
        tarefas_concluidas = df_plan[df_plan['Fim Plan'] <= data]['Valor'].sum()
        progresso_planejado.append(tarefas_concluidas)
    total_tarefas = df_plan['Valor'].sum()
    perc_planejado = [val / total_tarefas * 100 for val in progresso_planejado]

    progresso_real = []
    for data in datas:
        tarefas_concluidas = df_plan[df_plan['Fim Real'] <= data]['Valor'].sum()
        progresso_real.append(tarefas_concluidas)
    perc_real = [val / total_tarefas * 100 for val in progresso_real]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(datas, perc_planejado, label='Planejado', color='blue', marker='o')
    ax.plot(datas, perc_real, label='Real', color='green', marker='o')

    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y'))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    fig.autofmt_xdate()

    ax.set_xlabel("Data", fontsize=12)
    ax.set_ylabel("Progresso (%)", fontsize=12)
    ax.set_title("Curva S - Progresso Cumulativo (Planejado vs Real)", fontsize=14, fontweight='bold')
    ax.legend(loc="upper left", fontsize=12)
    ax.grid(True)

    st.pyplot(fig)
else:
    st.info("Não há dados suficientes para gerar a Curva S.")

# Gráfico de Curva S por Classificação de Impacto
st.subheader("Curva S - Progresso Cumulativo por Classificação de Impacto")
st.markdown("""
Este gráfico detalha o progresso cumulativo planejado e real para cada nível de impacto, permitindo uma análise mais aprofundada do andamento das atividades de diferentes importâncias.
""")
if not df_filtrado.empty:
    df_plan = df_filtrado.copy()
    df_plan['Valor'] = 1
    data_inicio = df_plan['Inicio Plan'].min()
    data_fim = df_plan['Fim Plan'].max()
    datas = pd.date_range(start=data_inicio, end=data_fim)

    classificacoes = df_plan['Classificação Impacto'].unique()
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = {'Alto': 'red', 'Médio': 'orange', 'Baixo': 'green', 'Indeterminado': 'grey'}
    for classificacao in classificacoes:
        df_classe = df_plan[df_plan['Classificação Impacto'] == classificacao]
        progresso_planejado = []
        progresso_real = []
        for data in datas:
            tarefas_planejadas_concluidas = df_classe[df_classe['Fim Plan'] <= data]['Valor'].sum()
            progresso_planejado.append(tarefas_planejadas_concluidas)

            tarefas_reais_concluidas = df_classe[df_classe['Fim Real'] <= data]['Valor'].sum()
            progresso_real.append(tarefas_reais_concluidas)

        total_tarefas = df_classe['Valor'].sum()
        if total_tarefas > 0:
            perc_planejado = [val / total_tarefas * 100 for val in progresso_planejado]
            perc_real = [val / total_tarefas * 100 for val in progresso_real]
            ax.plot(datas, perc_planejado, label=f'Planejado - {classificacao}', linestyle='--', color=colors.get(classificacao, 'black'))
            ax.plot(datas, perc_real, label=f'Real - {classificacao}', linestyle='-', color=colors.get(classificacao, 'black'))

    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y'))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    fig.autofmt_xdate()

    ax.set_xlabel("Data", fontsize=12)
    ax.set_ylabel("Progresso (%)", fontsize=12)
    ax.set_title("Curva S - Progresso Cumulativo por Classificação de Impacto", fontsize=14, fontweight='bold')
    ax.legend(loc="upper left", fontsize=10)
    ax.grid(True)

    st.pyplot(fig)
else:
    st.info("Não há dados suficientes para gerar a Curva S por impacto.")
