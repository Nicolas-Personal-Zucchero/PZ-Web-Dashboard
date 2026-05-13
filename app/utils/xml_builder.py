from datetime import datetime
from typing import Optional
from dachser_edi import *

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
        shipment_lines: Optional[list[ShipmentLine]],
        sscc: str,
    ) -> str:
    edi = TransportOrder(
        sender_id="72859708", # Fisso
        receiver_id="4023083000008", # Fisso
        document_id=document_id,
        document_date=datetime.now(),

        test=True, # Da rimuovere quando si andrà in produzione
        
        # transport_number="44332211",
        customer_shipment_reference= customer_shipment_reference,

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
        tail_lift_required=True,
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

        # COD=CodDetails(
        #     code="01", 
        #     amount=90,
        #     currency=Currency.EUR
        # ),
        
        lines=shipment_lines,
        SSCC=sscc
    )

    return edi.generate_xml_string()

def create_xml(nuova_spedizione):
    try:
        consignor = create_personal_zucchero_consignor()

        consignee_contact = Contact(
            name=nuova_spedizione["consignee"]["contact"]["name"],
            phone=nuova_spedizione["consignee"]["contact"]["phone"]
        )
        consignee_address = Address(
            street=nuova_spedizione["consignee"]["street"],
            city=nuova_spedizione["consignee"]["city"],
            postal_code=nuova_spedizione["consignee"]["postal_code"],
            country_code=nuova_spedizione["consignee"]["country_code"],
            supplement_information=""
        )
        consignee = Consignee(
            name=nuova_spedizione["consignee"]["name"],
            address=consignee_address,
            contact=consignee_contact
        )

        forwarder = Forwarder(
            id=nuova_spedizione["forwarder"]["id"]
        )

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
            shipment_lines=shipment_lines,
            sscc=nuova_spedizione["sscc"],
        )
        return xml_output
    except Exception as e:
        return None