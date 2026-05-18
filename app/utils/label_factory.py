LOGO_DATA = "A,2016,2016,16,,:::::V018,::V038,:V078,::V0F8,:U01F8,U01FC,:U03FC,U07FC,:I08Q07FC,I06Q07FE,I03CP0FFE,I07FO01FFE,I03FEN01FFE,I02FF8M03FFE,I017FFM03FFE,I017FFCL03FFE,J0BIFCK03IF,J09JFK03IF,J04JFEJ03IF,J04KF8I01IF,J067JFEI01IF,J023KF8001IF,J033KFC001IF,J018KFE001IF,J018KFEI0IF,J01C7KFI0IF,K0C3KFI0IF8,K063KF8007FF8,K071KF8007FF8,K070KFC007FF8,K038KFE007FF8,K0387JFE007FF8,K01C3KF007FFC,K01C1KF007FFC,L0E0KF803FFC,L0F0KF803FFC,L0F07JFC03FFC0E,L0783JFE01FFC0F8,L0783JFE01FFC07F,L03C1FFE7F01FFC03FC,L03C0IF0301FFC03FF8,L01E07FF8001FFC01FFE,L01F07FFC001FFE00IFC,M0F03FFCI0FFE00JF,M0F81FFEI0FFE007IFC,M0F80IFI0FFE007JFC,M07C0IFI0FFE003JFE,M07C07FFC007FE001KFE,M03E03FFC007FE001LF8,M03F01FFE007FFI0MF,M03F01IF007FFI0MF8,M03F80IF007FFI07KFE,M03F807FF807FFI07KF8,M07FC03FFC03FFI03JFC,M07FE03FFC03FFI01JF,M0FFE01FFE03FFI01IFC,M0IF00IF03FFJ0FFE,M0IF00IF81FFJ0FF8,L01IF807FFC1FFJ07C,L01IF803FFE1FF8I06,L03IFC01FFE1FF8,L03IFE00IF1FF8,L07IFE00IF8FF8,L07JF007FF8FF8,L0KF003FFCFF8,L0KF803FFEFFC,L0KF801IF7FC,K01KFC00KFC,K01KFE00KFC,K03KFE003JFC,K03LF003JFC,K07LF001JFC,K07LF800JFC,K0MFC007IFC,:J01MFE003IFE,J01MFE001IFE,J01MFC001IFE,J03MFJ0IFE,J03LFCJ07FFE,J07KFEK03FFE,J07KF8K03FFE,J07JFCL01IF,J0KFN0IF,I01JFO07FF,I01IFCO07FF,I01IFP03FF,I03FFCP01FF,I03FCR0FF,I07FS0FF,I078S07F,I06T03F,I08T03F8,Y0F8,:Y078,Y038,:Y018,g0C,:g04,,:::::::::"

def generate_sugar_label(ragione_sociale, via, cap_citta_provincia, stato, telefono, ca, notes):
    """
    Genera il codice ZPL per l'etichetta Personal Zucchero.
    I campi del mittente sono allineati a destra con margine 50.
    """
    zpl = f"""^XA

^FO690,50^GF{LOGO_DATA}^FS

^FO690,1025^GF{LOGO_DATA}^FS

^FX Inversione assi per formato verticale
^PW800
^LL1198
^LS0

^FX Imposta l'orientamento globale dei campi a 90 gradi (orario)
^FWR

^FX Sezione Superiore: Mittente
^CF0,65
^FO740,50^FB1098,1,0,C^FDPersonal Zucchero SRL^FS
^CF0,25
^FO700,50^FB1098,1,0,C^FDPiazza Allende 1 - 47824 Poggio Torriana RN - Italy^FS
^FX La riga orizzontale ^GB1100,3,3 diventa verticale ^GB3,1100,3
^FO670,50^GB3,1100,3^FS

^FX Sezione Centrale: Destinatario con flow dinamico
^CF0,25
^FO630,50^FDDestinatario / Recipient^FS

^FX Unico blocco per i dati variabili
^CF0,60
^FO120,60^FB1098,7,10,L,0^FD
{ragione_sociale}\&
{via}\&
{cap_citta_provincia}\&
{stato}\&
{telefono}\&
{ca}^FS

^FX Sezione Note
^FO110,50^GB3,1100,3^FS
^CF0,60
^FO30,60^FD{notes}^FS

^XZ"""
    return zpl

def generate_dachser_label(sscc, date, counter, total, ragione_sociale, via, cap_citta_provincia, stato, show_personal_zucchero):
    zpl_rows = ["^XA"]
    
    """
    Genera l'etichetta per Dachser con o senza logo Personal Zucchero.
    Se show_personal_zucchero è True, include il logo e la sezione mittente, altrimenti li esclude.
    """
    if show_personal_zucchero:
        zpl_rows.extend([
            f"^FO30,50^GF{LOGO_DATA}^FS",
            f"^FO30,1025^GF{LOGO_DATA}^FS"
        ])

    zpl_rows.extend([
        "^FX Inversione assi per formato verticale",
        "^PW800",
        "^LL1198",
        "^LS0",
        "^FX Imposta l'orientamento globale dei campi a 90 gradi (orario)",
        "^FWR",
        "^FX Sezione Superiore: Barcode SSCC",
        "^CF0,50",
        "^FO760,50^FDDACHSER^FS",
        "^FO700,80^FDSSCC^FS",
        f"^FO710,290^BY4^BCR,120,Y,N,Y,U^FD(00){sscc}^FS",
        "^CF0,40",
        f"^FO770,820^FB330,1,0,R^FD{date}^FS",
        "^CF0,50",
        f"^FO680,820^FB330,1,0,R^FD{counter}/{total}^FS",
        "^FX La riga orizzontale ^GB1100,3,3 diventa verticale ^GB3,1100,3",
        "^FO670,50^GB3,1100,3^FS",
        "^FX Sezione Centrale: Destinatario con flow dinamico",
        "^CFB,18,13",
        "^FO630,50^FDDestinatario / Recipient^FS",
        "^CF0,40",
        "^FO610,820^FB330,1,0,R^FDBS 2/103^FS",
        "^FX Unico blocco per i dati variabili",
        "^CF0,60",
        "^FO120,60^FB1098,7,10,L,0^FD",
        f"{ragione_sociale}\\&",
        f"{via}\\&",
        f"{cap_citta_provincia}\\&",
        f"{stato}^FS"
    ])
        
    if show_personal_zucchero:
        zpl_rows.extend([
            "^FX Sezione Mittente",
            "^FO150,50^GB3,1100,3^FS"
            "^CF0,65",
            "^FO70,50^FB1098,1,0,C^FDPersonal Zucchero SRL^FS",
            "^CFB,17",
            "^FO40,63^FB1098,1,0,C^FDPiazza Allende 1 - 47824 Poggio Torriana RN - Italy^FS"
        ])

    zpl_rows.append("^XZ")
    return "\n".join(zpl_rows)