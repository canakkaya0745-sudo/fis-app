# app.py
import streamlit as st
import pandas as pd
from datetime import datetime
import os
import altair as alt

# --- Dosya yolları ---
VERILENLER_DOSYA = "verilenler.csv"
ALINANLAR_DOSYA = "alinanlar.csv"

# --- Session State Başlat ---
def init_session_state():
    if 'verilenler' not in st.session_state:
        if os.path.exists(VERILENLER_DOSYA):
            st.session_state['verilenler'] = pd.read_csv(VERILENLER_DOSYA, parse_dates=['Tarih'])
        else:
            st.session_state['verilenler'] = pd.DataFrame(
                columns=['RecId', 'Tarih', 'Dükkan', 'İş Yeri', 'Seri Başlangıç', 'Seri Bitiş', 'Teslim Alan', 'Açıklama']
            )

    if 'alinanlar' not in st.session_state:
        if os.path.exists(ALINANLAR_DOSYA):
            st.session_state['alinanlar'] = pd.read_csv(ALINANLAR_DOSYA, parse_dates=['Tarih'])
        else:
            st.session_state['alinanlar'] = pd.DataFrame(
                columns=['RecId', 'Seri No', 'Tarih', 'Dükkan', 'İş Yeri', 'Açıklama']
            )

init_session_state()

# --- Başlık ---
st.title("Trendy Hotels Fiş Takip Uygulaması")

# --- Tablar ---
tabs = st.tabs(["Verilenler", "Alınanlar", "Durum Raporu", "Özet Rapor", "Tüm Verileri Kaydet"])
tab_verilen, tab_alinan, tab_durum, tab_ozet, tab_kaydet = tabs

# --- Yardımcı Fonksiyonlar ---
def get_next_recid():
    if st.session_state['verilenler'].empty:
        return 1
    return st.session_state['verilenler']['RecId'].max() + 1

def update_durum_list():
    verilenler = st.session_state['verilenler'].copy()
    alinanlar = st.session_state['alinanlar'].copy()

    # Verilenleri seri numaralarına aç
    expanded = pd.DataFrame(
        [(row['RecId'], row['Tarih'], row['Dükkan'], row['İş Yeri'], seri)
         for _, row in verilenler.iterrows()
         for seri in range(int(row['Seri Başlangıç']), int(row['Seri Bitiş']) + 1)],
        columns=['RecId', 'Tarih', 'Departman', 'İş Yeri', 'Seri No']
    )

    # Alınanlar ile merge
    df = expanded.merge(
        alinanlar[['RecId', 'Seri No', 'Tarih']],
        on=['RecId', 'Seri No'],
        how='left',
        suffixes=('', '_Alinan')
    )

    df['Durum'] = df['Tarih_Alinan'].apply(lambda x: 'Alındı' if pd.notnull(x) else 'Bekleniyor')
    df['Alınan Tarih'] = df['Tarih_Alinan']
    df['Gün'] = df['Tarih'].dt.day
    df['Ay'] = df['Tarih'].dt.month
    df['Yıl'] = df['Tarih'].dt.year

    df.drop(columns=['Tarih_Alinan'], inplace=True)
    return df

def highlight_status(row):
    if row['Durum'] == "Alındı":
        return ['background-color: lightgreen'] * len(row)
    elif row['Durum'] == "Bekleniyor":
        return ['background-color: lightcoral'] * len(row)
    else:
        return [''] * len(row)

def show_dataframe(title, df, highlight=False):
    st.subheader(title)
    if highlight:
        st.dataframe(df.style.apply(highlight_status, axis=1))
    else:
        st.dataframe(df)

# --- Verilenler Tabı ---
with tab_verilen:
    st.header("Verilen Fişler")
    with st.form("verilen_form"):
        tarih = st.date_input("Tarih", datetime.today())
        dukkan = st.text_input("Dükkan")
        is_yeri = st.text_input("İş Yeri")
        seri_bas = st.number_input("Seri Başlangıç", step=1)
        seri_bit = st.number_input("Seri Bitiş", step=1)
        teslim_alan = st.text_input("Teslim Alan")
        aciklama = st.text_area("Açıklama")
        submitted = st.form_submit_button("Kaydet")

        if submitted:
            if not dukkan or not is_yeri:
                st.error("Dükkan ve İş Yeri boş bırakılamaz!")
            elif seri_bas > seri_bit:
                st.error("Seri Başlangıç değeri Seri Bitiş değerinden büyük olamaz!")
            else:
                new_row = {
                    'RecId': get_next_recid(),
                    'Tarih': pd.to_datetime(tarih),
                    'Dükkan': dukkan,
                    'İş Yeri': is_yeri,
                    'Seri Başlangıç': seri_bas,
                    'Seri Bitiş': seri_bit,
                    'Teslim Alan': teslim_alan,
                    'Açıklama': aciklama
                }
                st.session_state['verilenler'] = pd.concat(
                    [st.session_state['verilenler'], pd.DataFrame([new_row])],
                    ignore_index=True
                )
                st.session_state['verilenler'].to_csv(VERILENLER_DOSYA, index=False)
                st.success("Kayıt eklendi ve kaydedildi!")

    # --- Verilenler Düzenleme ---
    st.subheader("Tüm Verilenler")
    edited_df = st.data_editor(st.session_state['verilenler'].drop(columns=['RecId']),
                               use_container_width=True)

    if st.button("Verilenleri Güncelle"):
        # RecId'yi koruyarak güncelle
        updated = st.session_state['verilenler'].copy()
        for idx, rec in edited_df.iterrows():
            updated.loc[idx, edited_df.columns] = rec
        st.session_state['verilenler'] = updated
        st.session_state['verilenler'].to_csv(VERILENLER_DOSYA, index=False)
        st.success("Verilenler güncellendi ve kaydedildi!")

# --- Alınanlar Tabı ---
with tab_alinan:
    st.header("Alınan Fişler")
    with st.form("alinan_form"):
        tarih = st.date_input("Tarih", datetime.today())
        seri_no = st.number_input("Seri No", step=1)
        dukkan = st.text_input("Dükkan")
        is_yeri = st.text_input("İş Yeri")
        aciklama = st.text_area("Açıklama")
        submitted = st.form_submit_button("Kaydet")

        if submitted:
            if not dukkan or not is_yeri:
                st.error("Dükkan ve İş Yeri boş bırakılamaz!")
            else:
                uygun_verilen = st.session_state['verilenler'][
                    (st.session_state['verilenler']['Dükkan'] == dukkan) &
                    (st.session_state['verilenler']['İş Yeri'] == is_yeri) &
                    (st.session_state['verilenler']['Seri Başlangıç'] <= seri_no) &
                    (st.session_state['verilenler']['Seri Bitiş'] >= seri_no)
                ]
                if uygun_verilen.empty:
                    st.error("Hatalı giriş: Bu seri numarası verilenler tablosunda bulunmamaktadır!")
                else:
                    recid = uygun_verilen.iloc[0]['RecId']
                    if not st.session_state['alinanlar'][
                        (st.session_state['alinanlar']['RecId'] == recid) &
                        (st.session_state['alinanlar']['Seri No'] == seri_no)
                    ].empty:
                        st.warning("Bu seri numarası zaten alınanlar tablosunda mevcut!")
                    else:
                        new_row = {
                            'RecId': recid,
                            'Seri No': seri_no,
                            'Tarih': pd.to_datetime(tarih),
                            'Dükkan': dukkan,
                            'İş Yeri': is_yeri,
                            'Açıklama': aciklama
                        }
                        st.session_state['alinanlar'] = pd.concat(
                            [st.session_state['alinanlar'], pd.DataFrame([new_row])],
                            ignore_index=True
                        )
                        st.session_state['alinanlar'].to_csv(ALINANLAR_DOSYA, index=False)
                        st.success("Kayıt eklendi ve kaydedildi!")

    # --- Alınanlar Düzenleme ---
    st.subheader("Tüm Alınanlar")
    edited_alinan = st.data_editor(st.session_state['alinanlar'].drop(columns=['RecId']),
                                   use_container_width=True)

    if st.button("Alınanları Güncelle"):
        updated = st.session_state['alinanlar'].copy()
        for idx, rec in edited_alinan.iterrows():
            updated.loc[idx, edited_alinan.columns] = rec
        st.session_state['alinanlar'] = updated
        st.session_state['alinanlar'].to_csv(ALINANLAR_DOSYA, index=False)
        st.success("Alınanlar güncellendi ve kaydedildi!")

# --- Durum Raporu Tabı ---
with tab_durum:
    st.header("Durum Raporu")
    durum_df = update_durum_list()
    show_dataframe("Durum Listesi", durum_df.drop(columns=['RecId']), highlight=True)

# --- Özet Rapor ---
with tab_ozet:
    st.header("Özet Rapor")
    durum_df = update_durum_list()

    if not durum_df.empty:
        # --- Filtreleme ---
        departmanlar = durum_df['Departman'].unique().tolist()
        secilen_departmanlar = st.multiselect("Departman Seç", departmanlar, default=departmanlar)

        # Tarih aralığı için ayrı başlangıç ve bitiş
        col1, col2 = st.columns(2)
        with col1:
            baslangic_tarih = st.date_input("Başlangıç Tarihi", durum_df['Tarih'].min())
        with col2:
            bitis_tarih = st.date_input("Bitiş Tarihi", durum_df['Tarih'].max())

        # Filtre uygulama
        filt_df = durum_df[
            (durum_df['Departman'].isin(secilen_departmanlar)) &
            (durum_df['Tarih'] >= pd.to_datetime(baslangic_tarih)) &
            (durum_df['Tarih'] <= pd.to_datetime(bitis_tarih))
        ]

        # --- Departman Bazında Özet ---
        ozet = filt_df.groupby('Departman', dropna=False).agg(
            Toplam=('Seri No', 'count'),
            Alinan=('Durum', lambda x: (x == "Alındı").sum()),
            Bekleyen=('Durum', lambda x: (x == "Bekleniyor").sum())
        ).reset_index()

        st.subheader("Departman Bazında Özet")
        st.dataframe(ozet)

        # --- Bekleyen Seri Numaraları ---
        bekleyen_seri = filt_df[filt_df['Durum'] == "Bekleniyor"].groupby('Departman')['Seri No'].apply(
            list).reset_index()
        st.subheader("Bekleyen Seri Numaraları")
        st.dataframe(bekleyen_seri)

        # --- Aylık Departman Bazında Fiş Sayısı Grafiği ---
        aylik_ozet = filt_df.groupby(['Yıl', 'Ay', 'Departman'], dropna=False).agg(
            Fis_Sayisi=('Durum', lambda x: (x == "Alındı").sum())
        ).reset_index()
        aylik_ozet['Ay_String'] = aylik_ozet['Yıl'].astype(str) + "-" + aylik_ozet['Ay'].astype(str).str.zfill(2)

        chart = alt.Chart(aylik_ozet).mark_bar().encode(
            x='Ay_String:N',
            y='Fis_Sayisi:Q',
            color='Departman:N',
            tooltip=['Ay_String', 'Departman', 'Fis_Sayisi']
        ).properties(title='Aylık Departman Bazında Fiş Sayıları')
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("Henüz veri yok.")


# --- Tüm Verileri Kaydet ---
with tab_kaydet:
    st.header("Tüm Verileri Kaydet")
    if st.button("Verilenler ve Alınanlar CSV’ye Kaydet"):
        st.session_state['verilenler'].to_csv(VERILENLER_DOSYA, index=False)
        st.session_state['alinanlar'].to_csv(ALINANLAR_DOSYA, index=False)
        st.success("Tüm veriler kaydedildi!")
 
