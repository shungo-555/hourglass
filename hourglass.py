import streamlit as st
import time
from datetime import datetime, timedelta
import plotly.graph_objects as go

import os
import base64


def init_session_state():
    """セッション状態の初期化"""
    default_states = {
        'is_running': False,
        'sound_played': False,
        'start_time': None,
        'total_seconds': 0,
        'paused_time': None,
        'remaining_time': 0
    }
    
    for key, default_value in default_states.items():
        if key not in st.session_state:
            st.session_state[key] = default_value


def create_hourglass_app():
    st.set_page_config(
        page_title="シンプルタイマー",
        page_icon="⌛",
        initial_sidebar_state="collapsed",
    )
    # セッション状態の初期化
    init_session_state()

    st.title("⌛シンプルタイマー")

    # カスタム時間設定（メイン画面上部）
    col1, col2, col3, col4 = st.columns([1.2, 1.2, 1.2, 1.5])
    with col1:
        minutes = st.number_input("分", min_value=0, max_value=60, value=0, step=1)
    with col2:
        seconds = st.number_input("秒", min_value=0, max_value=59, value=30, step=5)
    with col3:
        st.write("")  # 空白を入れてボタンの位置を合わせる
        st.write("")
        total_seconds = minutes * 60 + seconds
        if total_seconds == 0:
            st.warning("1秒以上を設定してください")
    with col4:
        st.write("")  # 空白を入れてボタンの位置を合わせる
        st.write("")
        if st.button("スタート ▶", type="primary", disabled=total_seconds == 0 or st.session_state.is_running, use_container_width=True):
            if not st.session_state.is_running:
                st.session_state.start_time = datetime.now()
                st.session_state.is_running = True
                st.session_state.total_seconds = total_seconds
                st.session_state.paused_time = None
                st.session_state.remaining_time = total_seconds
    
    # クイックスタートボタン
    quick_start_cols = st.columns(5)
    preset_times = {
        "1分": 60,
        "2分": 120,
        "3分": 180,
        "5分": 300,
        "10分": 600
    }
    
    # クイックスタートボタンの配置
    for i, (label, seconds) in enumerate(preset_times.items()):
        with quick_start_cols[i]:
            if st.button(label, type="primary" if not st.session_state.is_running else "secondary", disabled=st.session_state.is_running):
                if not st.session_state.is_running:
                    st.session_state.start_time = datetime.now()
                    st.session_state.is_running = True
                    st.session_state.total_seconds = seconds
                    st.session_state.paused_time = None
                    st.session_state.remaining_time = seconds
    
    st.divider()
    
    # タイマー制御エリア
    timer_cols = st.columns([1, 1, 1])
    
    with timer_cols[0]:
        if st.session_state.is_running:
            if st.button("一時停止", type="secondary", use_container_width=True):
                st.session_state.is_running = False
                st.session_state.paused_time = datetime.now()
                st.rerun()
        elif st.session_state.paused_time is not None:
            if st.button("再開", type="primary", use_container_width=True):
                # 一時停止していた時間を考慮して開始時刻を調整
                pause_duration = (datetime.now() - st.session_state.paused_time).total_seconds()
                st.session_state.start_time = st.session_state.start_time + timedelta(seconds=pause_duration)
                st.session_state.is_running = True
                st.session_state.paused_time = None
                st.rerun()

    with timer_cols[1]:
        if st.session_state.is_running or st.session_state.paused_time is not None:
            if st.button("キャンセル", type="secondary", use_container_width=True):
                st.session_state.is_running = False
                st.session_state.start_time = None
                st.session_state.paused_time = None
                st.session_state.remaining_time = 0
                st.rerun()

    # 進行状況の表示
    if st.session_state.is_running and st.session_state.start_time:
        elapsed = datetime.now() - st.session_state.start_time
        remaining = st.session_state.total_seconds - elapsed.total_seconds()
        st.session_state.remaining_time = remaining
        
        if remaining <= 0:
            st.session_state.is_running = False
            st.session_state.start_time = None
            st.session_state.paused_time = None
            st.session_state.remaining_time = 0
            
            if not st.session_state.sound_played:
                st.session_state.sound_played = True
                # st.success("⏰ 時間になりました！")
                st.balloons()
                with st.expander('時間になりました！', expanded=True, icon="⏰"):
                    st.audio("static/success.mp3", format="audio/mpeg", autoplay=True)
                time.sleep(20)
                st.rerun()
        else:
            # プログレスバーの表示
            progress = 1 - (remaining / st.session_state.total_seconds)
            st.progress(progress)
            
            # 残り時間の表示
            mins = int(remaining // 60)
            secs = int(remaining % 60)
            if mins > 0:
                st.markdown(f"<h2 style='text-align: center;'>残り時間: {mins:02d}:{secs:02d}</h2>", unsafe_allow_html=True)
            else:
                st.markdown(f"<h2 style='text-align: center;'>残り時間: {secs}秒</h2>", unsafe_allow_html=True)
            
            # 円グラフによる砂時計表示
            fig = go.Figure(go.Pie(
                values=[st.session_state.total_seconds - remaining, remaining],
                # labels=['経過時間', '残り時間'],
                hole=0.3,
                direction='clockwise',  # 時計回り
                marker_colors=['#FFA07A', '#E0E0E0'],  # 薄いオレンジと灰色
                textinfo='none',
                showlegend=False,
                sort=False
            ))
            
            fig.update_layout(
                width=250,
                height=250,
                margin=dict(l=0, r=0, t=0, b=0),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            
            # 中央揃えのためのカラムを作成
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.plotly_chart(fig, use_container_width=True)
            
            # 自動更新
            time.sleep(0.1)
            st.rerun()
    
    elif st.session_state.start_time is None:
        # タイマーがリセットされたときの処理
        st.session_state.sound_played = False

    elif st.session_state.paused_time is not None:
        # 一時停止中の表示
        remaining = st.session_state.remaining_time
        progress = 1 - (remaining / st.session_state.total_seconds)
        st.progress(progress)
        
        mins = int(remaining // 60)
        secs = int(remaining % 60)
        if mins > 0:
            st.markdown(f"<h2 style='text-align: center;'>一時停止中: {mins:02d}:{secs:02d}</h2>", unsafe_allow_html=True)
        else:
            st.markdown(f"<h2 style='text-align: center;'>一時停止中: {secs}秒</h2>", unsafe_allow_html=True)
            
            fig = go.Figure(go.Pie(
                values=[st.session_state.total_seconds - remaining, remaining],
                # labels=['経過時間', '残り時間'],
                hole=0.3,
                direction='clockwise',  # 時計回り
                marker_colors=['#FFA07A', '#E0E0E0'],  # 薄いオレンジと灰色
                textinfo='none',
                showlegend=False,
                sort=False
            ))
            
            fig.update_layout(
                width=300,
                height=300,
                margin=dict(l=0, r=0, t=0, b=0),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.plotly_chart(fig, use_container_width=True)
    else:
        if st.session_state.start_time is None:
            st.write("時間を選択して開始してください")


if __name__ == "__main__":
    create_hourglass_app()