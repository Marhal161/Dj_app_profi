def dict_access(request):
    """
    Добавляет функцию для доступа к словарям через шаблоны
    """
    def get_from_dict(dictionary, key):
        if dictionary is None or key is None:
            return None
        return dictionary.get(key)

    return {'get_from_dict': get_from_dict} 