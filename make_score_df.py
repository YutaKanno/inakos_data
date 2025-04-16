import numpy as np
import pandas as pd

def make_score_df(gd, team_top, team_bottom, date):
    df = gd[(gd['試合日時'] == date) & (gd['先攻チーム'] == team_top) & (gd['後攻チーム'] == team_bottom)]
    df['攻撃チーム'] = np.where(df['表.裏'] == '表', df['先攻チーム'], df['後攻チーム'])

    df_top = df[df['攻撃チーム'] == team_top]
    df_bottom = df[df['攻撃チーム'] == team_bottom]

    
    
    
    names_top = list(df_top['打者氏名'].unique())
    max_inning = df_top['回'].max()

    score_list_top = []
    for i in range(len(names_top)):
        batter = names_top[i]

        df_filtered = df_top[df_top['打者氏名'] == batter]
        batter_no = list(df_filtered['打順'].unique())

        df_result = df_filtered[df_filtered['打席結果'] != '0']
        batter_results = list(df_result['打席結果'])
        results_inning = list(df_result['回'])
        results_pt = list(df_result['球種'])

        temp_list = []
        temp_list2 = []
        max_inning = int(max_inning)
        for j in range(max_inning):
            temp_list.append('')
            temp_list2.append('')

        for j in range(len(results_inning)):
            value_inning = results_inning[j]
            value_inning = int(value_inning)
            temp_list[value_inning-1] = batter_results[j]
            temp_list2[value_inning-1] = results_pt[j]

        lists = [batter_no, batter, temp_list, temp_list2]
        score_list_top.append(lists)

    score_list_top.sort(key=lambda x: x[0][0])

    df_score_top = pd.DataFrame(
        score_list_top,
        columns=['打順', '打者氏名', '結果', '球種']
    )

    max_inning = int(max_inning)
    for i in range(max_inning):
        df_score_top[f'{i+1}回'] = df_score_top.apply(
            lambda row: row['結果'][i] if i < len(row['結果']) else None, axis=1
        )
        df_score_top[f'球種{i+1}'] = df_score_top.apply(
            lambda row: row['球種'][i] if i < len(row['結果']) else None, axis=1
        )

    df_score_top = df_score_top.drop(columns=['結果', '球種'])




    names_bottom = list(df_bottom['打者氏名'].unique())
    max_inning = df_bottom['回'].max()

    score_list_bottom = []
    for i in range(len(names_bottom)):
        batter = names_bottom[i]

        df_filtered = df_bottom[df_bottom['打者氏名'] == batter]
        batter_no = list(df_filtered['打順'].unique())

        df_result = df_filtered[df_filtered['打席結果'] != '0']
        batter_results = list(df_result['打席結果'])
        results_inning = list(df_result['回'])
        results_pt = list(df_result['球種'])

        temp_list = []
        temp_list2 = []
        max_inning = int(max_inning)
        for j in range(max_inning):
            temp_list.append('')
            temp_list2.append('')

        for j in range(len(results_inning)):
            value_inning = results_inning[j]
            value_inning = int(value_inning)
            temp_list[value_inning-1] = batter_results[j]
            temp_list2[value_inning-1] = results_pt[j]

        lists = [batter_no, batter, temp_list, temp_list2]
        score_list_bottom.append(lists)

    score_list_bottom.sort(key=lambda x: x[0][0])

    df_score_bottom = pd.DataFrame(
        score_list_bottom,
        columns=['打順', '打者氏名', '結果', '球種']
    )

    for i in range(max_inning):
        df_score_bottom[f'{i+1}回'] = df_score_bottom.apply(
            lambda row: row['結果'][i] if i < len(row['結果']) else None, axis=1
        )
        df_score_bottom[f'球種{i+1}'] = df_score_bottom.apply(
            lambda row: row['球種'][i] if i < len(row['結果']) else None, axis=1
        )

    df_score_bottom = df_score_bottom.drop(columns=['結果', '球種'])
    
    
    return df_score_top, df_score_bottom