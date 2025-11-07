link_registry = {}

def register_links(blueprint_name, links):
    """Registra una lista di link per un blueprint specifico"""
    link_registry[blueprint_name] = links

def get_links(*blueprints):
    """Restituisce tutti i link registrati per i blueprint richiesti"""
    result = []
    for bp in blueprints:
        result.extend(link_registry.get(bp, []))
    return result