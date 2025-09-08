# app.py
import streamlit as st
import pandas as pd
from datetime import datetime
import os
import altair as alt

VERILENLER_DOSYA = "verilenler.csv"
ALINANLAR_DOSYA = "alinanlar.csv"


if 'verilenler' not in st.session_state:
    if os.path.exists(VERILENLER_DOSYA):
        st.session_state['verilenler'] = pd.read_csv(VERILENLER_DOSYA, parse_dates=['Tarih'])
    else:
        st.session_state['verilenler'] = pd.DataFrame(
            columns=['RecId', 'Tarih', 'Dükkan', 'İş Yeri', 'Seri Başlangıç', 'Seri Bitiş', 'Teslim Alan', 'Açıklama'])

if 'alinanlar' not in st.session_state:
    if os.path.exists(ALINANLAR_DOSYA):
        st.session_state['alinanlar'] = pd.read_csv(ALINANLAR_DOSYA, parse_dates=['Tarih'])
    else:
        st.session_state['alinanlar'] = pd.DataFrame(
            columns=['RecId', 'Seri No', 'Tarih', 'Dükkan', 'İş Yeri', 'Açıklama'])


st.title("Trendy Hotels Fiş Takip Uygulaması")


tabs = st.tabs(["Verilenler", "Alınanlar", "Durum Raporu", "Günlük Fiş Raporu", "Özet Rapor", "Tüm Verileri Kaydet"])
tab_verilen, tab_alinan, tab_durum, tab_gunluk, tab_ozet, tab_kaydet = tabs



def get_next_recid():
    if st.session_state['verilenler'].empty:
        return 1
    return st.session_state['verilenler']['RecId'].max() + 1


def update_durum_list():
    durum_list = []
    verilenler = st.session_state['verilenler']
    alinanlar = st.session_state['alinanlar']

    for _, row in verilenler.iterrows():
        row_tarih = pd.to_datetime(row['Tarih'], errors='coerce') if 'Tarih' in row.index else pd.NaT

        for seri in range(int(row['Seri Başlangıç']), int(row['Seri Bitiş']) + 1):
            alinma_filt = alinanlar[alinanlar['RecId'] == row['RecId']]
            status = "Alındı" if seri in alinma_filt['Seri No'].values else "Bekleniyor"
            alinma_tarih = None
            if seri in alinma_filt['Seri No'].values:
                alinma_tarih = pd.to_datetime(alinma_filt[alinma_filt['Seri No'] == seri]['Tarih'].values[0],
                                              errors='coerce')

            durum_list.append({
                'RecId': row['RecId'],
                'Tarih': row_tarih,
                'Seri No': seri,
                'Departman': row['Dükkan'],
                'İş Yeri': row['İş Yeri'],
                'Durum': status,
                'Alınan Tarih': alinma_tarih,
                'Gün': row_tarih.day if pd.notnull(row_tarih) else None,
                'Ay': row_tarih.month if pd.notnull(row_tarih) else None,
                'Yıl': row_tarih.year if pd.notnull(row_tarih) else None
            })

    df = pd.DataFrame(durum_list)
    for col in ['RecId', 'Tarih', 'Seri No', 'Departman', 'İş Yeri', 'Durum', 'Alınan Tarih', 'Gün', 'Ay', 'Yıl']:
        if col not in df.columns:
            df[col] = pd.Series(dtype='object')

    df['Tarih'] = pd.to_datetime(df['Tarih'], errors='coerce')
    if 'Alınan Tarih' in df.columns:
        df['Alınan Tarih'] = pd.to_datetime(df['Alınan Tarih'], errors='coerce')

    return df


def highlight_status(row):
    if row['Durum'] == "Alındı":
        return ['background-color: lightgreen'] * len(row)
    elif row['Durum'] == "Bekleniyor":
        return ['background-color: lightcoral'] * len(row)
    else:
        return [''] * len(row)



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
            if seri_bas > seri_bit:
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

    st.subheader("Tüm Verilenler (Düzenlenebilir)")
    edited_verilenler = st.data_editor(st.session_state['verilenler'], num_rows="dynamic")
    if st.button("Değişiklikleri Kaydet (Verilenler)"):
        st.session_state['verilenler'] = edited_verilenler
        st.session_state['verilenler'].to_csv(VERILENLER_DOSYA, index=False)
        st.success("Değişiklikler kaydedildi!")


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

    st.subheader("Tüm Alınanlar (Düzenlenebilir)")
    edited_alinanlar = st.data_editor(st.session_state['alinanlar'], num_rows="dynamic")
    if st.button("Değişiklikleri Kaydet (Alınanlar)"):
        st.session_state['alinanlar'] = edited_alinanlar
        st.session_state['alinanlar'].to_csv(ALINANLAR_DOSYA, index=False)
        st.success("Değişiklikler kaydedildi!")

with tab_durum:
    st.header("Durum Raporu")
    durum_df = update_durum_list()
    st.dataframe(durum_df.style.apply(highlight_status, axis=1))


with tab_gunluk:
    st.header("Günlük ve Aylık Fiş Raporu")
    durum_df = update_durum_list()

    if not durum_df.empty:
        gunluk_ozet = durum_df.groupby(['Yıl', 'Ay', 'Gün', 'Departman'], dropna=False).agg(
            Alinan=('Durum', lambda x: (x == "Alındı").sum()),
            Bekleyen=('Durum', lambda x: (x == "Bekleniyor").sum())
        ).reset_index()


        gunluk_ozet['Tarih'] = pd.to_datetime({
            'year': gunluk_ozet['Yıl'],
            'month': gunluk_ozet['Ay'],
            'day': gunluk_ozet['Gün']
        })

        st.subheader("Günlük Toplamlar")
        st.dataframe(gunluk_ozet)

        aylik_ozet = durum_df.groupby(['Yıl', 'Ay', 'Departman'], dropna=False).agg(
            Fis_Sayisi=('Durum', lambda x: (x == "Alındı").sum())
        ).reset_index()
        st.subheader("Aylık Toplamlar (Departman Bazında)")
        st.dataframe(aylik_ozet)

        aylik_ozet['Ay_String'] = aylik_ozet['Yıl'].astype(str) + "-" + aylik_ozet['Ay'].astype(str).str.zfill(2)
        chart = alt.Chart(aylik_ozet).mark_bar().encode(
            x='Departman:N',
            y='Fis_Sayisi:Q',
            color='Departman:N',
            tooltip=['Ay_String', 'Departman', 'Fis_Sayisi']
        ).properties(title='Aylık Departman Bazında Fiş Sayıları')
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("Henüz veri yok.")


with tab_ozet:
    st.header("Özet Rapor")
    durum_df = update_durum_list()

    if not durum_df.empty:
        ozet = durum_df.groupby('Departman', dropna=False).agg(
            Toplam=('Seri No', 'count'),
            Alinan=('Durum', lambda x: (x == "Alındı").sum()),
            Bekleyen=('Durum', lambda x: (x == "Bekleniyor").sum())
        ).reset_index()
        st.subheader("Departman Bazında Özet")
        st.dataframe(ozet)

        bekleyen_seri = durum_df[durum_df['Durum'] == "Bekleniyor"].groupby('Departman')['Seri No'].apply(
            list).reset_index()
        st.subheader("Bekleyen Seri Numaraları")
        st.dataframe(bekleyen_seri)


        gunluk_ozet = durum_df.groupby(['Yıl', 'Ay', 'Gün', 'Departman'], dropna=False).agg(
            Alinan=('Durum', lambda x: (x == "Alındı").sum())
        ).reset_index()
        gunluk_ozet['Tarih'] = pd.to_datetime({
            'year': gunluk_ozet['Yıl'],
            'month': gunluk_ozet['Ay'],
            'day': gunluk_ozet['Gün']
        })
        st.subheader("Günlük Özet (Grafikli)")
        chart_gunluk = alt.Chart(gunluk_ozet).mark_bar().encode(
            x='Tarih:T',
            y='Alinan:Q',
            color='Departman:N',
            tooltip=['Tarih', 'Departman', 'Alinan']
        ).properties(title='Günlük Alınan Fiş Sayıları')
        st.altair_chart(chart_gunluk, use_container_width=True)
    else:
        st.info("Henüz veri yok.")


with tab_kaydet:
    st.header("Tüm Verileri Kaydet")
    if st.button("Verilenler ve Alınanlar CSV’ye Kaydet"):
        st.session_state['verilenler'].to_csv(VERILENLER_DOSYA, index=False)
        st.session_state['alinanlar'].to_csv(ALINANLAR_DOSYA, index=False)
        st.success("Tüm veriler kaydedildi!")
