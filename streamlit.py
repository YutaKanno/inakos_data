import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import datetime
import make_score_df

        


# パスワードなどをセッションで保存
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# ログイン画面
def login():
    st.title("ログイン画面")

    username = st.text_input("ユーザー名")
    password = st.text_input("パスワード", type="password")
    login_button = st.button("ログイン")

    if login_button:
        if username == "admin" and password == "password123":
            st.session_state.logged_in = True
            st.success("ログイン成功！")
        else:
            st.error("ユーザー名またはパスワードが間違っています")

# メイン画面
def main_page():
    gd_file = 'to_csv_out.csv'
    df = pd.read_csv(gd_file)


    #必要な列の追加


    df['守備チーム'] = np.where(df['表.裏'] == '表', df['後攻チーム'], df['先攻チーム'])
    #試合日時列のフォーマットをyyyy/mm/ddに
    df['試合日時'] = pd.to_datetime(df['試合日時']).dt.strftime('%Y/%m/%d')
    palette = {
        "ストレート": "#FF3333",
        "ツーシーム": "#FF9933",
        "スライダー": "#6666FF",
        "カット": "#9933FF",
        "カーブ": "#66B2FF",
        "チェンジ": "#00CC66",
        "フォーク": "#009900",
        "シンカー": "#CC00CC",
        "シュート": "#FF66B2",
        "特殊球": "#000000"
    }


    st.set_page_config(
        page_title="My Streamlit App",
        page_icon="📈",
        layout="wide",  # ウィンドウサイズに合わせて広く表示
    )


    page = st.radio("", ["ランキング", "個人成績", "スコア"])

    if page == 'ランキング':
        unique_teams = df['守備チーム'].unique()
        unique_teams2 = ["全チーム"] + [team for team in unique_teams if team != "全チーム"]
        team = st.selectbox('チーム名', unique_teams2, index=0)
        
            
        def stats(filtered_df):
            result = filtered_df.groupby(['投手氏名', '守備チーム']).agg(
                NP=('プレイの種類', lambda x: (x == '投球').sum()),
                
                IP_B = ('打者状況', lambda x: (x == 'アウト').sum()),
                IP_1 = ('一走状況', lambda x: (x.isin( ['封殺', '投手牽制死', '捕手牽制死'])).sum()),
                IP_2 = ('二走状況', lambda x: (x.isin( ['封殺', '投手牽制死', '捕手牽制死'])).sum()),
                IP_3 = ('三走状況', lambda x: (x.isin( ['封殺', '投手牽制死', '捕手牽制死'])).sum()),
                
                PA=('打席の継続', lambda x: (x == '打席完了').sum()),
                RV=('打撃結果', lambda x: (x.isin(['犠打', '犠飛', '犠打失策', '四球', '死球'])).sum()),
                S=('打撃結果', lambda x: (x == '単打').sum()),
                D=('打撃結果', lambda x: (x == '二塁打').sum()),
                T=('打撃結果', lambda x: (x == '三塁打').sum()),
                HR=('打撃結果', lambda x: (x == '本塁打').sum()),
                H=('打撃結果', lambda x: (x.isin(['単打', '二塁打', '三塁打', '本塁打'])).sum()),
                K=('打撃結果', lambda x: x.isin(['見逃し三振', '空振り三振', 'K3', '振り逃げ']).sum()),
                BB=('打撃結果', lambda x: (x == '四球').sum()),
            ).reset_index()

            # OAV, OBA, SLG, OPS, K%, B%, WHIP の計算
            result['IP'] = ((result['IP_B'] + result['IP_1'] + result['IP_2'] + result['IP_3']) / 3).round(1)
            result['AB'] = (result['PA'] - result['RV'])
            result['OAV'] = (result['H'] / result['AB']).round(3).fillna(0)
            result['OBA'] = ((result['H'] + result['BB']) / 
                            (result['AB'] + result['BB'] + filtered_df['打撃結果'].value_counts().get('犠飛', 0))).round(3).fillna(0)
            result['SLG'] = ((result['S'] + 2 * result['D'] + 3 * result['T'] + 4 * result['HR']) / result['AB']).round(3).fillna(0)
            result['OPS'] = result['OBA'] + result['SLG']
            result['K%'] = (100 * result['K'] / result['PA']).round(1).fillna(0)
            result['B%'] = (100 * result['BB'] / result['PA']).round(1).fillna(0)
            result['WHIP'] = ((result['H'] + result['BB']) / result['IP']).round(2).fillna(0)
            
            columns_order = ['投手氏名', '守備チーム', 'NP', 'IP', 'PA', 'AB', 'S', 'D', 'T', 'HR', 'H', 'K', 'BB', 
                        'OAV', 'OBA', 'SLG', 'OPS', 'K%', 'B%', 'WHIP']
            result = result[columns_order]
        
            return result
        
        result = stats(df)

        min_ip = result['IP'].min()
        max_ip = result['IP'].max()
        selected_ip = st.slider('イニング数', min_value=min_ip, max_value=max_ip, value=min_ip)
        
        if team != '全チーム':
            filtered_result = result[result['守備チーム'] == team]
        else:
            filtered_result = result
        
        filtered_result = filtered_result[filtered_result['IP'] >= selected_ip] 
        
        st.dataframe(filtered_result, height=1000)
        
    elif page == '個人成績':
        col1, col2 = st.columns(2)
        with col1:
            # チーム名リストの作成
            unique_teams = df['守備チーム'].unique()
            team = st.selectbox('チーム名を選択してください', unique_teams)
        with col2:
            # 投手氏名リストの作成
            team_filtered = df[df['守備チーム'] == team]
            unique_names = team_filtered['投手氏名'].unique()
            name = st.selectbox('投手氏名を選択してください', unique_names)


        # 投手氏名でフィルターをかけたデータフレーム
        filtered_df = df[(df['投手氏名'] == name) & (df['プレイの種類'] == '投球')]

        # 最速, 平均球速
        for_mean = filtered_df[(filtered_df['球種'] == 'ストレート') & (filtered_df['球速'] != 0)]
        FB_max = for_mean['球速'].max()
        FB_mean = round(for_mean['球速'].mean(), 1)



        # 各種指標の計算
        def cal_all_stats(filtered_df):
            result = {
                'NP': filtered_df['プレイの種類'].value_counts().get('投球', 0),
                'IP': round((filtered_df['打者状況'].value_counts().get('アウト', 0) +
                            filtered_df['一走状況'].isin(['封殺', '投手牽制死', '捕手牽制死']).sum() +
                            filtered_df['二走状況'].isin(['封殺', '投手牽制死', '捕手牽制死']).sum() +
                            filtered_df['三走状況'].isin(['封殺', '投手牽制死', '捕手牽制死']).sum()) / 3, 1),
                'PA': filtered_df['打席の継続'].value_counts().get('打席完了', 0),
                'AB': filtered_df['打席の継続'].value_counts().get('打席完了', 0) - filtered_df['打撃結果'].isin(['犠打', '犠飛', '犠打失策', '死球', '四球']).sum(),
                'S': filtered_df['打撃結果'].value_counts().get('単打', 0),
                'D': filtered_df['打撃結果'].value_counts().get('二塁打', 0),
                'T': filtered_df['打撃結果'].value_counts().get('三塁打', 0),
                'HR': filtered_df['打撃結果'].value_counts().get('本塁打', 0),
                'H': filtered_df['打撃結果'].isin(['単打', '二塁打', '三塁打', '本塁打']).sum(),
                'K': filtered_df['打撃結果'].isin(['見逃し三振', '空振り三振', 'K3', '振り逃げ']).sum(),
                'BB': filtered_df['打撃結果'].isin(['死球', '四球']).sum(),
            }

            AB = result['AB']
            H = result['H']
            K = result['K']
            BB = result['BB']
            IP = result['IP']
            PA = result['PA']

            result['OAV'] = round(H / AB, 3) if AB > 0 else 0
            result['OBA'] = round((H + BB) / (AB + BB + filtered_df['打撃結果'].value_counts().get('犠飛', 0)), 3) if (AB + BB + filtered_df['打撃結果'].value_counts().get('犠飛', 0)) > 0 else 0
            result['SLG'] = round((result['S'] + 2 * result['D'] + 3 * result['T'] + 4 * result['HR']) / AB, 3) if AB > 0 else 0
            result['OPS'] = result['OBA'] + result['SLG']
            result['K%'] = round(100 * K / PA, 1) if PA > 0 else 0
            result['BB%'] = round(100 * BB / PA, 1) if PA > 0 else 0
            result['WHIP'] = round((H + BB) / IP, 2) if IP > 0 else 0

            stats_table = pd.DataFrame([result])
            
            return stats_table


        # 打席左右別の計算
        def cal_LR_stats(filtered_df):
            result = filtered_df.groupby('打席左右').agg(
                NP=('プレイの種類', lambda x: (x == '投球').sum()),
                IP=('打者状況', lambda x: round((
                    (x == 'アウト').sum() +
                    (filtered_df['一走状況'].isin(['封殺', '投手牽制死', '捕手牽制死'])).sum() +
                    (filtered_df['二走状況'].isin(['封殺', '投手牽制死', '捕手牽制死'])).sum() +
                    (filtered_df['三走状況'].isin(['封殺', '投手牽制死', '捕手牽制死'])).sum()
                ) / 3, 1)),
                PA=('打席の継続', lambda x: (x == '打席完了').sum()),
                AB=('打席の継続', lambda x: (x == '打席完了').sum() - 
                    (filtered_df['打撃結果'].isin(['犠打', '犠飛', '犠打失策', '死球', '四球'])).sum()),
                S=('打撃結果', lambda x: (x == '単打').sum()),
                D=('打撃結果', lambda x: (x == '二塁打').sum()),
                T=('打撃結果', lambda x: (x == '三塁打').sum()),
                HR=('打撃結果', lambda x: (x == '本塁打').sum()),
                H=('打撃結果', lambda x: (x.isin(['単打', '二塁打', '三塁打', '本塁打'])).sum()),
                K=('打撃結果', lambda x: x.isin(['見逃し三振', '空振り三振', 'K3', '振り逃げ']).sum()),
                BB=('打撃結果', lambda x: (x == '四球').sum()),
            ).reset_index()

            # OAV, OBA, SLG, OPS, K%, B%, WHIP の計算
            result['OAV'] = (result['H'] / result['AB']).round(3).fillna(0)
            result['OBA'] = ((result['H'] + result['BB']) / 
                            (result['AB'] + result['BB'] + filtered_df['打撃結果'].value_counts().get('犠飛', 0))).round(3).fillna(0)
            result['SLG'] = ((result['S'] + 2 * result['D'] + 3 * result['T'] + 4 * result['HR']) / result['AB']).round(3).fillna(0)
            result['OPS'] = result['OBA'] + result['SLG']
            result['K%'] = (100 * result['K'] / result['PA']).round(1).fillna(0)
            result['B%'] = (100 * result['BB'] / result['PA']).round(1).fillna(0)
            result['WHIP'] = ((result['H'] + result['BB']) / result['IP']).round(2).fillna(0)
            
            return result


        def cal_all_stats_grouped(filtered_df):
            grouped_stats = (
                filtered_df
                .groupby(['試合日時', '先攻チーム', '後攻チーム'])
                .apply(lambda group: pd.Series(cal_all_stats(group).iloc[0]))
                .reset_index()
            )

            return grouped_stats

        stats_table = cal_all_stats(filtered_df)
        stats_LR_table = cal_LR_stats(filtered_df)
        grouped_stats = cal_all_stats_grouped(filtered_df)


        # 球速帯グラフ
        filtered_df2 = filtered_df[filtered_df['球速'] != 0]
        grouped_df = filtered_df2.groupby(['球種', '球速']).size().reset_index(name='N')
        speed = px.bar(
            grouped_df, 
            x='球速', 
            y='N', 
            color='球種', 
            title='球速帯グラフ',
            labels={'球速': '球速', 'N': 'カウント'},
            color_discrete_map=palette
        )

        # 球種別の球速の計算
        pt_speeds = filtered_df2.groupby('球種').agg(
            min=('球速', 'min'),
            mean=('球速', 'mean'),
            max=('球速', 'max')
        ).reset_index()
        pt_speeds['mean'] = pt_speeds['mean'].round(1)
        unique_pts = pt_speeds['球種'].unique()
        '---'

        # ヘッダー
        st.title(f'{name} ({team})')
        '---'
        st.write('全体成績')
        st.dataframe(stats_table)
        st.write('左右別')
        st.dataframe(stats_LR_table)
        st.write('試合別')
        st.dataframe(grouped_stats)

        # 球速グラフ
        col1, col2 = st.columns([3,1])
        with col1:
            st.plotly_chart(speed)
        with col2:
            st.write('平均球速, 最遅, 最速')
            for i in range(len(unique_pts)):
                pt_speeds['球種'][i], ' : ', pt_speeds['mean'][i], 'km/h (', pt_speeds['min'][i], ' ~ ', pt_speeds['max'][i], ') '



        '---'











        with st.form(key='filter_form'):
            col1, col2, col3, col4 = st.columns(4)
            situ_filtered_indv = filtered_df
            situ_filtered_league = df
            with col1:
                selected_LR = st.selectbox('打席左右', ['全体', '対左', '対右'])
            with col2:
                catcher_options = ['全体'] + list(filtered_df['捕手'].unique())
                selected_Catcher = st.selectbox('捕手', catcher_options)
            with col3:
                selected_Rsitu = st.selectbox('ランナー', ['全体', 'Rなし', 'R1', 'R2', 'R3', '得点圏'])
            with col4:
                selected_Csitu = st.selectbox('カウント', ['全体', '初球', '1-0', '0-1', '1-1', 'ストライク先行', 'ボール先行', '決め球'])


            generate_button = st.form_submit_button('generate')
            if generate_button:
                # リセット
                situ_filtered_indv = filtered_df
                # 打席左右でフィルター
                if selected_LR == '全体':
                    situ_filtered_indv = situ_filtered_indv
                elif selected_LR == '対左':
                    situ_filtered_indv = situ_filtered_indv[situ_filtered_indv['打席左右'] == '左']
                elif selected_LR == '対右':
                    situ_filtered_indv = situ_filtered_indv[situ_filtered_indv['打席左右'] == '右']
                # 捕手氏名でフィルター
                if selected_Catcher == '全体':
                    situ_filtered_indv = situ_filtered_indv
                else:
                    situ_filtered_indv = situ_filtered_indv[situ_filtered_indv['捕手'] == selected_Catcher]
                # 走者状況でフィルター
                if selected_Rsitu == '全体':
                    situ_filtered_indv = situ_filtered_indv
                elif selected_Rsitu == 'Rなし':
                    situ_filtered_indv = situ_filtered_indv[(situ_filtered_indv['一走氏名'] == '0') & (situ_filtered_indv['二走氏名'] == '0') & (situ_filtered_indv['三走氏名'] == '0')]
                elif selected_Rsitu == 'R1':
                    situ_filtered_indv = situ_filtered_indv[(situ_filtered_indv['一走氏名'] != '0') & (situ_filtered_indv['二走氏名'] == '0') & (situ_filtered_indv['三走氏名'] == '0')]
                elif selected_Rsitu == 'R2':
                    situ_filtered_indv = situ_filtered_indv[(situ_filtered_indv['二走氏名'] != '0') & (situ_filtered_indv['三走氏名'] == '0')]
                elif selected_Rsitu == 'R3':
                    situ_filtered_indv = situ_filtered_indv[['三走氏名'] != '0']
                elif selected_Rsitu == '得点圏':
                    situ_filtered_indv = situ_filtered_indv[(situ_filtered_indv['二走氏名'] != '0') | (situ_filtered_indv['三走氏名'] != '0')]
                # カウント状況でフィルター
                if selected_Csitu == '全体':
                    situ_filtered_indv = situ_filtered_indv
                elif selected_Csitu == '初球':
                    situ_filtered_indv = situ_filtered_indv[(situ_filtered_indv['B'] == 0) & (situ_filtered_indv['S'] == 0)]
                elif selected_Csitu == '1-0':
                    situ_filtered_indv = situ_filtered_indv[(situ_filtered_indv['B'] == 1) & (situ_filtered_indv['S'] == 0)]
                elif selected_Csitu == '0-1':
                    situ_filtered_indv = situ_filtered_indv[(situ_filtered_indv['B'] == 0) & (situ_filtered_indv['S'] == 1)]
                elif selected_Csitu == '1-1':
                    situ_filtered_indv = situ_filtered_indv[(situ_filtered_indv['B'] == 1) & (situ_filtered_indv['S'] == 1)]
                elif selected_Csitu == 'ストライク先行':
                    situ_filtered_indv = situ_filtered_indv[((situ_filtered_indv['B'] == 0) & (situ_filtered_indv['S'] >= 1) | (situ_filtered_indv['B'] <= 2) & (situ_filtered_indv['S'] == 2))]         
                elif selected_Csitu == 'ボール先行':
                    situ_filtered_indv = situ_filtered_indv[((situ_filtered_indv['B'] >= 1) & (situ_filtered_indv['S'] == 0) | (situ_filtered_indv['B'] >= 2) & (situ_filtered_indv['S'] == 1))]         
                elif selected_Csitu == '1-2,2-2':
                    situ_filtered_indv = situ_filtered_indv[(situ_filtered_indv['B'] <= 2) & (situ_filtered_indv['S'] == 2)]         
                
            
            col1, col2 = st.columns([1, 2])
            with col1:
                # 投球割合の円グラフ
                st.write('投球割合(設定された状況下)')
                pt_counts = situ_filtered_indv['球種'].value_counts()
                pie = px.pie(values=pt_counts, names=pt_counts.index,
                            color=pt_counts.index, color_discrete_map=palette)
                st.plotly_chart(pie)
            with col2:
                def calculate_metrics(group):
                    NP = (group['プレイの種類'] == '投球').sum()
                    Strike = (~group['打撃結果'].isin(['ボール', '四球', '死球', '0'])).sum()
                    Zone = ((group['コースX'].between(53, 210)) & (group['コースY'].between(53, 210))).sum()
                    Whiff = group['打撃結果'].isin(['空振り', '空振り三振']).sum()
                    Swing = group['打撃結果'].isin(['見逃し', '見逃し三振', 'ボール', '四球', '死球'])
                    Swing_count = (~Swing).sum()  # 振った数の合計
                    OSW = ((group['打撃結果'].isin(['空振り', '空振り三振'])) & 
                        ((group['コースX'] < 53) | (group['コースX'] > 210) | 
                            (group['コースY'] < 53) | (group['コースY'] > 210))).sum()
                    H = group['打撃結果'].isin(['単打', '二塁打', '三塁打', '本塁打']).sum()
                    AB = ((group['打席の継続'] == '打席完了') & 
                    (~group['打撃結果'].isin(['死球', '四球', '犠打', '犠飛']))).sum()
                    
                    Strike_percent = round((100 * Strike / NP) if NP != 0 else 0)  
                    Zone_percent = round((100 * Zone / NP) if NP != 0 else 0)  
                    SwStr_percent = round((100* Whiff / NP) if NP != 0 else 0)
                    Whiff_percent = round((100 * Whiff / Swing_count) if Swing_count != 0 else 0)
                    OSW_percent = round((100* OSW / (NP - Zone)) if NP - Zone != 0 else 0)
                    OAV = round(H / AB if AB != 0 else 0, 3)
                    

                    return pd.Series({
                        'NP': NP,
                        'Strike%': Strike_percent,
                        'Zone%': Zone_percent,
                        'SwStr%': SwStr_percent,
                        'Whiff%': Whiff_percent,
                        'O-Swg%': OSW_percent,
                        'OAV': OAV
                    })

                # 球種成績のデータフレームを作成する関数
                pt_stats_indv = filtered_df.groupby('球種').apply(calculate_metrics).reset_index()
                pt_stats_by_situ = situ_filtered_indv.groupby('球種').apply(calculate_metrics).reset_index()
                pt_stats_league = df.groupby('球種').apply(calculate_metrics).reset_index()

                def pt_stats_dataframe(pt_stats, pt_stats2):
                    merged_stats = pd.merge(pt_stats, pt_stats2, on='球種', suffixes=('_個人', '_平均'))
                    merged_stats['NP'] = merged_stats['NP_個人']
                    merged_stats['Strike%'] = merged_stats.apply(
                        lambda row: f"{row['Strike%_個人']} ({row['Strike%_平均']})",
                        axis=1
                    )
                    merged_stats['Zone%'] = merged_stats.apply(
                        lambda row: f"{row['Zone%_個人']} ({row['Zone%_平均']})",
                        axis=1
                    )
                    merged_stats['SwStr%'] = merged_stats.apply(
                        lambda row: f"{row['SwStr%_個人']} ({row['SwStr%_平均']})",
                        axis=1
                    )
                    merged_stats['Whiff%'] = merged_stats.apply(
                        lambda row: f"{row['Whiff%_個人']} ({row['Whiff%_平均']})",
                        axis=1
                    )
                    merged_stats['O-Swg%'] = merged_stats.apply(
                        lambda row: f"{row['O-Swg%_個人']} ({row['O-Swg%_平均']})",
                        axis=1
                    )
                    merged_stats['OAV'] = merged_stats.apply(
                        lambda row: f"{row['OAV_個人']} ({row['OAV_平均']})",
                        axis=1
                    )
                    columns_to_keep = ['球種', 'NP', 'Strike%', 'Zone%', 'SwStr%', 'Whiff%', 'O-Swg%', 'OAV']
                    merged_stats_cleaned = merged_stats[columns_to_keep]
                    
                    return merged_stats_cleaned
                pt_stats = pt_stats_dataframe(pt_stats_indv, pt_stats_league)
                st.write('球種成績(設定された状況下)')
                st.dataframe(pt_stats_by_situ)
                st.write('球種成績(全体)(括弧内はリーグ平均値)')
                st.dataframe(pt_stats)
                
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                situ_filtered_indv['打撃結果2'] = situ_filtered_indv['打撃結果'].apply(lambda x: '凡打' if x in ['凡打死', '凡打出塁'] else ('安打' if x in ['単打', '二塁打', '三塁打', '本塁打'] else None))
                situ_filtered_plot = situ_filtered_indv[situ_filtered_indv['打撃結果2'].isin(['安打'])]

                symbol_map = {
                '安打': 'circle',
                '凡打': 'x'
                }
                # Plot with Plotly
                fig = px.scatter(
                    situ_filtered_plot,
                    x='コースX',
                    y=situ_filtered_plot['コースY'].apply(lambda y: 263 - y),
                    color='球種',
                    symbol='打撃結果2',
                    symbol_map=symbol_map,
                    color_discrete_map=palette,
                    title='安打',
                    labels={'コースX': '', 'コースY': ''},
                    hover_data={
                        'コースX': False, 
                        'コースY': False, 
                        '打撃結果2': False,
                        '打撃結果': True,
                        '打者氏名': True,
                        '球速': True,
                        '捕球選手': True,
                        '打球タイプ': True,
                        '球種': False  
                    }
                )

                # Add grey boundary lines
                fig.add_shape(type='line', x0=53, x1=210, y0=263-53, y1=263-53, line=dict(color='grey'))
                fig.add_shape(type='line', x0=53, x1=210, y0=263-210, y1=263-210, line=dict(color='grey'))
                fig.add_shape(type='line', x0=53, x1=53, y0=263-53, y1=263-210, line=dict(color='grey'))
                fig.add_shape(type='line', x0=210, x1=210, y0=263-53, y1=263-210, line=dict(color='grey'))
                fig.update_xaxes(range=[0, 263])
                fig.update_yaxes(range=[0, 263])
                fig.update_traces(marker=dict(size=7))
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig)
            with col2:
                situ_filtered_indv['打撃結果2'] = situ_filtered_indv['打撃結果'].apply(lambda x: '凡打' if x in ['凡打死', '凡打出塁'] else ('安打' if x in ['単打', '二塁打', '三塁打', '本塁打'] else None))
                situ_filtered_plot = situ_filtered_indv[situ_filtered_indv['打撃結果2'].isin(['凡打'])]

                symbol_map = {
                '安打': 'circle',
                '凡打': 'circle'
                }
                # Plot with Plotly
                fig = px.scatter(
                    situ_filtered_plot,
                    x='コースX',
                    y=situ_filtered_plot['コースY'].apply(lambda y: 263 - y),
                    color='球種',
                    symbol='打撃結果2',
                    symbol_map=symbol_map,
                    color_discrete_map=palette,
                    title='凡打',
                    labels={'コースX': '', 'コースY': ''},
                    hover_data={
                        'コースX': False, 
                        'コースY': False, 
                        '打撃結果2': False,
                        '打撃結果': True,
                        '打者氏名': True,
                        '球速': True,
                        '捕球選手': True,
                        '打球タイプ': True,
                        '球種': False  
                    }
                )

                # Add grey boundary lines
                fig.add_shape(type='line', x0=53, x1=210, y0=263-53, y1=263-53, line=dict(color='grey'))
                fig.add_shape(type='line', x0=53, x1=210, y0=263-210, y1=263-210, line=dict(color='grey'))
                fig.add_shape(type='line', x0=53, x1=53, y0=263-53, y1=263-210, line=dict(color='grey'))
                fig.add_shape(type='line', x0=210, x1=210, y0=263-53, y1=263-210, line=dict(color='grey'))
                fig.update_xaxes(range=[0, 263])
                fig.update_yaxes(range=[0, 263])
                fig.update_traces(marker=dict(size=7))
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig)
            with col3:
                situ_filtered_indv['打撃結果2'] = situ_filtered_indv['打撃結果'].apply(lambda x: '空振り' if x in ['空振り', '空振り三振'] else ('ファール' if x in ['ファール', 'ファールフライ'] else None))
                situ_filtered_plot = situ_filtered_indv[situ_filtered_indv['打撃結果2'].isin(['空振り'])]

                symbol_map = {
                '空振り': 'circle',
                'ファール': 'circle'
                }
                # Plot with Plotly
                fig = px.scatter(
                    situ_filtered_plot,
                    x='コースX',
                    y=situ_filtered_plot['コースY'].apply(lambda y: 263 - y),
                    color='球種',
                    symbol='打撃結果2',
                    symbol_map=symbol_map,
                    color_discrete_map=palette,
                    title='空振り',
                    labels={'コースX': '', 'コースY': ''},
                    hover_data={
                        'コースX': False, 
                        'コースY': False, 
                        '打撃結果2': False,
                        '打撃結果': True,
                        '打者氏名': True,
                        '球速': True,
                        '捕球選手': True,
                        '打球タイプ': True,
                        '球種': False  
                    }
                )
                fig.add_shape(type='line', x0=53, x1=210, y0=263-53, y1=263-53, line=dict(color='grey'))
                fig.add_shape(type='line', x0=53, x1=210, y0=263-210, y1=263-210, line=dict(color='grey'))
                fig.add_shape(type='line', x0=53, x1=53, y0=263-53, y1=263-210, line=dict(color='grey'))
                fig.add_shape(type='line', x0=210, x1=210, y0=263-53, y1=263-210, line=dict(color='grey'))
                fig.update_xaxes(range=[0, 263])
                fig.update_yaxes(range=[0, 263])
                fig.update_traces(marker=dict(size=7))
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig)
            with col4:
                situ_filtered_indv['打撃結果2'] = situ_filtered_indv['打撃結果'].apply(lambda x: '空振り' if x in ['空振り', '空振り三振'] else ('ファール' if x in ['ファール', 'ファールフライ'] else None))
                situ_filtered_plot = situ_filtered_indv[situ_filtered_indv['打撃結果2'].isin(['ファール'])]

                symbol_map = {
                '空振り': 'circle',
                'ファール': 'circle'
                }
                # Plot with Plotly
                fig = px.scatter(
                    situ_filtered_plot,
                    x='コースX',
                    y=situ_filtered_plot['コースY'].apply(lambda y: 263 - y),
                    color='球種',
                    symbol='打撃結果2',
                    symbol_map=symbol_map,
                    color_discrete_map=palette,
                    title='ファール',
                    labels={'コースX': '', 'コースY': ''},
                    hover_data={
                        'コースX': False, 
                        'コースY': False, 
                        '打撃結果2': False,
                        '打撃結果': True,
                        '打者氏名': True,
                        '球速': True,
                        '捕球選手': True,
                        '打球タイプ': True,
                        '球種': False  
                    }
                )
                fig.add_shape(type='line', x0=53, x1=210, y0=263-53, y1=263-53, line=dict(color='grey'))
                fig.add_shape(type='line', x0=53, x1=210, y0=263-210, y1=263-210, line=dict(color='grey'))
                fig.add_shape(type='line', x0=53, x1=53, y0=263-53, y1=263-210, line=dict(color='grey'))
                fig.add_shape(type='line', x0=210, x1=210, y0=263-53, y1=263-210, line=dict(color='grey'))
                fig.update_xaxes(range=[0, 263])
                fig.update_yaxes(range=[0, 263])
                fig.update_traces(marker=dict(size=7))
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig)
                
                
                
    
    
        default_date = datetime.date.today()
        selected_date = st.date_input("日付を選択してください:", value=default_date)
        selected_date_str = selected_date.strftime('%Y/%m/%d')
        filtered_df = filtered_df[filtered_df['試合日時'] == selected_date_str]
        
        # 最速, 平均球速
        for_mean = filtered_df[(filtered_df['球種'] == 'ストレート') & (filtered_df['球速'] != 0)]
        FB_max = for_mean['球速'].max()
        FB_mean = round(for_mean['球速'].mean(), 1)



    


        stats_table = cal_all_stats(filtered_df)
        stats_LR_table = cal_LR_stats(filtered_df)


        # 球速帯グラフ
        filtered_df2 = filtered_df[filtered_df['球速'] != 0]
        grouped_df = filtered_df2.groupby(['球種', '球速']).size().reset_index(name='N')
        speed = px.bar(
            grouped_df, 
            x='球速', 
            y='N', 
            color='球種', 
            title='球速帯グラフ',
            labels={'球速': '球速', 'N': 'カウント'},
            color_discrete_map=palette
        )

        # 球種別の球速の計算
        pt_speeds = filtered_df2.groupby('球種').agg(
            min=('球速', 'min'),
            mean=('球速', 'mean'),
            max=('球速', 'max')
        ).reset_index()
        pt_speeds['mean'] = pt_speeds['mean'].round(1)
        unique_pts = pt_speeds['球種'].unique()
        '---'

        # ヘッダー
        st.write('全体成績')
        st.dataframe(stats_table)
        st.write('左右別')
        st.dataframe(stats_LR_table)

        # 球速グラフ
        col1, col2 = st.columns([3,1])
        with col1:
            st.plotly_chart(speed)
        with col2:
            st.write('平均球速, 最遅, 最速')
            for i in range(len(unique_pts)):
                pt_speeds['球種'][i], ' : ', pt_speeds['mean'][i], 'km/h (', pt_speeds['min'][i], ' ~ ', pt_speeds['max'][i], ') '



        '---'











        with st.form(key='filter_form2'):
            col1, col2, col3, col4 = st.columns(4)
            situ_filtered_indv = filtered_df
            situ_filtered_league = df
            with col1:
                selected_LR = st.selectbox('打席左右', ['全体', '対左', '対右'])
            with col2:
                catcher_options = ['全体'] + list(filtered_df['捕手'].unique())
                selected_Catcher = st.selectbox('捕手', catcher_options)
            with col3:
                selected_Rsitu = st.selectbox('ランナー', ['全体', 'Rなし', 'R1', 'R2', 'R3', '得点圏'])
            with col4:
                selected_Csitu = st.selectbox('カウント', ['全体', '初球', '1-0', '0-1', '1-1', 'ストライク先行', 'ボール先行', '決め球'])


            generate_button = st.form_submit_button('generate')
            if generate_button:
                # リセット
                situ_filtered_indv = filtered_df
                # 打席左右でフィルター
                if selected_LR == '全体':
                    situ_filtered_indv = situ_filtered_indv
                elif selected_LR == '対左':
                    situ_filtered_indv = situ_filtered_indv[situ_filtered_indv['打席左右'] == '左']
                elif selected_LR == '対右':
                    situ_filtered_indv = situ_filtered_indv[situ_filtered_indv['打席左右'] == '右']
                # 捕手氏名でフィルター
                if selected_Catcher == '全体':
                    situ_filtered_indv = situ_filtered_indv
                else:
                    situ_filtered_indv = situ_filtered_indv[situ_filtered_indv['捕手'] == selected_Catcher]
                # 走者状況でフィルター
                if selected_Rsitu == '全体':
                    situ_filtered_indv = situ_filtered_indv
                elif selected_Rsitu == 'Rなし':
                    situ_filtered_indv = situ_filtered_indv[(situ_filtered_indv['一走氏名'] == '0') & (situ_filtered_indv['二走氏名'] == '0') & (situ_filtered_indv['三走氏名'] == '0')]
                elif selected_Rsitu == 'R1':
                    situ_filtered_indv = situ_filtered_indv[(situ_filtered_indv['一走氏名'] != '0') & (situ_filtered_indv['二走氏名'] == '0') & (situ_filtered_indv['三走氏名'] == '0')]
                elif selected_Rsitu == 'R2':
                    situ_filtered_indv = situ_filtered_indv[(situ_filtered_indv['二走氏名'] != '0') & (situ_filtered_indv['三走氏名'] == '0')]
                elif selected_Rsitu == 'R3':
                    situ_filtered_indv = situ_filtered_indv[['三走氏名'] != '0']
                elif selected_Rsitu == '得点圏':
                    situ_filtered_indv = situ_filtered_indv[(situ_filtered_indv['二走氏名'] != '0') | (situ_filtered_indv['三走氏名'] != '0')]
                # カウント状況でフィルター
                if selected_Csitu == '全体':
                    situ_filtered_indv = situ_filtered_indv
                elif selected_Csitu == '初球':
                    situ_filtered_indv = situ_filtered_indv[(situ_filtered_indv['B'] == 0) & (situ_filtered_indv['S'] == 0)]
                elif selected_Csitu == '1-0':
                    situ_filtered_indv = situ_filtered_indv[(situ_filtered_indv['B'] == 1) & (situ_filtered_indv['S'] == 0)]
                elif selected_Csitu == '0-1':
                    situ_filtered_indv = situ_filtered_indv[(situ_filtered_indv['B'] == 0) & (situ_filtered_indv['S'] == 1)]
                elif selected_Csitu == '1-1':
                    situ_filtered_indv = situ_filtered_indv[(situ_filtered_indv['B'] == 1) & (situ_filtered_indv['S'] == 1)]
                elif selected_Csitu == 'ストライク先行':
                    situ_filtered_indv = situ_filtered_indv[((situ_filtered_indv['B'] == 0) & (situ_filtered_indv['S'] >= 1) | (situ_filtered_indv['B'] <= 2) & (situ_filtered_indv['S'] == 2))]         
                elif selected_Csitu == 'ボール先行':
                    situ_filtered_indv = situ_filtered_indv[((situ_filtered_indv['B'] >= 1) & (situ_filtered_indv['S'] == 0) | (situ_filtered_indv['B'] >= 2) & (situ_filtered_indv['S'] == 1))]         
                elif selected_Csitu == '1-2,2-2':
                    situ_filtered_indv = situ_filtered_indv[(situ_filtered_indv['B'] <= 2) & (situ_filtered_indv['S'] == 2)]         
                
            
            col1, col2 = st.columns([1, 2])
            with col1:
                # 投球割合の円グラフ
                st.write('投球割合(設定された状況下)')
                pt_counts = situ_filtered_indv['球種'].value_counts()
                pie = px.pie(values=pt_counts, names=pt_counts.index,
                            color=pt_counts.index, color_discrete_map=palette)
                st.plotly_chart(pie)
            
            with col2:
                def calculate_metrics(group):
                    NP = (group['プレイの種類'] == '投球').sum()
                    Strike = (~group['打撃結果'].isin(['ボール', '四球', '死球', '0'])).sum()
                    Zone = ((group['コースX'].between(53, 210)) & (group['コースY'].between(53, 210))).sum()
                    Whiff = group['打撃結果'].isin(['空振り', '空振り三振']).sum()
                    Swing = group['打撃結果'].isin(['見逃し', '見逃し三振', 'ボール', '四球', '死球'])
                    Swing_count = (~Swing).sum()  # 振った数の合計
                    OSW = ((group['打撃結果'].isin(['空振り', '空振り三振'])) & 
                        ((group['コースX'] < 53) | (group['コースX'] > 210) | 
                            (group['コースY'] < 53) | (group['コースY'] > 210))).sum()
                    H = group['打撃結果'].isin(['単打', '二塁打', '三塁打', '本塁打']).sum()
                    AB = ((group['打席の継続'] == '打席完了') & 
                    (~group['打撃結果'].isin(['死球', '四球', '犠打', '犠飛']))).sum()
                    
                    Strike_percent = round((100 * Strike / NP) if NP != 0 else 0)  
                    Zone_percent = round((100 * Zone / NP) if NP != 0 else 0)  
                    SwStr_percent = round((100* Whiff / NP) if NP != 0 else 0)
                    Whiff_percent = round((100 * Whiff / Swing_count) if Swing_count != 0 else 0)
                    OSW_percent = round((100* OSW / (NP - Zone)) if NP - Zone != 0 else 0)
                    OAV = round(H / AB if AB != 0 else 0, 3)
                    

                    return pd.Series({
                        'NP': NP,
                        'Strike%': Strike_percent,
                        'Zone%': Zone_percent,
                        'SwStr%': SwStr_percent,
                        'Whiff%': Whiff_percent,
                        'O-Swg%': OSW_percent,
                        'OAV': OAV
                    })

                # 球種成績のデータフレームを作成する関数
                pt_stats_indv = filtered_df.groupby('球種').apply(calculate_metrics).reset_index()
                pt_stats_by_situ = situ_filtered_indv.groupby('球種').apply(calculate_metrics).reset_index()
                pt_stats_league = df.groupby('球種').apply(calculate_metrics).reset_index()


                def pt_stats_dataframe(pt_stats, pt_stats2):
                    merged_stats = pd.merge(pt_stats, pt_stats2, on='球種', suffixes=('_個人', '_平均'))
                    merged_stats['NP'] = merged_stats['NP_個人']
                    merged_stats['Strike%'] = merged_stats.apply(
                        lambda row: f"{row['Strike%_個人']} ({row['Strike%_平均']})",
                        axis=1
                    )
                    merged_stats['Zone%'] = merged_stats.apply(
                        lambda row: f"{row['Zone%_個人']} ({row['Zone%_平均']})",
                        axis=1
                    )
                    merged_stats['SwStr%'] = merged_stats.apply(
                        lambda row: f"{row['SwStr%_個人']} ({row['SwStr%_平均']})",
                        axis=1
                    )
                    merged_stats['Whiff%'] = merged_stats.apply(
                        lambda row: f"{row['Whiff%_個人']} ({row['Whiff%_平均']})",
                        axis=1
                    )
                    merged_stats['O-Swg%'] = merged_stats.apply(
                        lambda row: f"{row['O-Swg%_個人']} ({row['O-Swg%_平均']})",
                        axis=1
                    )
                    merged_stats['OAV'] = merged_stats.apply(
                        lambda row: f"{row['OAV_個人']} ({row['OAV_平均']})",
                        axis=1
                    )
                    columns_to_keep = ['球種', 'NP', 'Strike%', 'Zone%', 'SwStr%', 'Whiff%', 'O-Swg%', 'OAV']
                    merged_stats_cleaned = merged_stats[columns_to_keep]
                    
                    return merged_stats_cleaned
                pt_stats = pt_stats_dataframe(pt_stats_indv, pt_stats_league)
                st.write('球種成績(設定された状況下)')
                st.dataframe(pt_stats_by_situ)
                st.write('球種成績(全体)(括弧内はリーグ平均値)')
                st.dataframe(pt_stats)
                
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                situ_filtered_indv['打撃結果2'] = situ_filtered_indv['打撃結果'].apply(lambda x: '凡打' if x in ['凡打死', '凡打出塁'] else ('安打' if x in ['単打', '二塁打', '三塁打', '本塁打'] else None))
                situ_filtered_plot = situ_filtered_indv[situ_filtered_indv['打撃結果2'].isin(['安打'])]

                symbol_map = {
                '安打': 'circle',
                '凡打': 'x'
                }
                # Plot with Plotly
                fig = px.scatter(
                    situ_filtered_plot,
                    x='コースX',
                    y=situ_filtered_plot['コースY'].apply(lambda y: 263 - y),
                    color='球種',
                    symbol='打撃結果2',
                    symbol_map=symbol_map,
                    color_discrete_map=palette,
                    title='安打',
                    labels={'コースX': '', 'コースY': ''},
                    hover_data={
                        'コースX': False, 
                        'コースY': False, 
                        '打撃結果2': False,
                        '打撃結果': True,
                        '打者氏名': True,
                        '球速': True,
                        '捕球選手': True,
                        '打球タイプ': True,
                        '球種': False  
                    }
                )

                # Add grey boundary lines
                fig.add_shape(type='line', x0=53, x1=210, y0=263-53, y1=263-53, line=dict(color='grey'))
                fig.add_shape(type='line', x0=53, x1=210, y0=263-210, y1=263-210, line=dict(color='grey'))
                fig.add_shape(type='line', x0=53, x1=53, y0=263-53, y1=263-210, line=dict(color='grey'))
                fig.add_shape(type='line', x0=210, x1=210, y0=263-53, y1=263-210, line=dict(color='grey'))
                fig.update_xaxes(range=[0, 263])
                fig.update_yaxes(range=[0, 263])
                fig.update_traces(marker=dict(size=7))
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig)
            with col2:
                situ_filtered_indv['打撃結果2'] = situ_filtered_indv['打撃結果'].apply(lambda x: '凡打' if x in ['凡打死', '凡打出塁'] else ('安打' if x in ['単打', '二塁打', '三塁打', '本塁打'] else None))
                situ_filtered_plot = situ_filtered_indv[situ_filtered_indv['打撃結果2'].isin(['凡打'])]

                symbol_map = {
                '安打': 'circle',
                '凡打': 'circle'
                }
                # Plot with Plotly
                fig = px.scatter(
                    situ_filtered_plot,
                    x='コースX',
                    y=situ_filtered_plot['コースY'].apply(lambda y: 263 - y),
                    color='球種',
                    symbol='打撃結果2',
                    symbol_map=symbol_map,
                    color_discrete_map=palette,
                    title='凡打',
                    labels={'コースX': '', 'コースY': ''},
                    hover_data={
                        'コースX': False, 
                        'コースY': False, 
                        '打撃結果2': False,
                        '打撃結果': True,
                        '打者氏名': True,
                        '球速': True,
                        '捕球選手': True,
                        '打球タイプ': True,
                        '球種': False  
                    }
                )

                # Add grey boundary lines
                fig.add_shape(type='line', x0=53, x1=210, y0=263-53, y1=263-53, line=dict(color='grey'))
                fig.add_shape(type='line', x0=53, x1=210, y0=263-210, y1=263-210, line=dict(color='grey'))
                fig.add_shape(type='line', x0=53, x1=53, y0=263-53, y1=263-210, line=dict(color='grey'))
                fig.add_shape(type='line', x0=210, x1=210, y0=263-53, y1=263-210, line=dict(color='grey'))
                fig.update_xaxes(range=[0, 263])
                fig.update_yaxes(range=[0, 263])
                fig.update_traces(marker=dict(size=7))
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig)
            with col3:
                situ_filtered_indv['打撃結果2'] = situ_filtered_indv['打撃結果'].apply(lambda x: '空振り' if x in ['空振り', '空振り三振'] else ('ファール' if x in ['ファール', 'ファールフライ'] else None))
                situ_filtered_plot = situ_filtered_indv[situ_filtered_indv['打撃結果2'].isin(['空振り'])]

                symbol_map = {
                '空振り': 'circle',
                'ファール': 'circle'
                }
                # Plot with Plotly
                fig = px.scatter(
                    situ_filtered_plot,
                    x='コースX',
                    y=situ_filtered_plot['コースY'].apply(lambda y: 263 - y),
                    color='球種',
                    symbol='打撃結果2',
                    symbol_map=symbol_map,
                    color_discrete_map=palette,
                    title='空振り',
                    labels={'コースX': '', 'コースY': ''},
                    hover_data={
                        'コースX': False, 
                        'コースY': False, 
                        '打撃結果2': False,
                        '打撃結果': True,
                        '打者氏名': True,
                        '球速': True,
                        '捕球選手': True,
                        '打球タイプ': True,
                        '球種': False  
                    }
                )
                fig.add_shape(type='line', x0=53, x1=210, y0=263-53, y1=263-53, line=dict(color='grey'))
                fig.add_shape(type='line', x0=53, x1=210, y0=263-210, y1=263-210, line=dict(color='grey'))
                fig.add_shape(type='line', x0=53, x1=53, y0=263-53, y1=263-210, line=dict(color='grey'))
                fig.add_shape(type='line', x0=210, x1=210, y0=263-53, y1=263-210, line=dict(color='grey'))
                fig.update_xaxes(range=[0, 263])
                fig.update_yaxes(range=[0, 263])
                fig.update_traces(marker=dict(size=7))
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig)
            with col4:
                situ_filtered_indv['打撃結果2'] = situ_filtered_indv['打撃結果'].apply(lambda x: '空振り' if x in ['空振り', '空振り三振'] else ('ファール' if x in ['ファール', 'ファールフライ'] else None))
                situ_filtered_plot = situ_filtered_indv[situ_filtered_indv['打撃結果2'].isin(['ファール'])]

                symbol_map = {
                '空振り': 'circle',
                'ファール': 'circle'
                }
                # Plot with Plotly
                fig = px.scatter(
                    situ_filtered_plot,
                    x='コースX',
                    y=situ_filtered_plot['コースY'].apply(lambda y: 263 - y),
                    color='球種',
                    symbol='打撃結果2',
                    symbol_map=symbol_map,
                    color_discrete_map=palette,
                    title='ファール',
                    labels={'コースX': '', 'コースY': ''},
                    hover_data={
                        'コースX': False, 
                        'コースY': False, 
                        '打撃結果2': False,
                        '打撃結果': True,
                        '打者氏名': True,
                        '球速': True,
                        '捕球選手': True,
                        '打球タイプ': True,
                        '球種': False  
                    }
                )
                fig.add_shape(type='line', x0=53, x1=210, y0=263-53, y1=263-53, line=dict(color='grey'))
                fig.add_shape(type='line', x0=53, x1=210, y0=263-210, y1=263-210, line=dict(color='grey'))
                fig.add_shape(type='line', x0=53, x1=53, y0=263-53, y1=263-210, line=dict(color='grey'))
                fig.add_shape(type='line', x0=210, x1=210, y0=263-53, y1=263-210, line=dict(color='grey'))
                fig.update_xaxes(range=[0, 263])
                fig.update_yaxes(range=[0, 263])
                fig.update_traces(marker=dict(size=7))
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig)
                
                
                
                
    elif page == 'スコア':
        df = pd.read_csv(gd_file)
        df['カード'] = df['試合日時'].astype(str) + ' ' + df['先攻チーム'] + ' vs ' + df['後攻チーム']
        select = df['カード'].unique()

        card = st.selectbox('試合を選択してください', select)
        selected_game = df[df['カード'] == card].iloc[0]

        # 試合情報の取得
        match_date = selected_game['試合日時']
        top_team = selected_game['先攻チーム']
        bottom_team = selected_game['後攻チーム']
        
        df_score_top, df_score_bottom = make_score_df.make_score_df(df, top_team, bottom_team, match_date)
        st.write(top_team)
        st.dataframe(df_score_top, height=450, width=2000)
        st.write(bottom_team)
        st.dataframe(df_score_bottom, height=450, width=2000)
        
            
        

# 表示切り替え
if st.session_state.logged_in:
    main_page()
else:
    login()
    
        
    