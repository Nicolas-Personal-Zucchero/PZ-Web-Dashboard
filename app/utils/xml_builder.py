from datetime import datetime
from typing import Optional
from dachser_edi import *
from flask import current_app

def encode_base36(num: int, length: int = 5) -> str:
    """Codifica un intero in Base36 con padding fisso."""
    alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    if num == 0:
        return alphabet[0] * length
    
    res = ""
    while num > 0:
        num, i = divmod(num, 36)
        res = alphabet[i] + res
        
    return res.zfill(length)

def generate_doc_id(numero: int, sigla: str, anno_documento: int) -> str:
    """
    Genera un doc_id univoco di 5 caratteri basato sui dati fattura.
    Garantisce assenza di collisioni tramite bit-packing.
    """
    # 1. Mappatura Sigla (3 bit max -> 0-7)
    sigle_map = {'FT': 0, 'BS': 1, 'BC': 2} 
    sigla_val = sigle_map.get(sigla, 7) # 7 come fallback per sigle non censite
    
    # 2. Calcolo Epoch (5 bit max -> 0-31)
    epoch_base = 2024
    year_val = anno_documento - epoch_base
    
    # Validazione vincoli hardware-like
    if not (0 <= year_val <= 31):
        raise ValueError(f"Anno {anno_documento} fuori range per l'epoch a 5 bit.")
    if not (0 <= numero <= 2 ** 17 - 1):
        raise ValueError(f"Numero {numero} supera la capacità di 17 bit.")
        
    # 3. Bit Packing
    # Struttura: [5 bit Anno] [3 bit Sigla] [17 bit Numero]
    packed_id = (year_val << 20) | (sigla_val << 17) | numero
    
    # 4. Encoding
    return encode_base36(packed_id, 5)

def create_personal_zucchero_consignor():
    #Address facoltativo in consignor
    address = Address(
        street="Piazza Allende, 1",
        city="Poggio Torriana",
        postal_code="47824",
        country_code=CountryCode.IT
    )

    #Contact facoltativo in consignor
    contact = Contact(
        name="Personal Zucchero",
        phone="0541629284",
        email="info@personalzucchero.it"
    )

    return Consignor(
        id="72859708",
        name="PERSONAL ZUCCHERO S.R.L.",
        address=address,
        contact=contact
    )

def create_transport_order(
        document_id: str, #ID di 5 caratteri, scelto da noi,
        customer_shipment_reference: str, # È il vostro riferimento della spedizione; può essere ad esempio il numero DDT o di ordine o di fattura
        consignor: Consignor,
        consignee: Consignee,
        forwarder: Forwarder,
        product: Product,
        cod: Optional[CodDetails],
        shipment_lines: Optional[list[ShipmentLine]],
        sscc: str,
        notes: Optional[list[str]] = None,
        tail_lift_required: bool = False
    ) -> str:
    edi = TransportOrder(
        sender_id="72859708", # Fisso
        receiver_id="4023083000008", # Fisso
        document_id=document_id,
        document_date=datetime.now(),

        test=True, # Da rimuovere quando si andrà in produzione
        
        # transport_number="44332211",
        customer_shipment_reference=customer_shipment_reference,

        consignor=consignor,
        consignee=consignee,
        forwarder=forwarder,

        original_term="031", #Questa è la resa, da cambiare
        # original_term_location="HAMBURG",
        division=Division.EUROPEAN, # Fisso
        dachser_product=product,
        # order_group="A",

        shipment_date=datetime.now(),
        # delivery_date_fixed=datetime.now(),
        # delivery_date_earliest=datetime.now(),
        # delivery_date_latest=datetime.now(),

        # goods_value = GoodsValue(
        #     amount=100,
        #     currency=Currency.EUR
        # ),

        # is_dangerous=True,
        tail_lift_required=tail_lift_required,
        # picked_up_by_consignee_at_delivery_branch=False,
        # dispatch_relation="8765",
        # sub_relation="432",
        # customs_relevant=True,

        # preliminary_shipment=PreliminaryShipmentDetails(
        #     action=Action.ORIGINAL,
        #     collection_date_from=datetime.now(),
        #     collection_date_until=datetime.now(),
        #     loading_point="GATE 3"
        # ),

        COD=cod,
        notes=notes,

        lines=shipment_lines,
        SSCC=sscc
    )

    return edi.generate_xml_string()

def create_xml(nuova_spedizione):
    try:
        consignor = create_personal_zucchero_consignor()

        consignee_contact = Contact(
            email=nuova_spedizione["consignee"]["contact"]["email"],
            phone=nuova_spedizione["consignee"]["contact"]["phone"]
        )
        consignee_address = Address(
            street=nuova_spedizione["consignee"]["street"],
            city=nuova_spedizione["consignee"]["city"],
            postal_code=nuova_spedizione["consignee"]["postal_code"],
            country_code=nuova_spedizione["consignee"]["country_code"],
            # supplement_information=""
        )
        consignee = Consignee(
            name=nuova_spedizione["consignee"]["name"],
            address=consignee_address,
            contact=consignee_contact,
            contact_type=DachserContactType(nuova_spedizione["consignee"]["type"]) if nuova_spedizione["consignee"]["type"] is not None else None
        )

        forwarder = Forwarder(
            id=nuova_spedizione["forwarder"]["id"]
        )

        cod_amount = nuova_spedizione.get("cod_amount")
        cod = CodDetails(
            code="01", 
            amount=cod_amount,
            currency=Currency.EUR
        ) if cod_amount is not None else None

        shipment_lines = [
            ShipmentLine(
                packages_quantity=item["quantity"],
                packing_type=item["type"],
                description=item["description"],
                measurements=[
                    Measurement(
                        name=m["name"],
                        value=m["value"],
                        unit=m["unit"], 
                        code=m.get("code", None)
                    ) for m in item["measurements"]
                ]
            ) for item in nuova_spedizione["items"]
        ]

        xml_output = create_transport_order(
            document_id=nuova_spedizione["doc_id"],
            customer_shipment_reference=nuova_spedizione["reference"],
            consignor=consignor,
            consignee=consignee,
            forwarder=forwarder,
            product=nuova_spedizione["product"],
            cod = cod,
            shipment_lines=shipment_lines,
            sscc=nuova_spedizione["sscc"],
            notes=nuova_spedizione.get("notes"),
            tail_lift_required=nuova_spedizione.get("tail_lift_required", False)
        )
        return xml_output
    except Exception as e:
        current_app.logger.error(f"Error creating XML: {e}")
        return None