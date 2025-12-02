from urllib.parse import urlparse
import mimetypes
import requests
import io
from typing import Dict, Any, Optional

def extract_logo_id(url_immagine: str) -> str | None:
    """
    Estrae l'ID del logo dal percorso di un URL di reindirizzamento firmato di HubSpot.
    L'ID è il segmento numerico posizionato dopo '/signed-url-redirect/'.

    :param url_immagine: L'URL completo da analizzare.
    :return: La stringa dell'ID del logo o None se non trovato.
    """
    MARKER = "/signed-url-redirect/"

    parsed_url = urlparse(url_immagine)
    path = parsed_url.path
    
    if MARKER in path:
        after_marker = path.split(MARKER)[1]
        logo_id = after_marker.split('/')[0]
        logo_id = logo_id.split('?')[0]
        
        if logo_id.isdigit():
            return logo_id

    return None

def download_file_stream(file_data: Dict[str, Any], file_name: str = "file") -> Optional[io.BytesIO]:
    try:
        url = file_data['url']
        extension = file_data.get('extension', 'bin')
        complete_name = f"{file_name}.{extension}"
        mime_type, _ = mimetypes.guess_type(complete_name)

        response = requests.get(url)
        response.raise_for_status()

        stream = io.BytesIO(response.content)
        stream.name = complete_name
        stream.mime_type = mime_type if mime_type else 'application/octet-stream'

        return stream
    except KeyError as e:
        print(f"Errore: Il JSON fornito non contiene la chiave 'url': {e}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Errore durante il download di {complete_name}: {e}")
        return None