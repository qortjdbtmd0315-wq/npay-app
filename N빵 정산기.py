import streamlit as st
import pandas as pd
from datetime import datetime

# 페이지 설정
st.set_page_config(page_title="우리 모임 정산 마스터", layout="wide")

# --- 0. 비밀번호 인증 로직 ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

if not st.session_state['authenticated']:
    st.title("🔐 모임 정산기 접속")
    st.write("우리 멤버들만 이용 가능한 페이지입니다.")

    # 비밀번호 입력 (원하는 번호로 수정 가능)
    input_password = st.text_input("비밀번호를 입력하세요", type="password")

    if st.button("접속하기"):
        if input_password == "0204":  # <--- 여기서 비밀번호를 변경하세요!
            st.session_state['authenticated'] = True
            st.rerun()
        else:
            st.error("비밀번호가 일치하지 않습니다. 운영진에게 문의하세요.")
    st.stop()  # 인증되지 않으면 아래 코드를 실행하지 않음

# --- 1. 고정 멤버 및 데이터 초기화 ---
if 'all_members' not in st.session_state:
    st.session_state.all_members = [
        "배경헌", "강민경", "박솔리", "백승훈", "강지은",
        "김준희", "정원택", "정원배", "나광연", "박민규"
    ]
if 'total_records' not in st.session_state:
    st.session_state.total_records = []
if 'temp_extras' not in st.session_state:
    st.session_state.temp_extras = []

# --- 2. 왼쪽 사이드바: 멤버 리스트 표시 ---
with st.sidebar:
    st.header("👥 모임 멤버 리스트")
    st.write(f"**총 인원: {len(st.session_state.all_members)}명**")

    member_df = pd.DataFrame(st.session_state.all_members, columns=["이름"])
    st.table(member_df)

    st.divider()
    if st.button("로그아웃"):
        st.session_state['authenticated'] = False
        st.rerun()

# --- 3. 메인 화면: 정산 로직 시작 ---
st.title("🏆 소모임 통합 정산 시스템")

# 모임 정보 설정
st.subheader("📅 모임 정보")
col_date, col_group = st.columns(2)
with col_date:
    meeting_date = st.date_input("모임 날짜", datetime.now())
with col_group:
    group_name = st.text_input("모임 명칭", value="정기 모임")

# 결제자 정보 입력
st.subheader("💳 결제자 정보 입력")
with st.container(border=True):
    col_acc1, col_acc2, col_acc3 = st.columns([0.3, 0.3, 0.4])
    payee_name = col_acc1.selectbox("결제한 사람(총무)", options=["선택"] + st.session_state.all_members)
    payee_bank = col_acc2.text_input("은행명", placeholder="예: 카카오뱅크")
    payee_account = col_acc3.text_input("계좌번호", placeholder="000-000-000000")

st.divider()

# 차수별 정산 입력
st.subheader("📍 차수별 영수증 추가")
col_input1, col_input2 = st.columns(2)
with col_input1:
    round_name = st.text_input("항목명 (예: 1차 저녁, 2차 볼링 등)", placeholder="항목을 입력하세요")
with col_input2:
    total_amount = st.number_input("해당 차수 총 금액 (원)", min_value=0, step=1000)

receipt_img = st.file_uploader("🧾 영수증 사진 업로드", type=['jpg', 'jpeg', 'png'])

st.write("---")
all_participants = st.multiselect("1️⃣ 이 차수에 참여한 사람 전부 선택", st.session_state.all_members)

st.write("**2️⃣ 제외 항목 설정 (술값 등 별도 계산)**")
if st.session_state.temp_extras:
    for i, extra in enumerate(st.session_state.temp_extras):
        c1, c2, c3, c4 = st.columns([0.2, 0.2, 0.5, 0.1])
        c1.write(f"**{extra['name']}**")
        c2.write(f"{extra['amount']:,}원")
        c3.write(f"{', '.join(extra['members'])}")
        if c4.button("❌", key=f"temp_del_{i}"):
            st.session_state.temp_extras.pop(i)
            st.rerun()

with st.container(border=True):
    col_n, col_a = st.columns(2)
    new_extra_name = col_n.text_input("제외 항목명", key="new_extra_name", placeholder="예: 술값")
    new_extra_amount = col_a.number_input("금액", min_value=0, step=100, key="new_extra_amount")
    new_extra_members = st.multiselect("해당 항목 지불자 선택", options=all_participants, key="new_extra_members")
    if st.button("항목 리스트에 추가"):
        if new_extra_name and new_extra_amount > 0 and new_extra_members:
            st.session_state.temp_extras.append(
                {"name": new_extra_name, "amount": new_extra_amount, "members": new_extra_members})
            st.rerun()

if st.button("위 내용으로 차수 영수증 확정 추가 ➕", use_container_width=True):
    total_extra_sum = sum(e['amount'] for e in st.session_state.temp_extras)
    if not round_name or total_amount <= 0 or not all_participants:
        st.warning("항목명, 금액, 참여자를 모두 입력해주세요.")
    else:
        common_total = total_amount - total_extra_sum
        per_common = common_total / len(all_participants)
        round_result = {p: per_common for p in all_participants}
        for extra in st.session_state.temp_extras:
            per_extra = extra['amount'] / len(extra['members'])
            for m in extra['members']:
                round_result[m] += per_extra

        st.session_state.total_records.append({
            "차수": round_name, "총액": total_amount, "공통금액": common_total,
            "상세": round_result, "제외항목들": list(st.session_state.temp_extras), "영수증": receipt_img
        })
        st.session_state.temp_extras = []
        st.success(f"'{round_name}' 추가 완료!")
        st.rerun()

# 최종 결과 리포트
if st.session_state.total_records:
    st.divider()
    st.subheader("📑 누적 정산 현황")
    final_combined = {}
    total_sum_all = 0
    for idx, record in enumerate(st.session_state.total_records):
        total_sum_all += record['총액']
        col_res, col_del = st.columns([0.85, 0.15])
        with col_res:
            with st.expander(f"📌 {record['차수']} 상세 보기 ({record['총액']:,}원)"):
                if record["영수증"]: st.image(record["영수증"], use_container_width=True)
                for name, price in record['상세'].items():
                    final_combined[name] = final_combined.get(name, 0) + price
                    st.write(f"{name}: {int(price):,}원")
        with col_del:
            if st.button("삭제", key=f"del_{idx}"):
                st.session_state.total_records.pop(idx)
                st.rerun()

    st.divider()
    st.subheader("💰 [최종] 입금 정산 공지")
    final_text = f"📢 [{meeting_date.strftime('%Y-%m-%d')} {group_name} 정산]\n"
    final_text += f"총 결제 금액: {int(total_sum_all):,}원\n"
    final_text += "--------------------------\n"

    other_members = sorted([n for n in final_combined.keys() if n != payee_name])
    if payee_name in final_combined:
        final_text += f"💳 [결제자] {payee_name}: {int(final_combined[payee_name]):,}원\n"
    for name in other_members:
        final_text += f"✅ {name}: {int(final_combined[name]):,}원\n"

    final_text += "--------------------------\n"
    if payee_name != "선택" and payee_bank and payee_account:
        final_text += f"🏦 입금처: {payee_bank}\n💳 계좌: {payee_account}\n👤 예금주: {payee_name}\n"
    final_text += "\n증빙 사진은 상세 내역을 확인해주세요! 😊"

    st.table(pd.DataFrame([{"이름": k, "최종 합계": f"{int(v):,}원"} for k, v in final_combined.items()]))
    st.text_area("카톡 공지용 복사", value=final_text, height=300)

if st.button("🔄 모든 데이터 초기화"):
    st.session_state.total_records = []
    st.session_state.temp_extras = []
    st.rerun()