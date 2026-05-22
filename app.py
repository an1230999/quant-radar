import streamlit as st
import pandas as pd

# ================= 1. 网页界面基础设置 =================
st.set_page_config(page_title="足球量化风控终端", layout="wide", page_icon="⚽")
st.title("⚽ 进球数全维量化风控终端")
st.markdown("---")

# ================= 2. 侧边栏：参数控制台 =================
with st.sidebar:
    st.header("⚙️ 风控参数控制台")
    z2 = st.number_input("宏观动量红线 (Z2)", value=0.0120, format="%.4f", step=0.001)
    z3 = st.number_input("宏观显著防线 (Z3)", value=0.0080, format="%.4f", step=0.001)
    v_limit = st.number_input("微观加速度红线", value=0.0050, format="%.4f", step=0.001)
    st.markdown("*注：参数已默认对齐 Excel 终极版本，可随抽水环境微调。*")

# ================= 3. 数据录入区 (支持直接在网页表格里修改) =================
st.subheader("📝 第一步：录入盘口赔率")
st.write("直接点击下方表格的数据进行修改，修改完毕后点击执行解析。")

# 默认占位数据
initial_data = {
    "选项": ["0球", "1球", "2球", "3球", "4球", "5球", "6球", "7+球"],
    "初盘赔率 (C)": [15.0, 5.5, 3.6, 3.45, 4.9, 8.25, 15.0, 22.0],
    "T-60赔率 (J)": [15.0, 5.6, 3.7, 3.2, 4.8, 8.3, 15.5, 23.0],
    "临场赔率 (D)": [15.5, 5.9, 3.8, 3.1, 4.7, 8.5, 16.0, 24.0]
}
df_input = pd.DataFrame(initial_data)

# 使用 data_editor 让表格在网页上可以直接编辑
edited_df = st.data_editor(df_input, hide_index=True, use_container_width=True)

# ================= 4. 核心精算引擎 =================
if st.button("🚀 执行量化解析", type="primary"):
    df = edited_df.copy()
    
    # 【归一化纯净概率计算】
    sum_c = sum(1 / df['初盘赔率 (C)'])
    sum_j = sum(1 / df['T-60赔率 (J)'])
    sum_d = sum(1 / df['临场赔率 (D)'])
    
    prob_c = (1 / df['初盘赔率 (C)']) / sum_c
    prob_j = (1 / df['T-60赔率 (J)']) / sum_j
    prob_d = (1 / df['临场赔率 (D)']) / sum_d
    
    # 【三维指标计算】
    df['总动量 (Delta)'] = (prob_d - prob_c).round(4)
    df['期望值 (EV)'] = (prob_c * df['临场赔率 (D)'] - 1).round(4)
    df['临场加速度 (V-Delta)'] = (prob_d - prob_j).round(4)
    
    # 【雷达防伪验证逻辑】
    def radar_scan(row):
        delta = row['总动量 (Delta)']
        ev = row['期望值 (EV)']
        v_delta = row['临场加速度 (V-Delta)']
        
        # 1. 测算微观加速度 (L列逻辑)
        if v_delta >= v_limit:
            micro_radar = "⚡ 绝杀爆发 (大户入场)"
        elif v_delta <= -v_limit:
            micro_radar = "🩸 极速撤离 (绝对杀猪)"
        else:
            micro_radar = "⚪ 匀速平稳"
            
        # 2. 测算宏观防伪验证 (I列逻辑)
        if delta >= (z2 * 1.5) and ev <= -0.25:
            macro_radar = "🩸 嗜血诱导 (动量极高/抽水极深)"
        elif delta >= z3 and delta < (z2 * 1.5) and ev <= -0.08 and ev >= -0.25:
            macro_radar = "🎯 精确制导 (真实主防核心)"
        elif delta <= -z3 and ev > 0:
            macro_radar = "☠️ 淬毒诱饵 (弃防陷阱)"
        else:
            macro_radar = "⚪ 边缘震荡"
            
        return macro_radar, micro_radar

    # 应用雷达逻辑
    df[['母子集防伪验证 (宏观)', '主力狙击雷达 (微观)']] = df.apply(radar_scan, axis=1, result_type='expand')
    
    # 整理需要展示的列
    result_df = df[['选项', '总动量 (Delta)', '期望值 (EV)', '临场加速度 (V-Delta)', '母子集防伪验证 (宏观)', '主力狙击雷达 (微观)']]
    
    st.markdown("---")
    st.subheader("📊 第二步：高维风控解析结果")
    
    # 动态颜色高亮设置：诱导变红，绝杀变绿
    def color_coding(val):
        if isinstance(val, str):
            if "🩸" in val or "☠️" in val:
                return 'background-color: rgba(255, 0, 0, 0.2); color: #ffcccc; font-weight: bold;'
            elif "🎯" in val or "⚡" in val:
                return 'background-color: rgba(0, 255, 0, 0.2); color: #ccffcc; font-weight: bold;'
        return ''

    # 渲染最终表格
    st.dataframe(result_df.style.applymap(color_coding, subset=['母子集防伪验证 (宏观)', '主力狙击雷达 (微观)']), hide_index=True, use_container_width=True)
    
    st.success("运算完成！请结合宏观与微观雷达，剔除诱导项，锁定真实赛果。")