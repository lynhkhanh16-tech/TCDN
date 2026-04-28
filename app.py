import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np

# Thiết lập cấu hình trang Streamlit
# page_title: Tiêu đề hiển thị trên tab trình duyệt
# layout="wide": Sử dụng toàn bộ chiều rộng màn hình để hiển thị dữ liệu rộng rãi hơn
st.set_page_config(page_title="Quản lý Dòng tiền & Mô phỏng Đầu tư", layout="wide")

st.title("📊 Quản lý Dòng tiền và Mô phỏng Đầu tư Cổ phiếu Dài hạn")
st.markdown("Ứng dụng giúp bạn quản lý thu chi hàng tháng, tính toán dòng tiền ròng và mô phỏng sự tăng trưởng tài sản khi đầu tư dài hạn vào thị trường chứng khoán.")

# ==========================================
# 1. KHỞI TẠO DỮ LIỆU LƯU TRỮ (SESSION STATE)
# ==========================================
# st.session_state được sử dụng để lưu trữ dữ liệu trên bộ nhớ của Streamlit, 
# giúp dữ liệu không bị mất đi mỗi khi ứng dụng reload (khi người dùng tương tác).
if 'transactions' not in st.session_state:
    # Nếu chưa có dữ liệu giao dịch, khởi tạo một DataFrame trống với các cột tương ứng.
    st.session_state['transactions'] = pd.DataFrame(
        columns=['ID', 'Tên khoản', 'Phân loại', 'Số tiền', 'Ngày ghi nhận', 'Tháng-Năm', 'Ghi chú']
    )

# ==========================================
# 2. GIAO DIỆN NHẬP LIỆU (THU - CHI)
# ==========================================
st.sidebar.header("📝 Nhập liệu Thu - Chi")

# Sử dụng st.form để gộp các trường nhập liệu lại, chỉ xử lý khi người dùng nhấn nút submit
with st.sidebar.form("transaction_form", clear_on_submit=True):
    # Lựa chọn loại giao dịch: Thu nhập hoặc Chi phí
    trans_type = st.radio("Phân loại", options=["Thu nhập", "Chi phí"])
    
    # Nhập tên khoản thu/chi
    trans_name = st.text_input("Tên khoản (VD: Lương, Tiền thuê nhà, ...)")
    
    # Nhập số tiền, min_value=0 để tránh nhập số âm, step=100000 để tăng giảm theo bước 100k
    trans_amount = st.number_input("Số tiền (VNĐ)", min_value=0.0, step=100000.0, format="%f")
    
    # Chọn ngày ghi nhận, mặc định là ngày hiện tại
    trans_date = st.date_input("Ngày ghi nhận", value=datetime.today())
    
    # Ghi chú thêm
    trans_note = st.text_input("Ghi chú")
    
    # Nút xác nhận thêm dữ liệu
    submit_button = st.form_submit_button("Thêm giao dịch")
    
    # Xử lý logic khi người dùng nhấn nút thêm
    if submit_button:
        if trans_name == "" or trans_amount <= 0:
            st.sidebar.error("Vui lòng nhập tên khoản và số tiền lớn hơn 0!")
        else:
            # Format ngày tháng thành dạng MM-YYYY để dễ dàng nhóm (group by) theo tháng
            month_year = trans_date.strftime("%m-%Y")
            
            # Tạo một dictionary chứa dữ liệu vừa nhập
            new_data = {
                'ID': len(st.session_state['transactions']) + 1,
                'Tên khoản': trans_name,
                'Phân loại': trans_type,
                'Số tiền': trans_amount,
                'Ngày ghi nhận': pd.to_datetime(trans_date), # Chuyển đổi sang kiểu datetime của pandas
                'Tháng-Năm': month_year,
                'Ghi chú': trans_note
            }
            
            # Thêm dòng dữ liệu mới vào DataFrame hiện tại lưu trong session_state
            # Sử dụng pd.concat thay vì append (vì append đã bị deprecate trong pandas bản mới)
            st.session_state['transactions'] = pd.concat(
                [st.session_state['transactions'], pd.DataFrame([new_data])], 
                ignore_index=True
            )
            st.sidebar.success("✅ Đã thêm thành công!")

# Nút xóa toàn bộ dữ liệu để người dùng làm lại từ đầu
if st.sidebar.button("🗑️ Xóa toàn bộ dữ liệu", use_container_width=True):
    st.session_state['transactions'] = pd.DataFrame(
        columns=['ID', 'Tên khoản', 'Phân loại', 'Số tiền', 'Ngày ghi nhận', 'Tháng-Năm', 'Ghi chú']
    )
    st.sidebar.success("Đã làm mới dữ liệu.")
    st.rerun() # Tải lại trang để cập nhật giao diện

# ==========================================
# 3. HIỂN THỊ DỮ LIỆU & TÍNH TOÁN DÒNG TIỀN RÒNG
# ==========================================
df = st.session_state['transactions']

st.header("💼 1. Quản lý Thu - Chi & Dòng tiền ròng")

tab1, tab2 = st.tabs(["📊 Thống kê theo tháng", "📋 Bảng dữ liệu chi tiết"])

with tab2:
    # Hiển thị bảng dữ liệu chi tiết tất cả các giao dịch
    st.dataframe(df, use_container_width=True, hide_index=True)

with tab1:
    if not df.empty:
        # Xử lý tính toán thống kê theo tháng
        # B1: Nhóm dữ liệu theo 'Tháng-Năm' và 'Phân loại', tính tổng 'Số tiền'
        monthly_summary = df.groupby(['Tháng-Năm', 'Phân loại'])['Số tiền'].sum().unstack(fill_value=0).reset_index()
        
        # Đảm bảo các cột 'Thu nhập' và 'Chi phí' luôn tồn tại dù chưa có dữ liệu loại đó
        if 'Thu nhập' not in monthly_summary.columns:
            monthly_summary['Thu nhập'] = 0.0
        if 'Chi phí' not in monthly_summary.columns:
            monthly_summary['Chi phí'] = 0.0
            
        # Ép kiểu dữ liệu về float để đồng bộ, tránh lỗi ValueError của Plotly Express
        monthly_summary['Thu nhập'] = monthly_summary['Thu nhập'].astype(float)
        monthly_summary['Chi phí'] = monthly_summary['Chi phí'].astype(float)
            
        # B2: Tính Dòng tiền ròng = Tổng Thu - Tổng Chi
        monthly_summary['Dòng tiền ròng'] = monthly_summary['Thu nhập'] - monthly_summary['Chi phí']

        
        # Hiển thị bảng tổng hợp
        st.write("### 📌 Bảng Tổng hợp Dòng tiền theo tháng")
        # Format hiển thị số tiền có dấu phẩy phân cách hàng nghìn
        st.dataframe(
            monthly_summary.style.format({
                'Thu nhập': "{:,.0f} ₫", 
                'Chi phí': "{:,.0f} ₫", 
                'Dòng tiền ròng': "{:,.0f} ₫"
            }), 
            use_container_width=True,
            hide_index=True
        )
        
        # Vẽ biểu đồ cột trực quan hóa dòng tiền ròng theo từng tháng
        # Sử dụng Plotly Express để vẽ biểu đồ nhanh
        fig_cf = px.bar(
            monthly_summary, 
            x='Tháng-Năm', 
            y=['Thu nhập', 'Chi phí', 'Dòng tiền ròng'],
            barmode='group', # Hiển thị các cột đứng cạnh nhau
            title="Biểu đồ Thu nhập, Chi phí và Dòng tiền ròng",
            labels={'value': 'Số tiền (VNĐ)', 'variable': 'Chỉ số'},
            color_discrete_sequence=['#2ecc71', '#e74c3c', '#3498db'] # Xanh lá (Thu), Đỏ (Chi), Xanh dương (Ròng)
        )
        st.plotly_chart(fig_cf, use_container_width=True)
        
        # Tính toán Dòng tiền ròng trung bình để sử dụng cho phần Mô phỏng Đầu tư
        avg_net_cashflow = monthly_summary['Dòng tiền ròng'].mean()
    else:
        st.info("Chưa có dữ liệu. Vui lòng thêm các khoản Thu/Chi ở menu bên trái.")
        avg_net_cashflow = 0.0

st.divider() # Đường kẻ ngang phân cách

# ==========================================
# 4. MÔ PHỎNG ĐẦU TƯ CỔ PHIẾU DÀI HẠN
# ==========================================
st.header("📈 2. Mô phỏng Đầu tư Cổ phiếu Dài hạn")

if avg_net_cashflow <= 0:
    st.warning("Dòng tiền ròng trung bình hiện tại <= 0. Bạn cần gia tăng thu nhập hoặc giảm chi tiêu để có dòng tiền dương phục vụ đầu tư.")
else:
    st.markdown(f"**Dòng tiền ròng trung bình hàng tháng của bạn:** `{avg_net_cashflow:,.0f} VNĐ`")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Thanh trượt tùy chỉnh tỷ lệ đầu tư từ 30% đến 50%
        # Áp dụng tỷ lệ này lên dòng tiền ròng hàng tháng
        investment_rate = st.slider(
            "Tỷ lệ đầu tư từ Dòng tiền ròng (trong 5 năm đầu) (%)", 
            min_value=30, max_value=50, value=40, step=1,
            help="Số tiền đầu tư mỗi tháng sẽ được trích từ Dòng tiền ròng theo tỷ lệ này."
        ) / 100.0
        
        # Tính toán số tiền đầu tư thực tế mỗi tháng
        monthly_investment = avg_net_cashflow * investment_rate
        
        st.info(f"💰 **Số tiền đầu tư hàng tháng:** `{monthly_investment:,.0f} VNĐ`")
        
        # Phân bổ vào 5 mã cổ phiếu (giả định chia đều 20% mỗi mã)
        stock_allocation = monthly_investment / 5
        st.write("Được phân bổ đều vào danh mục 5 mã cổ phiếu:")
        # Vẽ biểu đồ Pie đơn giản thể hiện phân bổ
        labels = ['Mã CP 1', 'Mã CP 2', 'Mã CP 3', 'Mã CP 4', 'Mã CP 5']
        values = [stock_allocation] * 5
        fig_pie = px.pie(names=labels, values=values, title="Cơ cấu phân bổ (20% mỗi mã)")
        fig_pie.update_traces(textinfo='percent+label')
        fig_pie.update_layout(height=300, margin=dict(t=30, b=0, l=0, r=0))
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        # Thanh trượt cho phép thiết lập mức tăng trưởng trung bình (15% - 20%/năm)
        annual_return_rate = st.slider(
            "Kỳ vọng mức tăng trưởng trung bình (%/năm)", 
            min_value=15.0, max_value=20.0, value=15.0, step=0.5
        ) / 100.0
        
        # CÔNG THỨC LÃI KÉP & ĐẦU TƯ ĐỊNH KỲ (Future Value of Annuity)
        # Vì ta đầu tư hàng tháng, nên cần quy đổi lãi suất năm sang lãi suất tháng.
        # Lãi suất tháng (r) = (1 + Lãi suất năm)^(1/12) - 1
        monthly_return_rate = (1 + annual_return_rate)**(1/12) - 1
        
        st.write("### 🚀 Giá trị Tài sản Tích lũy Tương lai")
        
        # Hàm tính toán giá trị tương lai của chuỗi đầu tư định kỳ hàng tháng
        # Công thức: FV = PMT * (((1 + r)^n - 1) / r) * (1 + r)
        # Trong đó:
        # - PMT: Số tiền đầu tư mỗi tháng (monthly_investment)
        # - r: Lãi suất mỗi tháng (monthly_return_rate)
        # - n: Số tháng đầu tư
        # Việc nhân thêm (1+r) ở cuối giả định ta đầu tư vào đầu mỗi tháng.
        def calculate_future_value(monthly_pmt, monthly_rate, years):
            months = years * 12
            # Xử lý trường hợp lãi suất = 0 để tránh lỗi chia cho 0
            if monthly_rate == 0:
                return monthly_pmt * months
            fv = monthly_pmt * (((1 + monthly_rate)**months - 1) / monthly_rate) * (1 + monthly_rate)
            return fv

        # Tính giá trị tại các mốc thời gian: 10, 20, 30 năm
        fv_10 = calculate_future_value(monthly_investment, monthly_return_rate, 10)
        fv_20 = calculate_future_value(monthly_investment, monthly_return_rate, 20)
        fv_30 = calculate_future_value(monthly_investment, monthly_return_rate, 30)
        
        # Tính tổng số tiền vốn đã bỏ ra (Vốn gốc) = Số tiền mỗi tháng * số tháng
        principal_10 = monthly_investment * 10 * 12
        principal_20 = monthly_investment * 20 * 12
        principal_30 = monthly_investment * 30 * 12
        
        # Hiển thị kết quả bằng metric (thẻ số liệu)
        m1, m2, m3 = st.columns(3)
        m1.metric("Sau 10 năm", f"{fv_10/1e9:,.2f} Tỷ ₫", f"Vốn: {principal_10/1e9:,.2f} Tỷ ₫", delta_color="off")
        m2.metric("Sau 20 năm", f"{fv_20/1e9:,.2f} Tỷ ₫", f"Vốn: {principal_20/1e9:,.2f} Tỷ ₫", delta_color="off")
        m3.metric("Sau 30 năm", f"{fv_30/1e9:,.2f} Tỷ ₫", f"Vốn: {principal_30/1e9:,.2f} Tỷ ₫", delta_color="off")

    # Vẽ biểu đồ đường thể hiện quá trình tăng trưởng tài sản theo thời gian (từ 1 đến 30 năm)
    st.write("### 📊 Biểu đồ Tăng trưởng Tài sản qua các năm")
    
    # Tạo danh sách các năm từ 1 đến 30
    years_list = list(range(1, 31))
    
    # Tính giá trị tương lai và vốn gốc cho từng năm để vẽ đồ thị
    fv_list = [calculate_future_value(monthly_investment, monthly_return_rate, y) for y in years_list]
    principal_list = [monthly_investment * y * 12 for y in years_list]
    
    # Tạo DataFrame chứa dữ liệu vẽ biểu đồ
    df_growth = pd.DataFrame({
        'Năm': years_list,
        'Tổng Tài sản (Giá trị tương lai)': fv_list,
        'Tổng Vốn gốc đầu tư': principal_list
    })
    
    # Sử dụng Plotly Graph Objects (go) để vẽ biểu đồ đường có lấp đầy diện tích
    fig_growth = go.Figure()
    
    # Đường biểu diễn Vốn gốc
    fig_growth.add_trace(go.Scatter(
        x=df_growth['Năm'], y=df_growth['Tổng Vốn gốc đầu tư'],
        mode='lines', name='Tổng Vốn gốc',
        line=dict(width=2, color='rgb(111, 231, 219)'),
        fill='tozeroy' # Lấp đầy từ trục X đến đường này
    ))
    
    # Đường biểu diễn Tổng Tài sản (Bao gồm vốn + lãi)
    fig_growth.add_trace(go.Scatter(
        x=df_growth['Năm'], y=df_growth['Tổng Tài sản (Giá trị tương lai)'],
        mode='lines', name='Tổng Tài sản (Lãi kép)',
        line=dict(width=3, color='rgb(131, 90, 241)'),
        fill='tonexty' # Lấp đầy khoảng cách giữa đường vốn gốc và đường tài sản để hiện phần "Lãi"
    ))
    
    # Tùy chỉnh layout đồ thị
    fig_growth.update_layout(
        title="Mô phỏng Lãi kép: Tăng trưởng tài sản trong 30 năm",
        xaxis_title="Số năm",
        yaxis_title="Số tiền (VNĐ)",
        hovermode="x unified", # Hiển thị tooltip chung cho cùng 1 trục x
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
    )
    
    st.plotly_chart(fig_growth, use_container_width=True)

    # Chú thích cuối trang
    st.caption("*Lưu ý: Mô phỏng này dựa trên giả định bạn duy trì kỷ luật đầu tư số tiền hàng tháng không đổi trong suốt quá trình và tỷ suất lợi nhuận trung bình được giữ ở mức mục tiêu. Trong thực tế, thị trường chứng khoán có những biến động ngắn hạn, nhưng nhìn chung xu hướng dài hạn là tăng trưởng.*")
